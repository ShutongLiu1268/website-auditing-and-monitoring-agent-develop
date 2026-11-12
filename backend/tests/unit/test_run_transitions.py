from app.comparison.transitions import compare_runs
from app.domain.models import ComparisonStatus, IssueObservation, PageSnapshot, Severity


def _snapshot(snapshot_id: str, locale: str) -> PageSnapshot:
    return PageSnapshot(
        id=snapshot_id,
        run_id="run",
        url=f"https://www.dell.com/{locale}/shop/laptops",
        locale=locale,
        content_hash="hash",
        extraction_version="fixture-0.1.0",
    )


def _observation(identity_id: str, snapshot_id: str) -> IssueObservation:
    return IssueObservation(
        id=f"observation-{identity_id}",
        issue_identity_id=identity_id,
        run_id="run",
        page_snapshot_id=snapshot_id,
        rule_quote="R2 & R3 · Section 7.1",
        evidence_quote="16 GB",
        dom_locator="#top-specs",
        problem="Top specification disagrees.",
        suggested_correction="Align the values.",
        proof_text="Top specs show 16 GB.",
        severity=Severity.MEDIUM,
        confidence=0.9,
        review_required=False,
    )


def _identities(items: list[IssueObservation]) -> list[str]:
    return [item.issue_identity_id for item in items]


def test_missing_issue_is_resolved_on_rechecked_page_and_not_rechecked_on_skipped_page():
    snapshots = {
        "previous-en-us": _snapshot("previous-en-us", "en-us"),
        "previous-fr-ca": _snapshot("previous-fr-ca", "fr-ca"),
        "current-en-ca": _snapshot("current-en-ca", "en-ca"),
    }
    previous = [
        _observation("fixed", "previous-en-us"),
        _observation("skipped", "previous-fr-ca"),
    ]
    current = [_observation("new", "current-en-ca")]

    grouped = compare_runs(
        current, previous, snapshots, rechecked_locales={"en-us", "en-ca"}
    )

    assert _identities(grouped[ComparisonStatus.NEW]) == ["new"]
    assert _identities(grouped[ComparisonStatus.RESOLVED]) == ["fixed"]
    assert _identities(grouped[ComparisonStatus.NOT_RECHECKED]) == ["skipped"]
    assert grouped[ComparisonStatus.UNRESOLVED] == []


def test_issue_present_in_both_runs_is_unresolved():
    snapshots = {
        "previous": _snapshot("previous", "en-us"),
        "current": _snapshot("current", "en-us"),
    }

    grouped = compare_runs(
        [_observation("still", "current")],
        [_observation("still", "previous")],
        snapshots,
        rechecked_locales={"en-us"},
    )

    assert _identities(grouped[ComparisonStatus.UNRESOLVED]) == ["still"]
    assert grouped[ComparisonStatus.NEW] == []
