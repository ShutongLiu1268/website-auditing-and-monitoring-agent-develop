"""Unit tests for schedule calculations and lifecycle."""

from datetime import UTC, datetime

import pytest

from app.schedules.service import next_occurrence


def test_daily_occurrence_converts_timezone():
    """Test local time converts to UTC."""
    result = next_occurrence(
        "08:00",
        "America/New_York",
        "daily",
        datetime(2026, 10, 9, 10, 0, tzinfo=UTC),
    )

    assert result.tzinfo is not None
    assert result.hour == 12


def test_weekly_occurrence_moves_one_week_when_time_passed():
    """Test weekly recurrence."""
    result = next_occurrence(
        "08:00",
        "UTC",
        "weekly",
        datetime(2026, 10, 9, 10, 0, tzinfo=UTC),
    )

    assert result == datetime(2026, 10, 16, 8, tzinfo=UTC)


def test_invalid_schedule_values_raise():
    """Test invalid timezone/time/frequency values."""
    with pytest.raises(ValueError):
        next_occurrence("25:00", "UTC", "daily", datetime.now(UTC))
    with pytest.raises(ValueError):
        next_occurrence("08:00", "Not/AZone", "daily", datetime.now(UTC))
    with pytest.raises(ValueError):
        next_occurrence("08:00", "UTC", "monthly", datetime.now(UTC))
