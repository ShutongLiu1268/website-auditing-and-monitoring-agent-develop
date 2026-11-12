"""Unit tests for one-page live audit service."""

import pytest
from pytest_mock import MockerFixture

from app.acquisition.playwright_fetcher import FetchedPage
from app.acquisition.zone_extractor import PAGE_ZONE, Zone
from app.agent.evaluator import DSXEvaluator
from app.agent.schemas import DSXEvaluation, DSXEvaluationResponse
from app.audits.live_page_service import LivePageAuditService
from app.domain.models import (
    AuditMode,
    AuditRun,
    CheckOutcome,
    CheckResult,
    PageTarget,
    RuleEvaluatorType,
    RulePassage,
    RunStatus,
    TokenUsage,
)
from app.facts.models import DimensionFact, LinkFact, PageFacts


def _run() -> AuditRun:
    """Build a test run."""
    return AuditRun(
        id="run-1",
        audit_definition_id="audit-1",
        status=RunStatus.RUNNING,
        total_pages=1,
    )


def _target(locale: str = "en-US") -> PageTarget:
    """Build a test target."""
    return PageTarget(url="https://example.test/pdp", locale=locale)


def _rule(
    rule_id: str,
    evaluator_type: RuleEvaluatorType,
    topics: list[str] | None = None,
    check: str | None = None,
) -> RulePassage:
    """Build a test rule."""
    return RulePassage(
        id=rule_id,
        version="v1",
        heading_path=["Section 1"],
        source_range=(1, 5),
        original_text="Check the page content.",
        modes=[AuditMode.R3],
        topics=topics or [],
        evaluator_type=evaluator_type,
        check=check,
    )


def _zone(name: str, text: str) -> Zone:
    """Build a zone with a locator matching its name."""
    return Zone(name=name, text=text, dom_locator=f".{name}", metadata={})


def _fetcher(mocker: MockerFixture, zones: list[Zone], facts: PageFacts | None = None):
    fetcher = mocker.MagicMock()
    fetcher.fetch_page = mocker.AsyncMock(
        return_value=FetchedPage(
            url="https://example.test/pdp",
            html="<html>content</html>",
            zones=zones,
            content_hash="hash-1",
            warnings=[],
            facts=facts or PageFacts(),
        )
    )
    fetcher.stop = mocker.AsyncMock()
    return fetcher


def _selector(mocker: MockerFixture, rules_by_zone: dict[str, list[RulePassage]]):
    selector = mocker.MagicMock()
    selector.select = mocker.MagicMock(
        side_effect=lambda mode, locale, zone: rules_by_zone.get(zone, [])
    )
    return selector


def _dsx(
    mocker: MockerFixture, outcome: str = "issue", evidence: str = "Dell PDP content"
):
    response = DSXEvaluationResponse(
        outcome=outcome,
        problem="Issue found" if outcome == "issue" else None,
        rule_quote="Check the page content.",
        evidence_quote=evidence if outcome == "issue" else None,
    )
    evaluator = mocker.MagicMock()
    evaluator.model = "gpt-oss-120b"
    evaluator.evaluate = mocker.AsyncMock(
        return_value=DSXEvaluation(
            model="gpt-oss-120b",
            attempts=1,
            response=response,
            token_usage=TokenUsage(
                prompt_tokens=10, completion_tokens=5, total_tokens=15
            ),
        )
    )
    return evaluator


def _repos(mocker: MockerFixture, persisted: list[CheckResult]):
    snapshot_repo = mocker.MagicMock()
    snapshot_repo.create = mocker.AsyncMock()
    result_repo = mocker.MagicMock()
    result_repo.create = mocker.AsyncMock(side_effect=persisted.append)
    return snapshot_repo, result_repo


@pytest.mark.asyncio
async def test_live_service_persists_snapshot_and_results(mocker: MockerFixture):
    """Test acquisition, rule evaluation, and persistence per zone and page scope."""
    zone = _zone("hero", "Dell PDP content")
    fetcher = _fetcher(mocker, [zone])
    selector = _selector(
        mocker,
        {
            "hero": [_rule("llm-rule", RuleEvaluatorType.LLM)],
            PAGE_ZONE: [
                _rule("code-rule", RuleEvaluatorType.CODE, check="broken_links")
            ],
        },
    )
    evaluator = _dsx(mocker)
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)

    service = LivePageAuditService(
        fetcher, selector, evaluator, snapshot_repo, result_repo
    )
    result = await service.audit_page(_run(), _target(), AuditMode.R3)

    snapshot_repo.create.assert_awaited_once()
    selector.select.assert_any_call(AuditMode.R3, "en-US", "hero")
    selector.select.assert_any_call(AuditMode.R3, "en-US", PAGE_ZONE)
    evaluator.evaluate.assert_awaited_once()
    assert len(result.results) == 2
    by_rule = {item.rule_passage_id: item for item in persisted}
    assert by_rule["llm-rule"].outcome == CheckOutcome.ISSUE
    assert by_rule["llm-rule"].token_usage == TokenUsage(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )
    assert by_rule["code-rule"].outcome == CheckOutcome.NOT_APPLICABLE
    assert by_rule["code-rule"].error is None


@pytest.mark.asyncio
async def test_live_service_marks_dsx_unavailable_not_evaluated(mocker: MockerFixture):
    """Test unavailable DSX does not become a false pass."""
    zone = _zone("hero", "content")
    fetcher = _fetcher(mocker, [zone])
    selector = _selector(mocker, {"hero": [_rule("llm-rule", RuleEvaluatorType.LLM)]})
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)

    service = LivePageAuditService(
        fetcher,
        selector,
        DSXEvaluator(None, model="gpt-oss-120b"),
        snapshot_repo,
        result_repo,
    )
    await service.audit_page(_run(), _target(), AuditMode.R3)

    assert persisted[0].outcome == CheckOutcome.NOT_EVALUATED
    assert persisted[0].error == "DSX_UNAVAILABLE:client_not_configured"


@pytest.mark.asyncio
async def test_en_ca_spelling_finding_is_flagged_for_review(mocker: MockerFixture):
    """Test findings from an en-CA review checkpoint require review."""
    zone = _zone("hero", "Colour")
    fetcher = _fetcher(mocker, [zone])
    spelling = _rule("SPR-06", RuleEvaluatorType.LLM)
    spelling.review = "en-CA"
    selector = _selector(mocker, {"hero": [spelling]})
    evaluator = _dsx(mocker, evidence="Colour")
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)
    service = LivePageAuditService(
        fetcher, selector, evaluator, snapshot_repo, result_repo
    )

    await service.audit_page(_run(), _target("en-CA"), AuditMode.R3)

    selector.select.assert_any_call(AuditMode.R3, "en-CA", "hero")
    assert persisted[0].review_required is True
    assert persisted[0].reminder is None


@pytest.mark.asyncio
async def test_code_checkpoint_decides_without_llm(mocker: MockerFixture):
    """Test a code checkpoint produces its verdict from facts and never calls the LLM."""
    facts = PageFacts(
        links=[
            LinkFact(
                href="https://www.dell.com/missing",
                locator="a:nth-of-type(1)",
                status_code=404,
                reachable=False,
            )
        ]
    )
    fetcher = _fetcher(mocker, [], facts)
    selector = _selector(
        mocker,
        {PAGE_ZONE: [_rule("SPR-12", RuleEvaluatorType.CODE, check="broken_links")]},
    )
    evaluator = _dsx(mocker)
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)
    service = LivePageAuditService(
        fetcher, selector, evaluator, snapshot_repo, result_repo
    )

    await service.audit_page(_run(), _target(), AuditMode.R3)

    evaluator.evaluate.assert_not_awaited()
    [result] = persisted
    assert result.outcome == CheckOutcome.ISSUE
    assert result.zone == PAGE_ZONE
    assert result.evidence_quote == "https://www.dell.com/missing"
    assert result.model is None


@pytest.mark.asyncio
async def test_hybrid_checkpoint_without_candidates_skips_llm(mocker: MockerFixture):
    """Test a gate with no candidates records not-applicable without an LLM call."""
    zone = _zone("features", "Affordable laptop")
    fetcher = _fetcher(mocker, [zone])
    selector = _selector(
        mocker,
        {
            "features": [
                _rule(
                    "SPR-05", RuleEvaluatorType.HYBRID, check="superlative_candidates"
                )
            ]
        },
    )
    evaluator = _dsx(mocker)
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)
    service = LivePageAuditService(
        fetcher, selector, evaluator, snapshot_repo, result_repo
    )

    await service.audit_page(_run(), _target(), AuditMode.R3)

    evaluator.evaluate.assert_not_awaited()
    assert persisted[0].outcome == CheckOutcome.NOT_APPLICABLE


@pytest.mark.asyncio
async def test_hybrid_checkpoint_sends_candidates_to_llm(mocker: MockerFixture):
    """Test a gate with candidates passes them to the LLM as facts."""
    zone = _zone("features", "The thinnest laptop")
    fetcher = _fetcher(mocker, [zone])
    selector = _selector(
        mocker,
        {
            "features": [
                _rule(
                    "SPR-05", RuleEvaluatorType.HYBRID, check="superlative_candidates"
                )
            ]
        },
    )
    evaluator = _dsx(mocker, evidence="thinnest")
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)
    service = LivePageAuditService(
        fetcher, selector, evaluator, snapshot_repo, result_repo
    )

    await service.audit_page(_run(), _target(), AuditMode.R3)

    evaluator.evaluate.assert_awaited_once()
    request = evaluator.evaluate.await_args.args[0]
    assert request.deterministic_facts == {"candidates": ["thinnest"]}


@pytest.mark.asyncio
async def test_llm_checkpoint_receives_only_its_topic_facts(mocker: MockerFixture):
    """Test LLM requests carry only the fact categories the checkpoint declares."""
    zone = _zone("dimensions_weight", "Width 344.72 mm")
    facts = PageFacts(
        links=[LinkFact(href="https://www.dell.com/a", locator="a:nth-of-type(1)")],
        dimensions=[
            DimensionFact(
                text="344.72 mm",
                value=344.72,
                unit="mm",
                locator=".dimensions_weight",
            )
        ],
    )
    fetcher = _fetcher(mocker, [zone], facts)
    selector = _selector(
        mocker,
        {
            "dimensions_weight": [
                _rule("R2G-05", RuleEvaluatorType.LLM, topics=["dimensions"]),
            ]
        },
    )
    evaluator = _dsx(mocker, evidence="Width 344.72 mm")
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)
    service = LivePageAuditService(
        fetcher, selector, evaluator, snapshot_repo, result_repo
    )

    await service.audit_page(_run(), _target(), AuditMode.R3)

    request = evaluator.evaluate.await_args.args[0]
    assert set(request.deterministic_facts) == {"dimensions"}


@pytest.mark.asyncio
async def test_empty_zone_skips_llm(mocker: MockerFixture):
    """Test a zone without text cannot hold evidence, so the LLM is not called."""
    zone = _zone("hero", "")
    fetcher = _fetcher(mocker, [zone])
    selector = _selector(mocker, {"hero": [_rule("SPR-18", RuleEvaluatorType.LLM)]})
    evaluator = _dsx(mocker)
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)
    service = LivePageAuditService(
        fetcher, selector, evaluator, snapshot_repo, result_repo
    )

    await service.audit_page(_run(), _target(), AuditMode.R3)

    evaluator.evaluate.assert_not_awaited()
    assert persisted[0].outcome == CheckOutcome.NOT_APPLICABLE


@pytest.mark.asyncio
async def test_page_checkpoint_runs_once_per_page(mocker: MockerFixture):
    """Test page-scope checkpoints are evaluated once, not once per zone."""
    hero = _zone("hero", "Dell PDP")
    features = _zone("features", "Laptop")
    fetcher = _fetcher(mocker, [hero, features])
    llm_rule = _rule("SPR-18", RuleEvaluatorType.LLM)
    selector = _selector(
        mocker,
        {
            "hero": [llm_rule],
            "features": [llm_rule],
            PAGE_ZONE: [_rule("SPR-12", RuleEvaluatorType.CODE, check="broken_links")],
        },
    )
    evaluator = _dsx(mocker, outcome="pass")
    persisted: list[CheckResult] = []
    snapshot_repo, result_repo = _repos(mocker, persisted)
    service = LivePageAuditService(
        fetcher, selector, evaluator, snapshot_repo, result_repo
    )

    await service.audit_page(_run(), _target(), AuditMode.R3)

    assert evaluator.evaluate.await_count == 2
    assert len([item for item in persisted if item.zone == PAGE_ZONE]) == 1
