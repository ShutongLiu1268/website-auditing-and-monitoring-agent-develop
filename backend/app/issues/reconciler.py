"""Stable issue identity and run-to-run reconciliation."""

import hashlib
from collections.abc import Iterable
from datetime import UTC, datetime

from app.domain.models import (
    CheckOutcome,
    CheckResult,
    ComparisonStatus,
    IssueIdentity,
    IssueObservation,
    PageSnapshot,
    Severity,
)


class IssueReconciler:
    """Create stable issue observations and compare comparable runs."""

    def build_identity(
        self,
        result: CheckResult,
        snapshot: PageSnapshot,
    ) -> IssueIdentity | None:
        """Build a stable identity for a reportable issue."""
        if result.outcome != CheckOutcome.ISSUE:
            return None
        normalized_subject = self._normalize_subject(
            result.evidence_quote or result.problem or ""
        )
        identity_id = self._fingerprint(
            snapshot.url,
            snapshot.locale,
            result.rule_passage_id,
            result.zone,
            result.dom_locator or "",
            str(result.occurrence),
            normalized_subject,
        )
        return IssueIdentity(
            id=identity_id,
            url=snapshot.url,
            locale=snapshot.locale,
            rule_passage_id=result.rule_passage_id,
            zone=result.zone,
            locator=result.dom_locator or "",
            normalized_subject=normalized_subject,
        )

    def build_observation(
        self,
        result: CheckResult,
        snapshot: PageSnapshot,
    ) -> IssueObservation | None:
        """Convert a reportable issue result to an observation."""
        identity = self.build_identity(result, snapshot)
        if identity is None:
            return None
        return IssueObservation(
            id=f"observation-{result.id}",
            issue_identity_id=identity.id,
            run_id=result.run_id,
            page_snapshot_id=result.page_snapshot_id,
            zone=result.zone,
            rule_quote=result.rule_quote or result.rule_passage_id,
            evidence_quote=result.evidence_quote or "",
            dom_locator=result.dom_locator or "",
            problem=result.problem or "Issue detected.",
            suggested_correction=result.suggested_correction
            or "Review the cited content.",
            proof_text=result.proof_text or result.evidence_quote or "",
            severity=result.severity or Severity.MEDIUM,
            confidence=result.confidence,
            review_required=result.review_required,
            reasoning=result.reasoning,
            reminder=result.reminder,
            observed_at=datetime.now(UTC),
        )

    def assign_occurrences(self, results: Iterable[CheckResult]) -> list[CheckResult]:
        """Number repeated issues of one checkpoint, zone, and locator on a page."""
        seen: dict[tuple[str, str, str, str], int] = {}
        numbered: list[CheckResult] = []
        for result in results:
            if result.outcome != CheckOutcome.ISSUE:
                numbered.append(result)
                continue
            key = (
                result.page_snapshot_id,
                result.rule_passage_id,
                result.zone,
                result.dom_locator or "",
            )
            occurrence = seen.get(key, 0)
            seen[key] = occurrence + 1
            numbered.append(result.model_copy(update={"occurrence": occurrence}))
        return numbered

    def group_keys(
        self, instances: Iterable[tuple[str, str, str, str, str, str]]
    ) -> dict[str, str]:
        """Key issues so one checkpoint text on several pages shares a key."""
        spots: dict[tuple[str, str, str, str], list[str]] = {}
        keys: dict[str, str] = {}
        for instance_id, page_id, passage_id, zone, quote, locator in instances:
            text = " ".join(quote.split()).casefold()
            if not text:
                keys[instance_id] = instance_id
                continue
            page_spots = spots.setdefault((page_id, passage_id, zone, text), [])
            if locator not in page_spots:
                page_spots.append(locator)
            keys[instance_id] = self._fingerprint(
                passage_id, zone, text, str(page_spots.index(locator))
            )
        return keys

    def compare(
        self,
        current_observations: Iterable[IssueObservation],
        previous_observations: Iterable[IssueObservation],
        *,
        current_run_completed: bool,
        comparable: bool = True,
    ) -> dict[ComparisonStatus, list[IssueObservation]]:
        """Classify issue transitions while respecting partial scans."""
        current = {item.issue_identity_id: item for item in current_observations}
        previous = {item.issue_identity_id: item for item in previous_observations}
        result: dict[ComparisonStatus, list[IssueObservation]] = {
            status: []
            for status in (
                ComparisonStatus.NEW,
                ComparisonStatus.UNRESOLVED,
                ComparisonStatus.RESOLVED,
                ComparisonStatus.NOT_RECHECKED,
                ComparisonStatus.CHANGED_PAGE,
            )
        }
        if not comparable:
            result[ComparisonStatus.CHANGED_PAGE].extend(current.values())
            result[ComparisonStatus.NOT_RECHECKED].extend(previous.values())
            return result

        for identity, observation in current.items():
            result[
                (
                    ComparisonStatus.UNRESOLVED
                    if identity in previous
                    else ComparisonStatus.NEW
                )
            ].append(observation)
        for identity, observation in previous.items():
            if identity not in current:
                status = (
                    ComparisonStatus.RESOLVED
                    if current_run_completed
                    else ComparisonStatus.NOT_RECHECKED
                )
                result[status].append(observation)
        return result

    @staticmethod
    def _normalize_subject(subject: str) -> str:
        """Normalize evidence for stable identity."""
        return " ".join(subject.lower().split())

    @staticmethod
    def _fingerprint(*parts: str) -> str:
        """Create a stable issue identity fingerprint."""
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
