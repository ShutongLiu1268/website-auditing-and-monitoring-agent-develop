"""Unit tests for evidence verification."""

from app.acquisition.zone_extractor import Zone
from app.agent.verifier import EvidenceVerifier
from app.domain.models import (
    AuditMode,
    CheckOutcome,
    CheckResult,
    RulePassage,
)
from app.facts.models import MediaFact, PageFacts


def _rule() -> RulePassage:
    """Build a source rule."""
    return RulePassage(
        id="rule-1",
        version="v1",
        heading_path=["Section"],
        source_range=(1, 2),
        original_text="Use metric units.",
        modes=[AuditMode.R3],
    )


def _result(**updates) -> CheckResult:
    """Build an issue result."""
    values = {
        "id": "result-1",
        "run_id": "run-1",
        "page_snapshot_id": "snapshot-1",
        "rule_passage_id": "rule-1",
        "zone": "dimensions_weight",
        "outcome": CheckOutcome.ISSUE,
        "rule_quote": "Use metric units.",
        "evidence_quote": "15.6 inches",
        "dom_locator": "#dimensions",
        "problem": "Imperial unit found.",
    }
    values.update(updates)
    return CheckResult(**values)


def test_verifier_accepts_exact_rule_evidence_and_locator():
    """Test valid issue citations."""
    result = EvidenceVerifier().verify(
        _result(),
        _rule(),
        Zone("dimensions_weight", "15.6 inches", "#dimensions", {}),
        PageFacts(),
    )

    assert result.accepted is True
    assert result.result.outcome == CheckOutcome.ISSUE


def test_verifier_rejects_missing_evidence():
    """Test missing evidence becomes an error."""
    result = EvidenceVerifier().verify(
        _result(evidence_quote="not present"),
        _rule(),
        Zone("dimensions_weight", "15.6 inches", "#dimensions", {}),
        PageFacts(),
    )

    assert result.accepted is False
    assert result.result.outcome == CheckOutcome.ERROR
    assert (
        result.result.error == "evidence_verification_failed:evidence_quote_not_found"
    )


def test_verifier_accepts_media_fact_evidence():
    """Test media sources and locators can satisfy evidence verification."""
    result = EvidenceVerifier().verify(
        _result(
            evidence_quote="https://cdn.example.test/x.mp4",
            dom_locator="video:nth-of-type(1)",
            zone="page",
        ),
        _rule(),
        Zone("page", "", "", {}),
        PageFacts(
            media=[
                MediaFact(
                    src="https://cdn.example.test/x.mp4",
                    locator="video:nth-of-type(1)",
                    broken=True,
                )
            ]
        ),
    )

    assert result.accepted is True


def test_verifier_accepts_fact_evidence():
    """Test fact values can satisfy evidence verification."""
    result = EvidenceVerifier().verify(
        _result(
            evidence_quote="https://example.test/broken", dom_locator="a:nth-of-type(1)"
        ),
        _rule(),
        Zone("hero", "no matching text", ".hero", {}),
        PageFacts(
            links=[
                {
                    "href": "https://example.test/broken",
                    "locator": "a:nth-of-type(1)",
                    "status_code": 404,
                    "reachable": False,
                }
            ]
        ),
    )

    assert result.accepted is True
