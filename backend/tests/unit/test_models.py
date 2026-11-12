"""
Unit tests for domain models.
"""

from app.domain.models import (
    AuditDefinition,
    AuditMode,
    CheckOutcome,
    CheckResult,
    IssueIdentity,
    IssueObservation,
    PageTarget,
    RulePassage,
    Severity,
)


def test_page_target_valid():
    """Test valid PageTarget."""
    target = PageTarget(url="https://www.dell.com/en-us/shop/laptops", locale="en-US")
    assert target.locale == "en-US"
    assert target.country is None


def test_page_target_with_country():
    """Test PageTarget with country."""
    from pydantic import HttpUrl

    target = PageTarget(
        url=HttpUrl("https://www.dell.com/en-ca/shop/laptops"),
        locale="en-CA",
        country="CA",
    )
    assert target.country == "CA"


def test_audit_definition():
    """Test AuditDefinition creation."""
    from pydantic import HttpUrl

    targets = [
        PageTarget(
            url=HttpUrl("https://www.dell.com/en-us/shop/laptops"),
            locale="en-US",
            country="US",
        )
    ]
    definition = AuditDefinition(
        id="audit-1", mode=AuditMode.R3, targets=targets, rule_version="0.1.0"
    )
    assert definition.mode == AuditMode.R3
    assert len(definition.targets) == 1


def test_rule_passage():
    """Test RulePassage with all fields."""
    passage = RulePassage(
        id="rule-1",
        version="0.1.0",
        heading_path=["Section 1", "Dimensions"],
        source_range=(10, 20),
        original_text="Check dimensions are correct.",
        modes=[AuditMode.R3],
        markets=["en-US", "en-CA"],
        zones=["dimensions_weight"],
        severity=Severity.HIGH,
    )
    assert passage.severity == Severity.HIGH
    assert "en-US" in passage.markets


def test_check_result_pass():
    """Test CheckResult with pass outcome."""
    result = CheckResult(
        id="check-1",
        run_id="run-1",
        page_snapshot_id="snapshot-1",
        rule_passage_id="rule-1",
        zone="dimensions_weight",
        outcome=CheckOutcome.PASS,
    )
    assert result.outcome == CheckOutcome.PASS
    assert result.problem is None


def test_check_result_issue():
    """Test CheckResult with issue outcome."""
    result = CheckResult(
        id="check-2",
        run_id="run-1",
        page_snapshot_id="snapshot-1",
        rule_passage_id="rule-1",
        zone="dimensions_weight",
        outcome=CheckOutcome.ISSUE,
        problem="Dimension unit mismatch",
        suggested_correction="Use metric units",
        proof_text="Original: 15.6 inches",
        severity=Severity.HIGH,
        rule_quote="Use metric units for non-US locales",
        evidence_quote="15.6 inches",
        dom_locator="#specs-table > tr:nth-child(2) > td",
        confidence=0.95,
    )
    assert result.outcome == CheckOutcome.ISSUE
    assert result.severity == Severity.HIGH
    assert result.confidence == 0.95


def test_issue_identity():
    """Test IssueIdentity."""
    identity = IssueIdentity(
        id="issue-1",
        url="https://www.dell.com/en-us/shop/laptops",
        locale="en-US",
        rule_passage_id="rule-1",
        zone="dimensions_weight",
        locator="#specs-table > tr:nth-child(2) > td",
        normalized_subject="dimension_unit",
    )
    assert identity.url == "https://www.dell.com/en-us/shop/laptops"


def test_issue_observation():
    """Test IssueObservation."""
    observation = IssueObservation(
        id="obs-1",
        issue_identity_id="issue-1",
        run_id="run-1",
        page_snapshot_id="snapshot-1",
        rule_quote="Use metric units",
        evidence_quote="15.6 inches",
        dom_locator="#specs-table > tr:nth-child(2) > td",
        problem="Dimension unit mismatch",
        suggested_correction="Use metric units",
        proof_text="Original: 15.6 inches",
        severity=Severity.HIGH,
        confidence=0.95,
        review_required=False,
    )
    assert observation.severity == Severity.HIGH
    assert observation.review_required is False


def test_rule_passage_declares_markets_and_review():
    """Test RulePassage carries declared markets and review rule."""
    passage = RulePassage(
        id="SPR-06",
        version="v1",
        heading_path=["Sprint/Launch audit", "SPR-06"],
        source_range=(1, 2),
        original_text="Spelling.",
        modes=[AuditMode.SPRINT_LAUNCH],
        markets=["global"],
        review="en-CA",
    )
    assert passage.markets == ["global"]
    assert passage.review == "en-CA"
    assert not hasattr(passage, "locales")
    assert not hasattr(passage, "review_required")


def test_check_result_carries_reminder():
    """Test CheckResult carries the checkpoint reminder."""
    result = CheckResult(
        id="r1",
        run_id="run-1",
        page_snapshot_id="snap-1",
        rule_passage_id="D3",
        zone="tech_specs",
        outcome=CheckOutcome.ISSUE,
        reminder="Rule not finalized and in discussion.",
    )
    assert result.reminder == "Rule not finalized and in discussion."
