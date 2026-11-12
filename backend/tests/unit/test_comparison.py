"""
Unit tests for comparison engine.
"""

from app.comparison.engine import ComparisonEngine
from app.domain.models import ComparisonStatus, IssueObservation


def test_compare_runs_new_issue():
    """Test detection of new issues."""
    current = [
        IssueObservation(
            id="obs-1",
            issue_identity_id="issue-1",
            run_id="run-2",
            page_snapshot_id="snap-1",
            rule_quote="Use metric units",
            evidence_quote="15.6 inches",
            dom_locator="#specs",
            problem="Imperial unit in metric locale",
            suggested_correction="Use mm",
            proof_text="Original: 15.6 inches",
            severity="high",
            confidence=0.95,
            review_required=False,
        )
    ]
    previous = []

    result = ComparisonEngine.compare_runs(current, previous, "completed", "completed")

    assert len(result[ComparisonStatus.NEW]) == 1
    assert len(result[ComparisonStatus.UNRESOLVED]) == 0
    assert len(result[ComparisonStatus.RESOLVED]) == 0


def test_compare_runs_unresolved():
    """Test detection of unresolved issues."""
    current = [
        IssueObservation(
            id="obs-1",
            issue_identity_id="issue-1",
            run_id="run-2",
            page_snapshot_id="snap-1",
            rule_quote="Use metric units",
            evidence_quote="15.6 inches",
            dom_locator="#specs",
            problem="Imperial unit in metric locale",
            suggested_correction="Use mm",
            proof_text="Original: 15.6 inches",
            severity="high",
            confidence=0.95,
            review_required=False,
        )
    ]
    previous = [
        IssueObservation(
            id="obs-2",
            issue_identity_id="issue-1",
            run_id="run-1",
            page_snapshot_id="snap-1",
            rule_quote="Use metric units",
            evidence_quote="15.6 inches",
            dom_locator="#specs",
            problem="Imperial unit in metric locale",
            suggested_correction="Use mm",
            proof_text="Original: 15.6 inches",
            severity="high",
            confidence=0.95,
            review_required=False,
        )
    ]

    result = ComparisonEngine.compare_runs(current, previous, "completed", "completed")

    assert len(result[ComparisonStatus.NEW]) == 0
    assert len(result[ComparisonStatus.UNRESOLVED]) == 1
    assert len(result[ComparisonStatus.RESOLVED]) == 0


def test_compare_runs_resolved():
    """Test detection of resolved issues."""
    current = []
    previous = [
        IssueObservation(
            id="obs-1",
            issue_identity_id="issue-1",
            run_id="run-1",
            page_snapshot_id="snap-1",
            rule_quote="Use metric units",
            evidence_quote="15.6 inches",
            dom_locator="#specs",
            problem="Imperial unit in metric locale",
            suggested_correction="Use mm",
            proof_text="Original: 15.6 inches",
            severity="high",
            confidence=0.95,
            review_required=False,
        )
    ]

    result = ComparisonEngine.compare_runs(current, previous, "completed", "completed")

    assert len(result[ComparisonStatus.NEW]) == 0
    assert len(result[ComparisonStatus.UNRESOLVED]) == 0
    assert len(result[ComparisonStatus.RESOLVED]) == 1


def test_compare_runs_not_rechecked():
    """Test not-rechecked when current run failed."""
    current = []
    previous = [
        IssueObservation(
            id="obs-1",
            issue_identity_id="issue-1",
            run_id="run-1",
            page_snapshot_id="snap-1",
            rule_quote="Use metric units",
            evidence_quote="15.6 inches",
            dom_locator="#specs",
            problem="Imperial unit in metric locale",
            suggested_correction="Use mm",
            proof_text="Original: 15.6 inches",
            severity="high",
            confidence=0.95,
            review_required=False,
        )
    ]

    result = ComparisonEngine.compare_runs(current, previous, "failed", "completed")

    assert len(result[ComparisonStatus.NEW]) == 0
    assert len(result[ComparisonStatus.UNRESOLVED]) == 0
    assert len(result[ComparisonStatus.RESOLVED]) == 0
    assert len(result[ComparisonStatus.NOT_RECHECKED]) == 1


def test_compute_identity_fingerprint():
    """Test identity fingerprint computation."""
    fingerprint = ComparisonEngine.compute_identity_fingerprint(
        url="https://www.dell.com/en-us/shop/laptops",
        locale="en-US",
        rule_passage_id="rule-1",
        zone="dimensions_weight",
        locator="#specs",
        normalized_subject="dimension_unit",
    )

    assert "https://www.dell.com/en-us/shop/laptops" in fingerprint
    assert "en-US" in fingerprint
    assert "rule-1" in fingerprint


def test_normalize_subject():
    """Test subject normalization."""
    assert ComparisonEngine.normalize_subject("  Dimension Unit  ") == "dimension unit"
    assert ComparisonEngine.normalize_subject("DIMENSION UNIT") == "dimension unit"
