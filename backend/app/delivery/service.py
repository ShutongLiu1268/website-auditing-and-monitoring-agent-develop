"""Report delivery and retry service."""

from datetime import UTC, datetime

from app.config import Settings
from app.delivery.smtp import SMTPTransport
from app.domain.models import DeliveryAttempt, Schedule
from app.persistence.repositories import DeliveryAttemptRepository
from app.reporting.generator import ReportGenerator


class DeliveryService:
    """Deliver generated reports and persist attempt status."""

    def __init__(
        self,
        repository: DeliveryAttemptRepository,
        transport: SMTPTransport,
        report_generator: ReportGenerator,
        config: Settings,
    ) -> None:
        self._repository = repository
        self._transport = transport
        self._report_generator = report_generator
        self._config = config

    async def deliver(self, schedule: Schedule, run, report) -> DeliveryAttempt:
        """Send one report and persist success/failure."""
        attempt = DeliveryAttempt(
            id=f"delivery-{schedule.id}-{run.id}",
            schedule_id=schedule.id,
            run_id=run.id,
            recipients=schedule.recipients,
            status="queued",
        )
        await self._repository.create(attempt)
        attempt.attempted_at = datetime.now(UTC)
        try:
            attempt.provider_message_id = await self._transport.send(
                schedule.recipients,
                f"{self._config.REPORT_BRAND_NAME} report",
                self._report_generator.render_html(report),
            )
            attempt.status = "sent"
        except Exception as exc:
            attempt.status = "failed"
            attempt.error_code = type(exc).__name__
        attempt.completed_at = datetime.now(UTC)
        return await self._repository.update(attempt)

    async def retry(self, schedule: Schedule, run, report) -> DeliveryAttempt:
        """Retry delivery using the same report/run without creating a new audit."""
        return await self.deliver(schedule, run, report)
