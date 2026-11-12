from app.api.checklist import build_checklist
from app.domain.models import (
    AuditMode,
    CheckOutcome,
    CheckResult,
    RulePassage,
    RunStatus,
)


def _passage(
    passage_id: str,
    heading: list[str],
    start: int,
    modes: list[AuditMode] | None = None,
) -> RulePassage:
    return RulePassage(
        id=passage_id,
        version="v1",
        heading_path=heading,
        source_range=(start, start + 10),
        original_text="text",
        modes=modes or [AuditMode.R3],
    )


def _result(passage_id: str, outcome: CheckOutcome, page: str = "page-1") -> CheckResult:
    return CheckResult(
        id=f"{passage_id}-{outcome.value}-{page}",
        run_id="run-1",
        page_snapshot_id=page,
        rule_passage_id=passage_id,
        zone="features",
        outcome=outcome,
    )


def _checklist(passages, results=(), status=RunStatus.COMPLETED, mode=AuditMode.R3):
    return build_checklist("run-1", "v1", mode, status, passages, results)


def _status_of(response, passage_id):
    return next(
        checkpoint.status
        for group in response.groups
        for checkpoint in group.checkpoints
        if checkpoint.id == passage_id
    )


def test_groups_follow_guide_order_and_mode():
    passages = [
        _passage("b", ["Regional", "R3R-01 Metric"], 30),
        _passage("r2-only", ["Detailed", "SECTION 9 Old"], 5, [AuditMode.R2]),
        _passage("a", ["Detailed", "SECTION 1 Spelling"], 10),
    ]
    response = _checklist(passages)
    assert [group.title for group in response.groups] == ["Detailed", "Regional"]
    assert [checkpoint.id for group in response.groups for checkpoint in group.checkpoints] == [
        "a",
        "b",
    ]
    assert response.groups[0].checkpoints[0].label == "SECTION 1 Spelling"
    assert response.counts.total == 2
    assert response.counts.not_applicable == 2


def test_status_precedence():
    cases = {
        "issue-wins": ([CheckOutcome.PASS, CheckOutcome.ISSUE, CheckOutcome.ERROR], "issues"),
        "error-beats-pass": ([CheckOutcome.PASS, CheckOutcome.ERROR], "error"),
        "pass-beats-not-evaluated": ([CheckOutcome.NOT_EVALUATED, CheckOutcome.PASS], "pass"),
        "not-evaluated-beats-not-applicable": (
            [CheckOutcome.NOT_APPLICABLE, CheckOutcome.NOT_EVALUATED],
            "not_evaluated",
        ),
    }
    passages = [_passage(name, ["Group", name], index) for index, name in enumerate(cases)]
    results = [
        _result(name, outcome, f"page-{index}")
        for name, (outcomes, _) in cases.items()
        for index, outcome in enumerate(outcomes)
    ]
    response = _checklist(passages, results)
    for name, (_, expected) in cases.items():
        assert _status_of(response, name) == expected


def test_missing_results_pending_while_active_then_not_applicable():
    passages = [_passage("p", ["Group", "Check"], 1)]
    assert _status_of(_checklist(passages, status=RunStatus.RUNNING), "p") == "pending"
    assert _status_of(_checklist(passages, status=RunStatus.QUEUED), "p") == "pending"
    assert _status_of(_checklist(passages, status=RunStatus.PARTIAL), "p") == "not_applicable"
    assert _status_of(_checklist(passages, status=RunStatus.COMPLETED), "p") == "not_applicable"


def test_issue_pages_and_counts():
    passages = [_passage("p", ["Group", "Check"], 1), _passage("q", ["Group", "Other"], 2)]
    results = [
        _result("p", CheckOutcome.ISSUE, "page-1"),
        _result("p", CheckOutcome.ISSUE, "page-2"),
        _result("p", CheckOutcome.PASS, "page-3"),
        _result("q", CheckOutcome.PASS, "page-1"),
    ]
    response = _checklist(passages, results, status=RunStatus.RUNNING)
    checkpoint = response.groups[0].checkpoints[0]
    assert (checkpoint.status, checkpoint.issues, checkpoint.pages) == ("issues", 2, 3)
    assert response.counts.total == 2
    assert response.counts.checked == 2
    assert response.counts.issues == 1
    assert response.counts.pending == 0
