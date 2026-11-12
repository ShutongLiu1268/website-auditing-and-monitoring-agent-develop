"""Unit tests for report generation."""

from app.domain.models import AuditRun, CheckOutcome, CheckResult, PageSnapshot, RunStatus
from app.reporting.generator import ReportGenerator


def test_report_generator_builds_summary_and_html():
    """Test report totals and HTML output."""
    run = AuditRun(
        id="run-1",
        audit_definition_id="audit-1",
        status=RunStatus.COMPLETED,
        total_pages=1,
        completed_pages=1,
    )
    snapshot = PageSnapshot(
        id="snapshot-1",
        run_id=run.id,
        url="https://example.test/pdp",
        locale="en-US",
        content_hash="hash",
        extraction_version="test",
    )
    result = CheckResult(
        id="result-1",
        run_id=run.id,
        page_snapshot_id=snapshot.id,
        rule_passage_id="rule-1",
        zone="hero",
        outcome=CheckOutcome.ISSUE,
        problem="Broken copy",
        evidence_quote="bad copy",
    )

    report = ReportGenerator().build(run, [result], {snapshot.id: snapshot})
    html = ReportGenerator().render_html(report)

    assert report.summary["total"] == 1
    assert report.summary["medium"] == 1
    assert "Broken copy" in html
