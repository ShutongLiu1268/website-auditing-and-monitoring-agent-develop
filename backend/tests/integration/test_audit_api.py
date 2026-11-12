import asyncio
from dataclasses import dataclass

import pytest
from fastapi import HTTPException

from app import main
from app.acquisition.playwright_fetcher import FetchedPage
from app.acquisition.zone_extractor import Zone
from app.agent.schemas import DSXEvaluation, DSXEvaluationResponse
from app.api.schemas import AuditCreateRequest, PromptParseRequest, PromptRunRequest
from app.audits.activity import RunActivityLog
from app.audits.live_page_service import LivePageAuditService
from app.audits.orchestrator import AuditOrchestrator
from app.domain.models import (
    AuditDefinition,
    AuditMode,
    AuditRun,
    CheckResult,
    PageSnapshot,
    RulePassage,
    RunStatus,
)

URL_EN_CA = "https://www.dell.com/en-ca/shop/laptops"
URL_EN_US = "https://www.dell.com/en-us/shop/laptops"
URL_FR_CA = "https://www.dell.com/fr-ca/shop/laptops"
URL_NO_ZONES = "https://www.dell.com/en-us/shop/empty"

PAGE_TEXT = {
    URL_EN_CA: "Dell 16 Laptop with 16 GB memory. Customization options.",
    URL_EN_US: "Dell 16 Laptop with 16 GB memory and 512 GB storage.",
    URL_FR_CA: "Ordinateur Dell 16 avec 16 Go de memoire. Enterprise Upgrades.",
}

RULES = [
    RulePassage(
        id=rule_id,
        version="test-rules",
        heading_path=["Test"],
        source_range=(1, 2),
        original_text=text,
        modes=[AuditMode.R3],
        zones=["hero"],
    )
    for rule_id, text in [
        ("R3R-01", "Show memory in gigabytes with the unit spelled out."),
        ("R3R-02", "Use regional spelling for product features."),
        ("R3R-03", "Add the trademark symbol after the product name."),
        ("D2", "Keep French-Canadian copy free of English fragments."),
    ]
]

LIVE_TARGETS = [
    {"url": URL_EN_CA, "locale": "en-CA"},
    {"url": URL_EN_US, "locale": "en-US"},
    {"url": URL_FR_CA, "locale": "fr-CA"},
]

FIRST_RUN_FINDINGS = {
    ("en-US", "R3R-01"): ("Memory unit is abbreviated.", "16 GB memory"),
    ("fr-CA", "D2"): ("English fragment remains visible.", "Enterprise Upgrades"),
}


class MemoryAuditDefinitionRepository:
    def __init__(self):
        self.items: dict[str, AuditDefinition] = {}

    async def create(self, definition):
        self.items[definition.id] = definition
        return definition

    async def get(self, id):
        return self.items.get(id)


class MemoryRunRepository:
    def __init__(self):
        self.items: dict[str, AuditRun] = {}

    async def create(self, run):
        self.items[run.id] = run
        return run

    async def get(self, id):
        return self.items.get(id)

    async def list_by_comparison_key(self, comparison_key):
        return [
            item
            for item in reversed(list(self.items.values()))
            if item.comparison_key == comparison_key
        ]

    async def find_baseline(self, comparison_key, exclude_id, started_before):
        runs = [
            item
            for item in self.items.values()
            if item.comparison_key == comparison_key
            and item.id != exclude_id
            and item.status in {RunStatus.COMPLETED, RunStatus.PARTIAL}
            and item.completed_pages > 0
            and item.completed_at is not None
            and item.completed_at < started_before
        ]
        return max(runs, key=lambda item: item.completed_at, default=None)

    async def update_status(
        self,
        id,
        status,
        completed_at=None,
        started_at=None,
        completed_pages=None,
        failed_pages=None,
        warnings=None,
        coverage=None,
        coverage_pages=None,
        active_page_progress=None,
        page_statuses=None,
    ):
        run = self.items[id]
        run.status = RunStatus(status)
        if completed_at is not None:
            run.completed_at = completed_at
        if started_at is not None:
            run.started_at = started_at
        if completed_pages is not None:
            run.completed_pages = completed_pages
        if failed_pages is not None:
            run.failed_pages = failed_pages
        if warnings is not None:
            run.warnings = warnings
        if active_page_progress is not None:
            run.active_page_progress = active_page_progress
        if page_statuses is not None:
            run.page_statuses = page_statuses


class MemorySnapshotRepository:
    def __init__(self):
        self.items: list[PageSnapshot] = []

    async def create(self, snapshot):
        self.items.append(snapshot)
        return snapshot

    async def get_by_run(self, run_id):
        return [item for item in self.items if item.run_id == run_id]


class MemoryResultRepository:
    def __init__(self):
        self.items: list[CheckResult] = []

    async def create(self, result):
        self.items.append(result)
        return result

    async def get_by_run(self, run_id):
        return [item for item in self.items if item.run_id == run_id]


class MemoryIdentityRepository:
    def __init__(self):
        self.items = {}

    async def get_or_create(self, identity):
        return self.items.setdefault(identity.id, identity)

    async def get_many(self, ids):
        return {
            item_id: self.items[item_id] for item_id in ids if item_id in self.items
        }


class MemoryObservationRepository:
    def __init__(self):
        self.items = []

    async def create(self, observation):
        self.items.append(observation)
        return observation

    async def get_by_run(self, run_id):
        return [item for item in self.items if item.run_id == run_id]


class MemoryRulePassageRepository:
    async def get_latest_version(self):
        return "test-rules"


class ScriptedFetcher:
    """Serves scripted pages in place of Playwright acquisition."""

    def __init__(self):
        self.unreachable: set[str] = set()

    async def fetch_page(self, url: str, *, probe_links: bool = False) -> FetchedPage:
        if url in self.unreachable:
            raise ConnectionError(url)
        text = PAGE_TEXT.get(url, "")
        zones = (
            [Zone(name="hero", text=text, dom_locator=".hero >> nth=0", metadata={})]
            if text
            else []
        )
        return FetchedPage(
            url=url,
            html=f"<html>{text}</html>",
            zones=zones,
            content_hash=f"hash:{url}",
            warnings=[],
        )

    async def stop(self) -> None:
        return None


class ScriptedDSX:
    """Scripted DSX stand-in: flags (locale, checkpoint) pairs with exact evidence."""

    model = "scripted-dsx"

    def __init__(self):
        self.findings: dict[tuple[str, str], tuple[str, str]] = {}

    async def evaluate(self, request):
        finding = self.findings.get((request.locale, request.checkpoint_id))
        if finding is None:
            response = DSXEvaluationResponse(
                outcome="pass", reasoning="Checkpoint satisfied on this page."
            )
        else:
            problem, evidence = finding
            response = DSXEvaluationResponse(
                outcome="issue",
                problem=problem,
                suggested_correction="Correct the page copy.",
                proof_text=evidence,
                severity="high",
                rule_quote=request.checkpoint_text,
                evidence_quote=evidence,
                confidence=0.9,
                reasoning=f"{problem} The page text contains {evidence!r}.",
            )
        return DSXEvaluation(model=self.model, attempts=1, response=response)


class FixedSelector:
    """Returns the same checkpoints for every zone."""

    def select(self, mode, locale, zone):
        return list(RULES)


class NoEvaluationCache:
    """Disables DSX result reuse so each run sees its own scripted outcomes."""

    def get(self, key):
        return None

    def set(self, key, value):
        return None


@dataclass
class LiveHarness:
    fetcher: ScriptedFetcher
    dsx: ScriptedDSX


@pytest.fixture
def live_audit_app():
    fetcher = ScriptedFetcher()
    dsx = ScriptedDSX()
    audit_repo = MemoryAuditDefinitionRepository()
    run_repo = MemoryRunRepository()
    snapshot_repo = MemorySnapshotRepository()
    result_repo = MemoryResultRepository()
    identity_repo = MemoryIdentityRepository()
    observation_repo = MemoryObservationRepository()
    activity = RunActivityLog()
    live_service = LivePageAuditService(
        fetcher,
        FixedSelector(),
        dsx,
        snapshot_repo,
        result_repo,
        identity_repo=identity_repo,
        observation_repo=observation_repo,
        evaluation_cache=NoEvaluationCache(),
        activity=activity,
    )

    main.app.state.audit_def_repo = audit_repo
    main.app.state.run_repo = run_repo
    main.app.state.snapshot_repo = snapshot_repo
    main.app.state.result_repo = result_repo
    main.app.state.rule_passage_repo = MemoryRulePassageRepository()
    main.app.state.run_tasks = set()
    main.app.state.issue_identity_repo = identity_repo
    main.app.state.issue_observation_repo = observation_repo
    main.app.state.activity = activity
    main.app.state.live_page_service = live_service
    main.app.state.orchestrator = AuditOrchestrator(
        audit_repo,
        run_repo,
        live_service,
        activity=activity,
    )
    return LiveHarness(fetcher=fetcher, dsx=dsx)


async def _wait_for_terminal_status(run_id):
    status = await main.get_run_status(run_id)
    for _ in range(500):
        if status.status in {"completed", "partial", "failed"}:
            break
        await asyncio.sleep(0.01)
        status = await main.get_run_status(run_id)
    return status


async def _run_live_audit(targets=LIVE_TARGETS):
    audit = await main.create_audit(AuditCreateRequest(mode="r3", targets=targets))
    run = await main.create_run(audit.id)
    await _wait_for_terminal_status(run.run_id)
    return run.run_id


@pytest.mark.asyncio
async def test_live_audit_runs_through_api(live_audit_app):
    live_audit_app.dsx.findings = FIRST_RUN_FINDINGS
    payload = AuditCreateRequest(mode="r3", targets=LIVE_TARGETS)
    audit = await main.create_audit(payload)
    run = await main.create_run(audit.id)

    status = await _wait_for_terminal_status(run.run_id)

    assert status.status == "completed"
    assert status.progress == 100
    issues = await main.get_run_issues(
        run.run_id,
        severity=None,
        page=None,
        locale=None,
    )
    assert len(issues) == 2
    assert {issue.page for issue in issues} == {"EN-US", "FR-CA"}
    assert all(issue.proof for issue in issues)
    assert all(issue.reasoning for issue in issues)
    trace = await main.get_run_trace(run.run_id)
    assert len(trace) == 10
    assert {entry.evaluator for entry in trace} == {"DSX", "Deterministic"}
    assert {locale for entry in trace for locale in entry.locales} == {
        "en-CA",
        "en-US",
        "fr-CA",
    }
    assert all(entry.reasoning for entry in trace if entry.evaluator == "DSX")


@pytest.mark.asyncio
async def test_live_audit_without_supported_zones_reports_partial(live_audit_app):
    audit = await main.create_audit(
        AuditCreateRequest(
            mode="r3",
            targets=[{"url": URL_NO_ZONES, "locale": "en-US"}],
        )
    )
    run = await main.create_run(audit.id)

    status = await _wait_for_terminal_status(run.run_id)

    assert status.status == "partial"
    assert "no_supported_zones_extracted" in status.warnings
    assert (
        await main.get_run_issues(run.run_id, severity=None, page=None, locale=None)
        == []
    )


@pytest.mark.asyncio
async def test_prompt_parse_returns_pdp_targets_and_problems(live_audit_app):
    response = await main.parse_prompt(
        PromptParseRequest(
            prompt=(
                "Audit https://www.dell.com/en-us/shop/laptops and "
                "https://www.dell.com/fr-ca/shop/laptops and "
                "https://www.dell.com/shop/laptops"
            )
        )
    )

    assert [(target.url, target.locale) for target in response.targets] == [
        ("https://www.dell.com/en-us/shop/laptops", "en-US"),
        ("https://www.dell.com/fr-ca/shop/laptops", "fr-CA"),
    ]
    assert len(response.problems) == 1
    assert "https://www.dell.com/shop/laptops" in response.problems[0]


@pytest.mark.asyncio
async def test_prompt_run_creates_audit_and_streams_bot_activity(live_audit_app):
    started = await main.create_prompt_run(
        PromptRunRequest(
            prompt="Audit https://www.dell.com/en-us/shop/laptops and https://www.dell.com/fr-ca/shop/laptops",
            mode="r3",
        )
    )

    assert [target.locale for target in started.targets] == ["en-US", "fr-CA"]
    status = await _wait_for_terminal_status(started.run_id)
    assert status.status == "completed"

    stream = await main.stream_run_events(started.run_id)
    body = "".join([chunk async for chunk in stream.body_iterator])

    assert "Rendered en-US page" in body
    assert "Rendered fr-CA page" in body
    assert body.endswith("event: done\ndata: {}\n\n")


@pytest.mark.asyncio
async def test_live_run_streams_each_checkpoint_as_activity(live_audit_app):
    live_audit_app.dsx.findings = {
        ("en-US", "R3R-01"): ("Memory unit is abbreviated.", "16 GB memory"),
    }
    run_id = await _run_live_audit(targets=[{"url": URL_EN_US, "locale": "en-US"}])

    stream = await main.stream_run_events(run_id)
    body = "".join([chunk async for chunk in stream.body_iterator])

    assert "Checkpoint R3R-01 on hero: issue" in body
    assert "Checkpoint R3R-02 on hero: pass" in body
    assert body.count("event: activity") >= 6


@pytest.mark.asyncio
async def test_prompt_run_rejects_prompt_without_pdp_urls(live_audit_app):
    with pytest.raises(HTTPException) as error:
        await main.create_prompt_run(
            PromptRunRequest(prompt="Audit my site please", mode="r3")
        )

    assert error.value.status_code == 422


@pytest.mark.asyncio
async def test_prompt_run_audits_each_repeated_url_once(live_audit_app):
    started = await main.create_prompt_run(
        PromptRunRequest(
            prompt=(
                "Audit https://www.dell.com/fr-ca/shop/laptops\n"
                "https://www.dell.com/fr-ca/shop/laptops"
            ),
            mode="r3",
        )
    )

    assert [target.url for target in started.targets] == [
        "https://www.dell.com/fr-ca/shop/laptops"
    ]
    await _wait_for_terminal_status(started.run_id)


@pytest.mark.asyncio
async def test_first_live_run_lists_every_issue_as_new(live_audit_app):
    live_audit_app.dsx.findings = FIRST_RUN_FINDINGS
    run_id = await _run_live_audit()

    comparison = await main.get_run_comparison(run_id)

    assert comparison.previous_run_id is None
    assert len(comparison.statuses["new"]) == 2


@pytest.mark.asyncio
async def test_second_live_run_reports_transitions_and_not_rechecked_pages(
    live_audit_app,
):
    live_audit_app.dsx.findings = {
        **FIRST_RUN_FINDINGS,
        ("en-US", "R3R-02"): ("Regional spelling is missing.", "512 GB storage"),
    }
    await _run_live_audit()

    live_audit_app.dsx.findings = {
        ("en-US", "R3R-01"): ("Memory unit is abbreviated.", "16 GB memory"),
        ("en-US", "R3R-03"): ("Trademark symbol is missing.", "Dell 16 Laptop"),
    }
    live_audit_app.fetcher.unreachable = {URL_FR_CA}
    second_run_id = await _run_live_audit()

    status = await main.get_run_status(second_run_id)
    comparison = await main.get_run_comparison(second_run_id)
    problems = {
        name: sorted(item.problem for item in items)
        for name, items in comparison.statuses.items()
        if items
    }

    assert status.status == "partial"
    assert "crawl_inaccessible_pages:1" in status.warnings
    assert comparison.previous_run_id is not None
    assert problems == {
        "new": ["Trademark symbol is missing."],
        "unresolved": ["Memory unit is abbreviated."],
        "resolved": ["Regional spelling is missing."],
        "not_rechecked": ["English fragment remains visible."],
    }
