"""Audit orchestrator: coordinates live audit runs."""

import asyncio
import uuid
from datetime import UTC, datetime

from app.acquisition.crawler import CrawledPage, ScopedCrawler
from app.audits.activity import RunActivityLog
from app.audits.live_page_service import LivePageAuditService
from app.config import settings
from app.domain.models import (
    AuditMode,
    AuditRun,
    CheckOutcome,
    CrawlScope,
    PageTarget,
    RunStatus,
)
from app.persistence.repositories import AuditDefinitionRepository, AuditRunRepository

_MODE_LABELS = {
    AuditMode.SPRINT_LAUNCH: "Sprint/Launch",
    AuditMode.R2: "R2",
    AuditMode.R3: "R3",
}


class AuditOrchestrator:
    """Orchestrate live audit runs."""

    def __init__(
        self,
        audit_def_repo: AuditDefinitionRepository,
        run_repo: AuditRunRepository,
        live_page_service: LivePageAuditService,
        activity: RunActivityLog | None = None,
    ) -> None:
        self.audit_def_repo = audit_def_repo
        self.run_repo = run_repo
        self.live_page_service = live_page_service
        self.activity = activity or RunActivityLog()

    async def create_run(self, audit_definition_id: str) -> AuditRun:
        """Create a queued run for an audit definition."""
        audit_definition = await self.audit_def_repo.get(audit_definition_id)
        if not audit_definition:
            raise ValueError(f"Audit definition not found: {audit_definition_id}")

        run = AuditRun(
            id=str(uuid.uuid4()),
            audit_definition_id=audit_definition_id,
            status=RunStatus.QUEUED,
            total_pages=len(audit_definition.targets),
            comparison_key=audit_definition.comparison_key,
        )
        await self.run_repo.create(run)
        return run

    async def execute_audit(self, audit_definition_id: str) -> AuditRun:
        """Create and execute a run synchronously for callers that need it."""
        run = await self.create_run(audit_definition_id)
        return await self.execute_run(run.id)

    async def execute_run(self, run_id: str) -> AuditRun:
        """Execute an existing queued run and persist progress/results."""
        run = await self.run_repo.get(run_id)
        if not run:
            raise ValueError(f"Audit run not found: {run_id}")

        audit_definition = await self.audit_def_repo.get(run.audit_definition_id)
        if not audit_definition:
            raise ValueError(f"Audit definition not found: {run.audit_definition_id}")

        started_at = datetime.now(UTC)
        run.status = RunStatus.RUNNING
        run.started_at = started_at
        heartbeat = asyncio.create_task(self._heartbeat(run.id))
        try:
            await self._persist_progress(run, started_at=started_at)
            await self.activity.record(
                run.id,
                "run",
                f"Auditing {len(audit_definition.targets)} PDP URLs against "
                f"{_MODE_LABELS[audit_definition.mode]}",
            )
            await self._execute_live_run(
                run,
                audit_definition.targets,
                audit_definition.scope,
                audit_definition.mode,
            )

            run.status = (
                RunStatus.PARTIAL
                if run.failed_pages > 0 or run.warnings
                else RunStatus.COMPLETED
            )
            run.completed_at = datetime.now(UTC)
            await self._persist_progress(run, completed_at=run.completed_at)
            await self.activity.record(
                run.id,
                "complete",
                f"Run {run.status.value}: {run.completed_pages} of "
                f"{run.total_pages} pages audited",
            )
        finally:
            heartbeat.cancel()
            await self.activity.close(run.id)
        return run

    async def _heartbeat(self, run_id: str) -> None:
        """Keep the run's heartbeat fresh while it executes."""
        while True:
            await self.run_repo.heartbeat(run_id)
            await asyncio.sleep(settings.RUN_HEARTBEAT_SECONDS)

    async def _execute_live_run(
        self,
        run: AuditRun,
        targets: list[PageTarget],
        scope: CrawlScope,
        mode: AuditMode,
    ) -> None:
        """Crawl pages and start each audit as soon as its fetch completes."""
        if not targets:
            run.warnings.append("live_mode_no_targets")
            return

        await self.activity.record(run.id, "crawl", "Crawling in-scope pages")
        run.page_statuses = ["queued"] * len(targets)
        index_by_url = {str(target.url): index for index, target in enumerate(targets)}
        active: dict[str, float] = {}
        audits: list[asyncio.Task[None]] = []

        async def on_fetched(crawled_page: CrawledPage) -> None:
            locale = crawled_page.target.locale
            await self.activity.record(
                run.id,
                "render",
                f"Rendered {locale} page",
                page=locale,
            )
            index = index_by_url.get(str(crawled_page.target.url))
            audits.append(
                asyncio.create_task(
                    self._audit_page(run, crawled_page, mode, index, active)
                )
            )

        probe_links = self.live_page_service.needs_link_probe(
            mode, {target.locale for target in targets}
        )
        crawler = ScopedCrawler(
            self.live_page_service.fetcher,
            max_concurrent=settings.CRAWL_MAX_CONCURRENT,
            on_fetched=on_fetched,
            probe_links=probe_links,
        )
        try:
            crawl_result = await crawler.crawl(targets, scope)
            run.coverage_pages = crawl_result.coverage_pages
            run.total_pages = len(crawl_result.coverage_pages)
            run.coverage.scanned = sum(
                record.status == "scanned" for record in crawl_result.coverage_pages
            )
            run.coverage.skipped = sum(
                record.status == "skipped" for record in crawl_result.coverage_pages
            )
            run.coverage.duplicate = sum(
                record.status == "duplicate" for record in crawl_result.coverage_pages
            )
            run.coverage.inaccessible = sum(
                record.status == "inaccessible"
                for record in crawl_result.coverage_pages
            )
            run.coverage.timeout = sum(
                record.status == "timeout" for record in crawl_result.coverage_pages
            )
            run.failed_pages += run.coverage.inaccessible + run.coverage.timeout
            for record in crawl_result.coverage_pages:
                index = index_by_url.get(record.url)
                if record.status in {"inaccessible", "timeout"}:
                    self._set_page_status(run, index, "failed")
                elif record.status in {"skipped", "duplicate"}:
                    self._set_page_status(run, index, "not_evaluated")
            if run.coverage.skipped:
                run.warnings.append(f"crawl_skipped_pages:{run.coverage.skipped}")
            if run.coverage.inaccessible:
                run.warnings.append(
                    f"crawl_inaccessible_pages:{run.coverage.inaccessible}"
                )
            if run.coverage.timeout:
                run.warnings.append(f"crawl_timeout_pages:{run.coverage.timeout}")
            await self._persist_progress(run)
            await asyncio.gather(*audits)
        finally:
            for audit in audits:
                audit.cancel()
            await self.live_page_service.close()
            await self._persist_progress(run)

    async def _audit_page(
        self,
        run: AuditRun,
        crawled_page: CrawledPage,
        mode: AuditMode,
        index: int | None,
        active: dict[str, float],
    ) -> None:
        """Audit one fetched page; a failure is recorded for this page only."""
        target = crawled_page.target
        url = str(target.url)

        async def report_check(done: int, total: int) -> None:
            active[url] = done / total if total else 0.0
            run.active_page_progress = sum(active.values())
            await self._persist_progress(run)

        active[url] = 0.0
        self._set_page_status(run, index, "auditing")
        await self._persist_progress(run)
        try:
            result = await self.live_page_service.audit_fetched_page(
                run,
                target,
                mode,
                crawled_page.fetched,
                on_check=report_check,
            )
        except Exception as exc:
            run.failed_pages += 1
            run.warnings.append(f"live_page_failed:{type(exc).__name__}")
            self._set_page_status(run, index, "failed")
        else:
            run.completed_pages += 1
            run.warnings.extend(result.warnings)
            self._set_page_status(run, index, "scanned")
            issues = sum(
                check.outcome == CheckOutcome.ISSUE for check in result.results
            )
            await self.activity.record(
                run.id,
                "evaluate",
                f"Checked {_MODE_LABELS[mode]} checkpoints for {target.locale}: {issues} issues",
                page=target.locale,
            )
        active.pop(url, None)
        run.active_page_progress = sum(active.values())
        await self._persist_progress(run)

    @staticmethod
    def _set_page_status(run: AuditRun, index: int | None, status: str) -> None:
        if index is not None and index < len(run.page_statuses):
            run.page_statuses[index] = status

    async def _persist_progress(
        self,
        run: AuditRun,
        *,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Persist current run lifecycle and warning fields."""
        await self.run_repo.update_status(
            run.id,
            run.status.value,
            completed_at=completed_at,
            started_at=started_at,
            completed_pages=run.completed_pages,
            failed_pages=run.failed_pages,
            warnings=run.warnings,
            coverage=run.coverage,
            coverage_pages=run.coverage_pages,
            active_page_progress=run.active_page_progress,
            page_statuses=run.page_statuses,
        )
