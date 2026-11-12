"""
Comparison engine for issue tracking across runs.
"""

from app.domain.models import (
    ComparisonStatus,
    IssueObservation,
)


class ComparisonEngine:
    """Compares issues between runs and determines transitions."""

    @staticmethod
    def compare_runs(
        current_observations: list[IssueObservation],
        previous_observations: list[IssueObservation],
        current_run_status: str,
        previous_run_status: str,
    ) -> dict[ComparisonStatus, list[IssueObservation]]:
        """Compare observations and group by comparison status."""
        current_map = {obs.issue_identity_id: obs for obs in current_observations}
        previous_map = {obs.issue_identity_id: obs for obs in previous_observations}

        result: dict[ComparisonStatus, list[IssueObservation]] = {
            ComparisonStatus.NEW: [],
            ComparisonStatus.UNRESOLVED: [],
            ComparisonStatus.RESOLVED: [],
            ComparisonStatus.NOT_RECHECKED: [],
        }

        # Check current observations
        for identity_id, current_obs in current_map.items():
            if identity_id in previous_map:
                # Issue exists in both runs
                result[ComparisonStatus.UNRESOLVED].append(current_obs)
            else:
                # New issue
                result[ComparisonStatus.NEW].append(current_obs)

        # Check resolved issues (in previous but not current)
        for identity_id, previous_obs in previous_map.items():
            if identity_id not in current_map:
                # Issue was in previous run but not current
                # Only mark as resolved if current run completed successfully
                if current_run_status == "completed":
                    result[ComparisonStatus.RESOLVED].append(previous_obs)
                else:
                    result[ComparisonStatus.NOT_RECHECKED].append(previous_obs)

        return result

    @staticmethod
    def compute_identity_fingerprint(
        url: str,
        locale: str,
        rule_passage_id: str,
        zone: str,
        locator: str,
        normalized_subject: str,
    ) -> str:
        """Compute stable fingerprint for issue identity."""
        parts = [
            url,
            locale,
            rule_passage_id,
            zone,
            locator,
            normalized_subject,
        ]
        return "|".join(parts)

    @staticmethod
    def normalize_subject(text: str) -> str:
        """Normalize text for identity comparison."""
        # Lowercase, strip whitespace, normalize unicode
        return text.lower().strip()
