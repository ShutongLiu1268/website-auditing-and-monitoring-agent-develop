from collections.abc import Iterable, Mapping

from app.api.schemas import (
    CrossPageFieldResponse,
    CrossPageValueResponse,
    IssueResponse,
    TraceEntry,
)
from app.comparison.cross_page import CrossPageField
from app.domain.models import CheckResult, IssueObservation, PageSnapshot
from app.issues.reconciler import IssueReconciler

ZONE_CATEGORIES = {
    "configuration_selector": "Language",
    "configuration_cards": "Spelling",
    "dimensions_weight": "Dimensions",
    "media_gallery": "Accessibility",
    "tech_specs": "Specifications",
}


def rule_label(rule_text: str) -> str:
    lines = [line.strip() for line in rule_text.splitlines() if line.strip()]
    return (lines[0] if lines else rule_text)[:120]


def to_issue_response(
    result: CheckResult,
    snapshots: dict[str, PageSnapshot],
    status: str = "new",
    issue_key: str | None = None,
) -> IssueResponse:
    snapshot = snapshots.get(result.page_snapshot_id)
    locale = snapshot.locale if snapshot else "unknown"
    page = locale.upper()
    evaluator = "DSX · GPT-OSS" if result.model else "Deterministic fact tool"
    return IssueResponse(
        id=result.id,
        run_id=result.run_id,
        severity=result.severity.value if result.severity else "medium",
        status=status,
        rule=rule_label(result.rule_quote or result.rule_passage_id),
        category=ZONE_CATEGORIES.get(
            result.zone, result.zone.replace("_", " ").title()
        ),
        page=page,
        locale=locale,
        snippet=result.evidence_quote or "Evidence unavailable",
        problem=result.problem or "Issue detected by audit checkpoint.",
        correction=result.suggested_correction
        or "Review and correct the cited page content.",
        proof=result.proof_text or result.evidence_quote or "Evidence unavailable",
        locator=result.dom_locator or "Unavailable",
        evaluator=evaluator,
        confidence=result.confidence,
        review_required=result.review_required,
        reasoning=result.reasoning,
        reminder=result.reminder,
        issue_key=issue_key,
        capture_url=(
            f"/api/runs/{result.run_id}/snapshots/{result.page_snapshot_id}/html"
            if snapshot and snapshot.html_capture_id
            else None
        ),
    )


def to_observation_response(
    observation: IssueObservation,
    snapshot: PageSnapshot | None,
    status: str,
    issue_key: str | None = None,
) -> IssueResponse:
    """Map a persisted issue observation to an API finding."""
    locale = snapshot.locale if snapshot else "unknown"
    page = locale.upper()
    return IssueResponse(
        id=observation.issue_identity_id,
        run_id=observation.run_id,
        severity=observation.severity.value,
        status=status,
        rule=rule_label(observation.rule_quote),
        category=ZONE_CATEGORIES.get(
            observation.zone, observation.zone.replace("_", " ").title()
        ),
        page=page,
        locale=locale,
        snippet=observation.evidence_quote,
        problem=observation.problem,
        correction=observation.suggested_correction,
        proof=observation.proof_text,
        locator=observation.dom_locator,
        evaluator="Deterministic fact tool",
        confidence=observation.confidence,
        review_required=observation.review_required,
        reasoning=observation.reasoning,
        reminder=observation.reminder,
        issue_key=issue_key,
        capture_url=(
            f"/api/runs/{observation.run_id}/snapshots/{observation.page_snapshot_id}/html"
            if snapshot and snapshot.html_capture_id
            else None
        ),
    )


def to_issue_responses(
    results: Iterable[CheckResult],
    snapshots: dict[str, PageSnapshot],
    transitions: Mapping[str, str] | None = None,
) -> list[IssueResponse]:
    reconciler = IssueReconciler()
    issues = [result for result in results if result.outcome.value == "issue"]
    keys = reconciler.group_keys(
        (
            result.id,
            result.page_snapshot_id,
            result.rule_passage_id,
            result.zone,
            result.evidence_quote or "",
            result.dom_locator or "",
        )
        for result in issues
    )
    responses: list[IssueResponse] = []
    for result in issues:
        status = "new"
        snapshot = snapshots.get(result.page_snapshot_id)
        if transitions and snapshot:
            identity = reconciler.build_identity(result, snapshot)
            if identity:
                status = transitions.get(identity.id, "new")
        responses.append(to_issue_response(result, snapshots, status, keys[result.id]))
    return responses


def to_trace_entries(
    results: Iterable[CheckResult],
    locales: Mapping[str, str],
) -> list[TraceEntry]:
    """Show each checkpoint once per zone and outcome, with its locales and unique evidence."""
    groups: dict[tuple[str, str, str, str], list[CheckResult]] = {}
    for result in results:
        key = (
            result.rule_passage_id,
            result.zone,
            result.outcome.value,
            result.error or "",
        )
        groups.setdefault(key, []).append(result)
    entries: list[TraceEntry] = []
    for members in groups.values():
        first = members[0]
        found = list(
            dict.fromkeys(
                locales[member.page_snapshot_id]
                for member in members
                if member.page_snapshot_id in locales
            )
        )
        entries.append(
            TraceEntry(
                rule=rule_label(first.rule_quote or first.rule_passage_id),
                zone=first.zone,
                outcome=first.outcome.value,
                evaluator=" + ".join(
                    dict.fromkeys(
                        "DSX" if member.model else "Deterministic" for member in members
                    )
                ),
                detail=first.error or first.problem or "Checkpoint evaluated.",
                reasoning=first.reasoning,
                evidence=list(
                    dict.fromkeys(
                        member.evidence_quote
                        for member in members
                        if member.evidence_quote
                    )
                ),
                locale=found[0] if found else None,
                locales=found,
            )
        )
    return entries


def to_cross_page_responses(
    fields: Iterable[CrossPageField],
) -> list[CrossPageFieldResponse]:
    return [
        CrossPageFieldResponse(
            field=field.key,
            label=field.label,
            category=field.category,
            status=field.status,
            values=[
                CrossPageValueResponse(
                    locale=value.locale, url=value.url, value=value.value
                )
                for value in field.values
            ],
        )
        for field in fields
    ]
