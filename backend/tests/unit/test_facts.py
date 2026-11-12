"""Unit tests for deterministic page facts and rule checks."""

import pytest
from pytest_mock import MockerFixture

from app.acquisition.zone_extractor import Zone
from app.domain.models import (
    AuditMode,
    AuditRun,
    CheckOutcome,
    PageSnapshot,
    RuleEvaluatorType,
    RulePassage,
    RunStatus,
)
from app.facts.collector import FactCollector
from app.facts.deterministic_runner import DeterministicFactRunner
from app.facts.models import DimensionFact, ImageFact, LinkFact, MediaFact, PageFacts


def _rule(
    rule_id: str,
    check: str,
    evaluator: RuleEvaluatorType = RuleEvaluatorType.CODE,
) -> RulePassage:
    """Build a checkpoint that names a deterministic check."""
    return RulePassage(
        id=rule_id,
        version="v1",
        heading_path=["Section 1"],
        source_range=(1, 2),
        original_text="Check the page facts.",
        modes=[AuditMode.R3],
        evaluator_type=evaluator,
        check=check,
    )


def _run() -> AuditRun:
    """Build a running audit."""
    return AuditRun(id="run-1", audit_definition_id="audit-1", status=RunStatus.RUNNING)


def _snapshot() -> PageSnapshot:
    """Build a page snapshot."""
    return PageSnapshot(
        id="snapshot-1",
        run_id="run-1",
        url="https://example.test/pdp",
        locale="en-CA",
        content_hash="hash",
        extraction_version="test",
    )


def _zone(text: str = "396 mm") -> Zone:
    """Build a zone."""
    return Zone(
        name="dimensions_weight", text=text, dom_locator="#dimensions", metadata={}
    )


@pytest.mark.asyncio
async def test_fact_collector_collects_links_images_and_dimensions(
    mocker: MockerFixture,
):
    """Test DOM facts and response status mapping."""
    page = mocker.MagicMock()
    page.evaluate = mocker.AsyncMock(
        return_value={
            "links": [
                {"href": "https://example.test/broken", "locator": "a:nth-of-type(1)"}
            ],
            "images": [
                {
                    "src": "https://example.test/hero.jpg",
                    "alt": "",
                    "loaded": False,
                    "locator": "img:nth-of-type(1)",
                }
            ],
        }
    )

    facts = await FactCollector().collect(
        page,
        [_zone("396 mm")],
        {"https://example.test/broken": 404},
    )

    assert facts.links[0].reachable is False
    assert facts.links[0].status_code == 404
    assert facts.images[0].loaded is False
    assert facts.dimensions[0].unit == "mm"


@pytest.mark.asyncio
async def test_fact_collector_collects_media_load_state(mocker: MockerFixture):
    """Test video load failures become media facts."""
    page = mocker.MagicMock()
    page.evaluate = mocker.AsyncMock(
        return_value={
            "links": [],
            "images": [],
            "videos": [
                {
                    "src": "https://cdn.example.test/x.mp4",
                    "broken": True,
                    "locator": "video:nth-of-type(1)",
                }
            ],
        }
    )

    facts = await FactCollector().collect(page, [], {})

    assert facts.media == [
        MediaFact(
            src="https://cdn.example.test/x.mp4",
            locator="video:nth-of-type(1)",
            broken=True,
        )
    ]


@pytest.mark.asyncio
async def test_fact_collector_marks_links_inside_zones(mocker: MockerFixture):
    """Test the DOM probe receives zone selectors and flags links inside zones."""
    page = mocker.MagicMock()
    page.evaluate = mocker.AsyncMock(
        return_value={
            "links": [
                {
                    "href": "https://example.test/a",
                    "locator": "a:nth-of-type(1)",
                    "in_zone": True,
                }
            ],
            "images": [],
            "videos": [],
        }
    )
    zone = Zone(
        name="hero",
        text="Dell",
        dom_locator=".hero >> nth=0",
        metadata={"selector": ".hero"},
    )

    facts = await FactCollector().collect(page, [zone], {})

    assert facts.links[0].in_zone is True
    assert page.evaluate.await_args.args[1] == [".hero"]


@pytest.mark.asyncio
async def test_fact_collector_skips_footer_for_link_probing(mocker: MockerFixture):
    """Test the DOM probe never marks global footer links as probe candidates."""
    page = mocker.MagicMock()
    page.evaluate = mocker.AsyncMock(
        return_value={"links": [], "images": [], "videos": []}
    )
    hero = Zone(
        name="hero",
        text="Dell",
        dom_locator=".hero >> nth=0",
        metadata={"selector": ".hero"},
    )
    footer = Zone(
        name="global_footer",
        text="Contact Dell",
        dom_locator=".global-footer >> nth=0",
        metadata={"selector": ".global-footer, footer"},
    )

    await FactCollector().collect(page, [hero, footer], {})

    assert page.evaluate.await_args.args[1] == [".hero"]


def test_runner_reports_broken_link():
    """Test broken link issue evidence comes from link facts."""
    facts = PageFacts(
        links=[
            LinkFact(
                href="https://example.test/broken",
                locator="a:nth-of-type(1)",
                status_code=404,
                reachable=False,
            )
        ]
    )

    [result] = DeterministicFactRunner().evaluate(
        _rule("SPR-12", "broken_links"), _run(), _snapshot(), _zone(), facts
    )

    assert result.outcome == CheckOutcome.ISSUE
    assert result.evidence_quote == "https://example.test/broken"
    assert result.dom_locator == "a:nth-of-type(1)"
    assert result.confidence == 1.0
    assert result.model is None


def test_runner_passes_reachable_links():
    """Test verified reachable links produce a deterministic pass."""
    facts = PageFacts(
        links=[
            LinkFact(
                href="https://example.test/ok",
                locator="a:nth-of-type(1)",
                status_code=200,
                reachable=True,
            )
        ]
    )

    [result] = DeterministicFactRunner().evaluate(
        _rule("SPR-12", "broken_links"), _run(), _snapshot(), _zone(), facts
    )

    assert result.outcome == CheckOutcome.PASS
    assert result.confidence == 1.0


def test_runner_reports_failed_video():
    """Test failed media loads become issues with the source as evidence."""
    facts = PageFacts(
        media=[
            MediaFact(
                src="https://cdn.example.test/x.mp4",
                locator="video:nth-of-type(1)",
                broken=True,
            )
        ]
    )

    [result] = DeterministicFactRunner().evaluate(
        _rule("SPR-13", "broken_media"), _run(), _snapshot(), _zone(), facts
    )

    assert result.outcome == CheckOutcome.ISSUE
    assert result.evidence_quote == "https://cdn.example.test/x.mp4"


def test_runner_reports_out_of_order_dimensions():
    """Test dimension order issues cite the out-of-place label."""
    zone = _zone("Width: 344.72 mm\nHeight: 18.00 mm")

    [result] = DeterministicFactRunner().evaluate(
        _rule("SPR-01", "dimension_order"), _run(), _snapshot(), zone, PageFacts()
    )

    assert result.outcome == CheckOutcome.ISSUE
    assert result.evidence_quote == "Height"
    assert result.rule_quote == "Check the page facts."


def test_runner_marks_unverified_links_not_applicable():
    """Test links without probe results never become false passes."""
    facts = PageFacts(
        links=[LinkFact(href="https://example.test/a", locator="a:nth-of-type(1)")]
    )

    [result] = DeterministicFactRunner().evaluate(
        _rule("SPR-12", "broken_links"), _run(), _snapshot(), _zone(), facts
    )

    assert result.outcome == CheckOutcome.NOT_APPLICABLE
    assert result.confidence == 0.0


def test_runner_marks_empty_fact_category_not_applicable():
    """Test empty fact categories do not become false passes."""
    [result] = DeterministicFactRunner().evaluate(
        _rule("SPR-13", "broken_media"), _run(), _snapshot(), _zone(), PageFacts()
    )

    assert result.outcome == CheckOutcome.NOT_APPLICABLE
    assert result.confidence == 0.0


def test_runner_unknown_check_is_error():
    """Test a checkpoint without a registered check reports an error."""
    [result] = DeterministicFactRunner().evaluate(
        _rule("X-1", "does_not_exist"), _run(), _snapshot(), _zone(), PageFacts()
    )

    assert result.outcome == CheckOutcome.ERROR
    assert result.error == "unsupported_deterministic_rule"


def test_runner_screen_returns_gate_candidates():
    """Test hybrid gates return candidate strings for the LLM."""
    rule = _rule("SPR-05", "superlative_candidates", RuleEvaluatorType.HYBRID)

    candidates = DeterministicFactRunner().screen(
        rule, "en-CA", _zone("The thinnest laptop"), PageFacts()
    )

    assert candidates == ["thinnest"]


def test_runner_skipped_gate_is_not_applicable():
    """Test a gate without candidates records a not-applicable result."""
    rule = _rule("SPR-05", "superlative_candidates", RuleEvaluatorType.HYBRID)

    result = DeterministicFactRunner().skipped(rule, _run(), _snapshot(), _zone())

    assert result.outcome == CheckOutcome.NOT_APPLICABLE
    assert result.zone == "dimensions_weight"
    assert result.model is None


def test_scoped_facts_keep_only_topic_fields():
    """Test LLM facts include only the categories a checkpoint declares."""
    facts = PageFacts(
        links=[LinkFact(href="https://example.test/a", locator="a:nth-of-type(1)")],
        dimensions=[
            DimensionFact(text="18 mm", value=18.0, unit="mm", locator="#dimensions")
        ],
    )

    scoped = facts.scoped(["dimensions"])

    assert set(scoped) == {"dimensions"}


def test_scoped_facts_without_topics_are_empty():
    """Test checkpoints without topics receive no fact payload."""
    facts = PageFacts(
        images=[ImageFact(src="hero.jpg", locator="img:nth-of-type(1)", loaded=True)]
    )

    assert facts.scoped([]) == {}
