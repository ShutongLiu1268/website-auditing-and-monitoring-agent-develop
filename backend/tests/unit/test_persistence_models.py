"""Unit tests for crawl, schedule, and delivery models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.models import (
    AuditDefinition,
    AuditMode,
    CrawlScope,
    DeliveryAttempt,
    PageCoverage,
    PageTarget,
    Schedule,
)


def test_crawl_scope_defaults_and_bounds():
    """Test crawl scope defaults and validation bounds."""
    scope = CrawlScope()
    assert scope.page_limit == 25
    assert scope.max_depth == 0

    with pytest.raises(ValidationError):
        CrawlScope(page_limit=0)


def test_audit_definition_persists_scope():
    """Test audit definition contains crawl scope."""
    definition = AuditDefinition(
        id="audit-1",
        mode=AuditMode.R3,
        targets=[PageTarget(url="https://example.test", locale="en-US")],
        rule_version="v1",
        scope=CrawlScope(include_paths=["/products"], page_limit=10),
    )

    assert definition.scope.include_paths == ["/products"]
    assert definition.scope.page_limit == 10


def test_schedule_and_delivery_models():
    """Test recurring schedule and delivery attempt models."""
    next_run = datetime(2026, 10, 10, tzinfo=UTC)
    schedule = Schedule(
        id="schedule-1",
        audit_definition_id="audit-1",
        frequency="daily",
        local_time="08:00",
        timezone="America/New_York",
        recipients=["webteam@example.com"],
        next_run_at_utc=next_run,
    )
    attempt = DeliveryAttempt(
        id="delivery-1",
        schedule_id=schedule.id,
        run_id="run-1",
        recipients=schedule.recipients,
        status="queued",
    )

    assert schedule.next_run_at_utc == next_run
    assert attempt.status == "queued"


def test_page_coverage_defaults():
    """Test coverage counters start at zero."""
    coverage = PageCoverage()
    assert coverage.model_dump() == {
        "scanned": 0,
        "skipped": 0,
        "inaccessible": 0,
        "duplicate": 0,
        "timeout": 0,
    }
