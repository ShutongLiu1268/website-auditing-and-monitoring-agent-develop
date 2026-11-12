from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from app.domain.models import (
    ComparisonStatus,
    IssueIdentity,
    IssueObservation,
    PageSnapshot,
)
from app.issues.reconciler import IssueReconciler
from app.persistence.repositories import (
    AuditRunRepository,
    IssueIdentityRepository,
    IssueObservationRepository,
    PageSnapshotRepository,
)


@dataclass(frozen=True)
class RunTransitions:
    previous_run_id: str | None
    current_snapshots: list[PageSnapshot]
    snapshots: dict[str, PageSnapshot]
    grouped: dict[ComparisonStatus, list[IssueObservation]]
    issue_keys: dict[tuple[str, str], str]

    def identity_statuses(self) -> dict[str, str]:
        return {
            observation.issue_identity_id: status.value
            for status in (ComparisonStatus.NEW, ComparisonStatus.UNRESOLVED)
            for observation in self.grouped[status]
        }


def compare_runs(
    current_observations: Iterable[IssueObservation],
    previous_observations: Iterable[IssueObservation],
    snapshots: Mapping[str, PageSnapshot],
    rechecked_locales: set[str],
) -> dict[ComparisonStatus, list[IssueObservation]]:
    current = list(current_observations)
    previous = list(previous_observations)
    reconciler = IssueReconciler()
    grouped: dict[ComparisonStatus, list[IssueObservation]] = {
        status: [] for status in ComparisonStatus
    }
    for locale in sorted({_locale(item, snapshots) for item in (*current, *previous)}):
        transitions = reconciler.compare(
            [item for item in current if _locale(item, snapshots) == locale],
            [item for item in previous if _locale(item, snapshots) == locale],
            current_run_completed=locale in rechecked_locales,
        )
        for status, items in transitions.items():
            grouped[status].extend(items)
    return grouped


async def load_run_transitions(
    run_id: str,
    run_repo: AuditRunRepository,
    snapshot_repo: PageSnapshotRepository,
    observation_repo: IssueObservationRepository,
    identity_repo: IssueIdentityRepository,
) -> RunTransitions:
    run = await run_repo.get(run_id)
    previous = (
        await run_repo.find_baseline(run.comparison_key, run_id, run.started_at)
        if run and run.comparison_key and run.started_at
        else None
    )
    current_snapshots = await snapshot_repo.get_by_run(run_id)
    previous_snapshots = await snapshot_repo.get_by_run(previous.id) if previous else []
    snapshots = {
        snapshot.id: snapshot for snapshot in [*current_snapshots, *previous_snapshots]
    }
    current_observations = await observation_repo.get_by_run(run_id)
    previous_observations = (
        await observation_repo.get_by_run(previous.id) if previous else []
    )
    identities = await identity_repo.get_many(
        list(
            {
                observation.issue_identity_id
                for observation in [*current_observations, *previous_observations]
            }
        )
    )
    issue_keys = {
        **_observation_keys(current_observations, identities),
        **_observation_keys(previous_observations, identities),
    }
    grouped = compare_runs(
        current_observations,
        previous_observations,
        snapshots,
        {snapshot.locale for snapshot in current_snapshots},
    )
    return RunTransitions(
        previous_run_id=previous.id if previous else None,
        current_snapshots=current_snapshots,
        snapshots=snapshots,
        grouped=grouped,
        issue_keys=issue_keys,
    )


def _observation_keys(
    observations: Iterable[IssueObservation],
    identities: Mapping[str, IssueIdentity],
) -> dict[tuple[str, str], str]:
    items = list(observations)
    rows: list[tuple[str, str, str, str, str, str]] = []
    for observation in items:
        identity = identities.get(observation.issue_identity_id)
        passage_id = identity.rule_passage_id if identity else observation.rule_quote
        rows.append(
            (
                observation.id,
                observation.page_snapshot_id,
                passage_id,
                observation.zone,
                observation.evidence_quote,
                observation.dom_locator,
            )
        )
    keys = IssueReconciler().group_keys(rows)
    return {
        (observation.run_id, observation.id): keys[observation.id]
        for observation in items
    }


def _locale(
    observation: IssueObservation, snapshots: Mapping[str, PageSnapshot]
) -> str:
    snapshot = snapshots.get(observation.page_snapshot_id)
    return snapshot.locale if snapshot else ""
