"""One-page live audit application service."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from hashlib import sha256

from app.acquisition.playwright_fetcher import FetchedPage, PageFetcher
from app.acquisition.zone_extractor import PAGE_ZONE, Zone
from app.agent.cache import DSXEvaluationCache, EvaluationCacheKey
from app.agent.evaluator import DSXEvaluator, build_check_result
from app.agent.schemas import DSXEvaluation, DSXEvaluationRequest
from app.agent.verifier import EvidenceVerifier
from app.audits.activity import RunActivityLog
from app.config import settings
from app.domain.models import (
    AuditMode,
    AuditRun,
    CheckResult,
    PageSnapshot,
    PageTarget,
    RuleEvaluatorType,
    RulePassage,
)
from app.facts.deterministic_runner import DeterministicFactRunner
from app.facts.models import PageFacts
from app.issues.reconciler import IssueReconciler
from app.persistence.repositories import (
    CheckResultRepository,
    IssueIdentityRepository,
    IssueObservationRepository,
    PageCaptureRepository,
    PageSnapshotRepository,
)
from app.rule_knowledge.selection import RuleSelector


@dataclass(frozen=True)
class LivePageAuditResult:
    """Result of auditing one live target."""

    snapshot: PageSnapshot
    results: list[CheckResult]
    warnings: list[str]


class LivePageAuditService:
    """Execute acquisition, rule selection, and evaluation for one target."""

    def __init__(
        self,
        fetcher: PageFetcher,
        selector: RuleSelector,
        evaluator: DSXEvaluator,
        snapshot_repo: PageSnapshotRepository,
        result_repo: CheckResultRepository,
        fact_runner: DeterministicFactRunner | None = None,
        verifier: EvidenceVerifier | None = None,
        identity_repo: IssueIdentityRepository | None = None,
        observation_repo: IssueObservationRepository | None = None,
        reconciler: IssueReconciler | None = None,
        evaluation_cache: DSXEvaluationCache | None = None,
        capture_repo: PageCaptureRepository | None = None,
        activity: RunActivityLog | None = None,
    ) -> None:
        self._fetcher = fetcher
        self._selector = selector
        self._evaluator = evaluator
        self._snapshot_repo = snapshot_repo
        self._result_repo = result_repo
        self._fact_runner = fact_runner or DeterministicFactRunner()
        self._verifier = verifier or EvidenceVerifier()
        self._identity_repo = identity_repo
        self._observation_repo = observation_repo
        self._reconciler = reconciler or IssueReconciler()
        self._evaluation_cache = evaluation_cache or DSXEvaluationCache()
        self._capture_repo = capture_repo
        self._activity = activity or RunActivityLog()
        self._dsx_slots = asyncio.Semaphore(settings.DSX_MAX_CONCURRENT)

    @property
    def fetcher(self) -> PageFetcher:
        """Expose acquisition for the crawl coordinator."""
        return self._fetcher

    async def close(self) -> None:
        """Release the live browser after a run."""
        await self._fetcher.stop()

    def needs_link_probe(self, mode: AuditMode, locales: Iterable[str]) -> bool:
        """Return True when a page-scope checkpoint reads probed link status."""
        return any(
            rule.check == "broken_links"
            for locale in locales
            for rule in self._selector.select(mode, locale, PAGE_ZONE)
        )

    async def audit_page(
        self,
        run: AuditRun,
        target: PageTarget,
        mode: AuditMode,
    ) -> LivePageAuditResult:
        """Fetch and audit one target."""
        probe_links = self.needs_link_probe(mode, [target.locale])
        fetched = await self._fetcher.fetch_page(
            str(target.url), probe_links=probe_links
        )
        return await self.audit_fetched_page(run, target, mode, fetched)

    async def audit_fetched_page(
        self,
        run: AuditRun,
        target: PageTarget,
        mode: AuditMode,
        fetched: FetchedPage,
        on_check: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> LivePageAuditResult:
        """Audit a previously fetched target and persist its results."""
        warnings = list(fetched.warnings)
        capture_id: str | None = None
        capture_size: int | None = None
        capture_hash: str | None = None
        html_size = len(fetched.html.encode("utf-8"))
        if (
            self._capture_repo is not None
            and html_size <= settings.HTML_CAPTURE_MAX_BYTES
        ):
            capture_id = await self._capture_repo.create(
                fetched.html,
                {"run_id": run.id, "url": fetched.url, "locale": target.locale},
            )
            capture_size = html_size
            capture_hash = sha256(fetched.html.encode("utf-8")).hexdigest()
        elif self._capture_repo is not None:
            warnings.append("html_capture_skipped_size_limit")
        snapshot = PageSnapshot(
            id=str(uuid.uuid4()),
            run_id=run.id,
            url=fetched.url,
            locale=target.locale,
            content_hash=fetched.content_hash,
            extraction_version="live-0.2.0",
            warnings=warnings,
            html_capture_id=capture_id,
            html_capture_size=capture_size,
            html_capture_hash=capture_hash,
        )
        await self._snapshot_repo.create(snapshot)
        await self._activity.record(
            run.id,
            "extract",
            f"Extracted {len(fetched.zones)} page zones",
            page=target.locale,
        )

        page_scope = Zone(name=PAGE_ZONE, text="", dom_locator="", metadata={})
        zone_rules: list[tuple[Zone, RulePassage]] = []
        for zone in [*fetched.zones, page_scope]:
            rules = self._selector.select(mode, target.locale, zone.name)
            await self._activity.record(
                run.id,
                "retrieve",
                f"Retrieved {len(rules)} checkpoints for {zone.name}",
                page=target.locale,
            )
            zone_rules.extend((zone, rule) for rule in rules)

        completed = 0

        async def check(zone: Zone, rule: RulePassage) -> list[CheckResult]:
            nonlocal completed
            produced = self._reconciler.assign_occurrences(
                await self._evaluate_rule(
                    run, target, snapshot, zone, rule, fetched.facts
                )
            )
            for result in produced:
                await self._result_repo.create(result)
                await self._persist_issue_observation(result, snapshot)
            await self._activity.record(
                run.id,
                "check",
                f"Checkpoint {rule.id} on {zone.name}: {_summarize(produced)}",
                page=target.locale,
            )
            completed += 1
            if on_check is not None:
                await on_check(completed, len(zone_rules))
            return produced

        outcomes = await asyncio.gather(
            *(check(zone, rule) for zone, rule in zone_rules),
            return_exceptions=True,
        )
        for outcome in outcomes:
            if isinstance(outcome, BaseException):
                raise outcome
        results = [
            result
            for outcome in outcomes
            if isinstance(outcome, list)
            for result in outcome
        ]

        if not fetched.zones:
            warnings.append("no_supported_zones_extracted")
        return LivePageAuditResult(
            snapshot=snapshot,
            results=results,
            warnings=warnings,
        )

    async def _persist_issue_observation(
        self,
        result: CheckResult,
        snapshot: PageSnapshot,
    ) -> None:
        """Persist stable identity and observation when configured."""
        if self._identity_repo is None or self._observation_repo is None:
            return
        identity = self._reconciler.build_identity(result, snapshot)
        observation = self._reconciler.build_observation(result, snapshot)
        if identity is None or observation is None:
            return
        await self._identity_repo.get_or_create(identity)
        await self._observation_repo.create(observation)

    async def _call_dsx(self, request: DSXEvaluationRequest) -> DSXEvaluation:
        async with self._dsx_slots:
            return await self._evaluator.evaluate(request)

    async def _evaluate_rule(
        self,
        run: AuditRun,
        target: PageTarget,
        snapshot: PageSnapshot,
        zone: Zone,
        rule: RulePassage,
        facts: PageFacts,
    ) -> list[CheckResult]:
        """Return a code verdict, a gated LLM verdict, or an LLM verdict for one checkpoint."""
        if rule.evaluator_type == RuleEvaluatorType.CODE:
            produced = self._fact_runner.evaluate(rule, run, snapshot, zone, facts)
            return [
                self._finalize(result, rule, target, zone, facts) for result in produced
            ]
        candidates: list[str] | None = None
        if rule.evaluator_type == RuleEvaluatorType.HYBRID:
            candidates = self._fact_runner.screen(rule, target.locale, zone, facts)
        if not zone.text or candidates == []:
            skipped = self._fact_runner.skipped(rule, run, snapshot, zone)
            return [self._finalize(skipped, rule, target, zone, facts)]
        result = await self._evaluate_with_dsx(
            run, target, snapshot, zone, rule, facts, candidates
        )
        return [self._finalize(result, rule, target, zone, facts)]

    async def _evaluate_with_dsx(
        self,
        run: AuditRun,
        target: PageTarget,
        snapshot: PageSnapshot,
        zone: Zone,
        rule: RulePassage,
        facts: PageFacts,
        candidates: list[str] | None,
    ) -> CheckResult:
        deterministic_facts = facts.scoped(rule.topics)
        if candidates:
            deterministic_facts["candidates"] = candidates
        cache_key = EvaluationCacheKey.build(
            rule.version,
            rule.id,
            zone.text,
            deterministic_facts,
            "audit-prompt-v2",
            self._evaluator.model,
        )
        evaluation = self._evaluation_cache.get(cache_key)
        if evaluation is None:
            evaluation = await self._call_dsx(
                DSXEvaluationRequest(
                    url=snapshot.url,
                    locale=target.locale,
                    zone=zone.name,
                    checkpoint_text=rule.original_text,
                    checkpoint_id=rule.id,
                    page_text=zone.text,
                    deterministic_facts=deterministic_facts,
                    context={"heading_path": rule.heading_path},
                )
            )
            if evaluation.response is not None and evaluation.error_code is None:
                self._evaluation_cache.set(cache_key, evaluation)
        return build_check_result(
            evaluation,
            result_id=str(uuid.uuid4()),
            run_id=run.id,
            page_snapshot_id=snapshot.id,
            rule_passage_id=rule.id,
            zone=zone.name,
        ).model_copy(
            update={
                "rule_quote": rule.original_text,
                "dom_locator": zone.dom_locator,
            }
        )

    def _finalize(
        self,
        result: CheckResult,
        rule: RulePassage,
        target: PageTarget,
        zone: Zone,
        facts: PageFacts,
    ) -> CheckResult:
        checked = self._verifier.verify(result, rule, zone, facts).result
        return checked.model_copy(
            update={
                "review_required": checked.review_required
                or _needs_review(rule, target.locale),
                "reminder": rule.reminder,
            }
        )


def _needs_review(rule: RulePassage, locale: str) -> bool:
    return rule.review == "always" or rule.review.lower() == locale.lower()


def _summarize(results: list[CheckResult]) -> str:
    return ", ".join(sorted({result.outcome.value for result in results}))
