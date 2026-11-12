from collections import defaultdict
from collections.abc import Iterable

from app.api.schemas import (
    ChecklistCheckpoint,
    ChecklistCounts,
    ChecklistGroup,
    ChecklistResponse,
    ChecklistStatus,
)
from app.domain.models import (
    AuditMode,
    CheckOutcome,
    CheckResult,
    RulePassage,
    RunStatus,
)

ACTIVE_STATUSES = {RunStatus.QUEUED, RunStatus.RUNNING}
CHECKED_STATUSES = {"pass", "issues", "error"}


def build_checklist(
    run_id: str,
    rule_version: str,
    mode: AuditMode,
    run_status: RunStatus,
    passages: Iterable[RulePassage],
    results: Iterable[CheckResult],
) -> ChecklistResponse:
    results_by_passage: defaultdict[str, list[CheckResult]] = defaultdict(list)
    for result in results:
        results_by_passage[result.rule_passage_id].append(result)
    active = run_status in ACTIVE_STATUSES
    applicable = sorted(
        (passage for passage in passages if mode in passage.modes),
        key=lambda passage: passage.source_range,
    )
    groups: dict[str, list[ChecklistCheckpoint]] = defaultdict(list)
    for passage in applicable:
        members = results_by_passage.get(passage.id, [])
        title = passage.heading_path[0] if passage.heading_path else "Other"
        label = passage.heading_path[1] if len(passage.heading_path) > 1 else title
        groups[title].append(
            ChecklistCheckpoint(
                id=passage.id,
                label=label,
                status=_status(members, active),
                issues=sum(member.outcome == CheckOutcome.ISSUE for member in members),
                pages=len({member.page_snapshot_id for member in members}),
            )
        )
    checkpoints = [checkpoint for rows in groups.values() for checkpoint in rows]
    return ChecklistResponse(
        run_id=run_id,
        rule_version=rule_version,
        mode=mode,
        run_status=run_status,
        counts=_counts(checkpoints),
        groups=[
            ChecklistGroup(title=title, counts=_counts(rows), checkpoints=rows)
            for title, rows in groups.items()
        ],
    )


def _status(members: list[CheckResult], active: bool) -> ChecklistStatus:
    outcomes = {member.outcome for member in members}
    if CheckOutcome.ISSUE in outcomes:
        return "issues"
    if CheckOutcome.ERROR in outcomes:
        return "error"
    if CheckOutcome.PASS in outcomes:
        return "pass"
    if CheckOutcome.NOT_EVALUATED in outcomes:
        return "not_evaluated"
    if CheckOutcome.NOT_APPLICABLE in outcomes:
        return "not_applicable"
    return "pending" if active else "not_applicable"


def _counts(checkpoints: Iterable[ChecklistCheckpoint]) -> ChecklistCounts:
    statuses = [checkpoint.status for checkpoint in checkpoints]
    return ChecklistCounts(
        total=len(statuses),
        checked=sum(status in CHECKED_STATUSES for status in statuses),
        issues=statuses.count("issues"),
        not_evaluated=statuses.count("not_evaluated"),
        pending=statuses.count("pending"),
        not_applicable=statuses.count("not_applicable"),
    )
