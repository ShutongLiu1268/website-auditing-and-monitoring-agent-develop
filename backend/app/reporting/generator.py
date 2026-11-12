"""Shared report generation for API and email delivery."""

from html import escape

from app.api.mappers import to_issue_responses
from app.api.schemas import ReportResponse, RunStatusResponse
from app.domain.models import AuditRun, CheckResult, PageSnapshot


class ReportGenerator:
    """Generate stable report models and HTML output."""

    def build(
        self,
        run: AuditRun,
        results: list[CheckResult],
        snapshots: dict[str, PageSnapshot],
    ) -> ReportResponse:
        """Build a report from persisted run results."""
        findings = to_issue_responses(results, snapshots)
        summary = {
            "critical": sum(item.severity == "critical" for item in findings),
            "high": sum(item.severity == "high" for item in findings),
            "medium": sum(item.severity == "medium" for item in findings),
            "low": sum(item.severity == "low" for item in findings),
            "total": len(findings),
            "new": sum(item.status == "new" for item in findings),
            "unresolved": sum(item.status == "unresolved" for item in findings),
            "resolved": sum(item.status == "resolved" for item in findings),
            "not_rechecked": sum(item.status == "not_rechecked" for item in findings),
        }
        run_response = RunStatusResponse(
            run_id=run.id,
            audit_definition_id=run.audit_definition_id,
            status=run.status,
            progress=(
                0 if run.total_pages == 0 else round(run.completed_pages / run.total_pages * 100)
            ),
            total_pages=run.total_pages,
            completed_pages=run.completed_pages,
            failed_pages=run.failed_pages,
            started_at=run.started_at,
            completed_at=run.completed_at,
            warnings=run.warnings,
            coverage=run.coverage,
        )
        return ReportResponse(run=run_response, findings=findings, summary=summary)

    def render_html(self, report: ReportResponse) -> str:
        """Render a compact report suitable for SMTP delivery."""
        rows = "".join(
            "<tr>"
            f"<td>{escape(item.page)}</td>"
            f"<td>{escape(item.rule)}</td>"
            f"<td>{escape(item.problem)}</td>"
            f"<td>{escape(item.severity)}</td>"
            f"<td>{escape(item.correction)}</td>"
            "</tr>"
            for item in report.findings
        )
        return (
            "<html><body>"
            f"<h1>NPL PDP Audit Report</h1><p>Status: {escape(report.run.status.value)}</p>"
            f"<p>Issues: {report.summary['total']}</p>"
            "<table><thead><tr><th>Page</th><th>Rule</th><th>Problem</th>"
            "<th>Severity</th><th>Correction</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></body></html>"
        )
