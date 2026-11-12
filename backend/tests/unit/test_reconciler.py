"""Unit tests for issue reconciliation."""

from app.api.mappers import to_observation_response
from app.domain.models import (
    CheckOutcome,
    CheckResult,
    ComparisonStatus,
    PageSnapshot,
)
from app.issues.reconciler import IssueReconciler


def _snapshot() -> PageSnapshot:
    """Build a snapshot."""
    return PageSnapshot(
        id="snapshot-1",
        run_id="run-1",
        url="https://example.test/pdp",
        locale="en-US",
        content_hash="hash",
        extraction_version="test",
    )


def _result(result_id: str, evidence: str) -> CheckResult:
    """Build an issue result."""
    return CheckResult(
        id=result_id,
        run_id="run-1",
        page_snapshot_id="snapshot-1",
        rule_passage_id="rule-1",
        zone="hero",
        outcome=CheckOutcome.ISSUE,
        rule_quote="Check copy.",
        evidence_quote=evidence,
        dom_locator="#hero",
        problem="Copy issue",
    )


def _observation(reconciler: IssueReconciler, result_id: str, evidence: str):
    """Build an observation from a result."""
    return reconciler.build_observation(_result(result_id, evidence), _snapshot())


def test_reconciler_classifies_new_and_unresolved():
    """Test current issues are new or unresolved."""
    reconciler = IssueReconciler()
    previous = _observation(reconciler, "old", "same")
    current_same = _observation(reconciler, "new", "same")
    current_new = _observation(reconciler, "newer", "new")

    result = reconciler.compare(
        [current_same, current_new],
        [previous],
        current_run_completed=True,
    )

    assert len(result[ComparisonStatus.UNRESOLVED]) == 1
    assert len(result[ComparisonStatus.NEW]) == 1


def test_reconciler_classifies_resolved_only_after_complete_run():
    """Test partial runs do not resolve missing issues."""
    reconciler = IssueReconciler()
    previous = _observation(reconciler, "old", "same")

    partial = reconciler.compare([], [previous], current_run_completed=False)
    complete = reconciler.compare([], [previous], current_run_completed=True)

    assert len(partial[ComparisonStatus.NOT_RECHECKED]) == 1
    assert len(complete[ComparisonStatus.RESOLVED]) == 1


def test_reconciler_marks_scope_mismatch_changed():
    """Test incomparable runs are disclosed."""
    reconciler = IssueReconciler()
    current = _observation(reconciler, "current", "new")
    previous = _observation(reconciler, "old", "old")

    result = reconciler.compare(
        [current], [previous], current_run_completed=True, comparable=False
    )

    assert len(result[ComparisonStatus.CHANGED_PAGE]) == 1
    assert len(result[ComparisonStatus.NOT_RECHECKED]) == 1


def test_reconciler_ignores_non_issue_results():
    """Test passes do not create observations."""
    reconciler = IssueReconciler()
    result = CheckResult(
        id="pass",
        run_id="run-1",
        page_snapshot_id="snapshot-1",
        rule_passage_id="rule-1",
        zone="hero",
        outcome=CheckOutcome.PASS,
    )

    assert reconciler.build_observation(result, _snapshot()) is None


def test_observation_response_carries_check_reasoning():
    """Test comparison responses carry the checkpoint reasoning."""
    result = _result("reasoned", "same").model_copy(
        update={"reasoning": "The heading uses the US spelling."}
    )

    observation = IssueReconciler().build_observation(result, _snapshot())
    assert observation is not None
    response = to_observation_response(observation, None, "new")

    assert response.reasoning == "The heading uses the US spelling."


def test_observation_keeps_check_reminder():
    """Test observations carry the checkpoint reminder into comparisons."""
    result = _result("reminded", "same").model_copy(
        update={"reminder": "Rule not finalized and in discussion."}
    )

    observation = IssueReconciler().build_observation(result, _snapshot())

    assert observation is not None
    assert observation.reminder == "Rule not finalized and in discussion."


def test_observation_response_carries_check_reminder():
    """Test comparison responses carry the checkpoint reminder."""
    result = _result("reminded", "same").model_copy(
        update={"reminder": "Rule not finalized and in discussion."}
    )
    observation = IssueReconciler().build_observation(result, _snapshot())
    assert observation is not None

    response = to_observation_response(observation, None, "new")

    assert response.reminder == "Rule not finalized and in discussion."
