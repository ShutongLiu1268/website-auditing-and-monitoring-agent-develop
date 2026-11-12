"""Unit tests for report delivery."""

from datetime import UTC, datetime

import pytest

from app.delivery.service import DeliveryService
from app.domain.models import AuditRun, RunStatus, Schedule
from app.reporting.generator import ReportGenerator


@pytest.mark.asyncio
async def test_delivery_records_success(mocker):
    """Test SMTP success is persisted."""
    repository = mocker.MagicMock()
    repository.create = mocker.AsyncMock(side_effect=lambda value: value)
    repository.update = mocker.AsyncMock(side_effect=lambda value: value)
    transport = mocker.MagicMock()
    transport.send = mocker.AsyncMock(return_value="250 accepted")
    schedule = Schedule(
        id="schedule-1",
        audit_definition_id="audit-1",
        frequency="daily",
        local_time="08:00",
        timezone="UTC",
        recipients=["team@example.com"],
        next_run_at_utc=datetime.now(UTC),
    )
    run = AuditRun(id="run-1", audit_definition_id="audit-1", status=RunStatus.COMPLETED)
    report = mocker.MagicMock()
    config = mocker.MagicMock(REPORT_BRAND_NAME="NPL PDP Audit")

    attempt = await DeliveryService(
        repository,
        transport,
        ReportGenerator(),
        config,
    ).deliver(schedule, run, report)

    assert attempt.status == "sent"
    assert attempt.provider_message_id == "250 accepted"
    repository.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_delivery_records_failure(mocker):
    """Test SMTP failure remains visible for retry."""
    repository = mocker.MagicMock()
    repository.create = mocker.AsyncMock(side_effect=lambda value: value)
    repository.update = mocker.AsyncMock(side_effect=lambda value: value)
    transport = mocker.MagicMock()
    transport.send = mocker.AsyncMock(side_effect=RuntimeError("smtp down"))
    schedule = Schedule(
        id="schedule-1",
        audit_definition_id="audit-1",
        frequency="daily",
        local_time="08:00",
        timezone="UTC",
        recipients=["team@example.com"],
        next_run_at_utc=datetime.now(UTC),
    )
    run = AuditRun(id="run-1", audit_definition_id="audit-1", status=RunStatus.COMPLETED)
    config = mocker.MagicMock(REPORT_BRAND_NAME="NPL PDP Audit")

    attempt = await DeliveryService(
        repository,
        transport,
        ReportGenerator(),
        config,
    ).deliver(schedule, run, mocker.MagicMock())

    assert attempt.status == "failed"
    assert attempt.error_code == "RuntimeError"
