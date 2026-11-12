"""Timezone-aware recurring schedule service."""

import asyncio
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import settings
from app.domain.models import AuditDefinition, Schedule
from app.persistence.repositories import ScheduleRepository


class ScheduleService:
    """Create, update, and claim recurring schedules."""

    def __init__(self, repository: ScheduleRepository) -> None:
        self._repository = repository

    async def create(
        self,
        audit_definition: AuditDefinition,
        frequency: str,
        local_time: str,
        timezone: str,
        recipients: list[str],
        now_utc: datetime | None = None,
    ) -> Schedule:
        """Create a validated schedule."""
        next_run = next_occurrence(
            local_time,
            timezone,
            frequency,
            now_utc or datetime.now(UTC),
        )
        schedule = Schedule(
            id=f"schedule-{audit_definition.id}-{int(next_run.timestamp())}",
            audit_definition_id=audit_definition.id,
            frequency=frequency,
            local_time=local_time,
            timezone=timezone,
            recipients=recipients,
            next_run_at_utc=next_run,
        )
        return await self._repository.create(schedule)

    async def list(self) -> list[Schedule]:
        """List schedules."""
        return await self._repository.list()

    async def pause(self, schedule: Schedule) -> Schedule:
        """Pause a schedule."""
        schedule.enabled = False
        schedule.updated_at = datetime.now(UTC)
        return await self._repository.update(schedule)

    async def resume(self, schedule: Schedule) -> Schedule:
        """Resume a schedule with a fresh next-run time."""
        schedule.enabled = True
        schedule.next_run_at_utc = next_occurrence(
            schedule.local_time,
            schedule.timezone,
            schedule.frequency,
            datetime.now(UTC),
        )
        schedule.updated_at = datetime.now(UTC)
        return await self._repository.update(schedule)

    async def run_forever(self, on_due_schedule) -> None:
        """Poll and claim due schedules until canceled."""
        while True:
            now = datetime.now(UTC)
            lease_until = now + timedelta(seconds=settings.SCHEDULER_POLL_SECONDS * 2)
            schedule = await self._repository.claim_due_schedule(now, lease_until)
            if schedule:
                await on_due_schedule(schedule)
                schedule.next_run_at_utc = next_occurrence(
                    schedule.local_time,
                    schedule.timezone,
                    schedule.frequency,
                    now,
                )
                schedule.lease_until_utc = None
                schedule.updated_at = datetime.now(UTC)
                await self._repository.update(schedule)
            await asyncio.sleep(settings.SCHEDULER_POLL_SECONDS)


def next_occurrence(
    local_time: str,
    timezone: str,
    frequency: str,
    now_utc: datetime,
) -> datetime:
    """Calculate next daily or weekly occurrence in UTC."""
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {timezone}") from exc
    try:
        hour, minute = (int(value) for value in local_time.split(":", 1))
    except ValueError as exc:
        raise ValueError("local_time must use HH:MM format") from exc
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("local_time must use HH:MM format")
    if frequency not in {"daily", "weekly"}:
        raise ValueError("frequency must be daily or weekly")

    local_now = now_utc.astimezone(zone)
    candidate = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= local_now:
        candidate += timedelta(days=7 if frequency == "weekly" else 1)
    return candidate.astimezone(UTC)
