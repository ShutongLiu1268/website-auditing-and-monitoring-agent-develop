"""Integration coverage for the one-page live orchestration path."""

import pytest

from app.acquisition.playwright_fetcher import FetchedPage
from app.audits.live_page_service import LivePageAuditResult
from app.audits.orchestrator import AuditOrchestrator
from app.domain.models import (
    AuditDefinition,
    AuditMode,
    AuditRun,
    CrawlScope,
    PageSnapshot,
    RunStatus,
)
from app.facts.models import PageFacts


class MemoryAuditDefinitionRepository:
    """In-memory audit definition repository."""

    def __init__(self, definition: AuditDefinition) -> None:
        self.definition = definition

    async def get(self, audit_definition_id: str) -> AuditDefinition | None:
        return self.definition if self.definition.id == audit_definition_id else None


class MemoryRunRepository:
    """In-memory run repository."""

    def __init__(self) -> None:
        self.items: dict[str, AuditRun] = {}

    async def create(self, run: AuditRun) -> AuditRun:
        self.items[run.id] = run
        return run

    async def get(self, run_id: str) -> AuditRun | None:
        return self.items.get(run_id)

    async def update_status(
        self,
        run_id: str,
        status: str,
        completed_at=None,
        started_at=None,
        completed_pages=None,
        failed_pages=None,
        warnings=None,
        coverage=None,
        coverage_pages=None,
        active_page_progress=None,
        page_statuses=None,
    ) -> None:
        run = self.items[run_id]
        run.status = RunStatus(status)
        if completed_at is not None:
            run.completed_at = completed_at
        if started_at is not None:
            run.started_at = started_at
        if completed_pages is not None:
            run.completed_pages = completed_pages
        if failed_pages is not None:
            run.failed_pages = failed_pages
        if warnings is not None:
            run.warnings = warnings
        if active_page_progress is not None:
            run.active_page_progress = active_page_progress
        if page_statuses is not None:
            run.page_statuses = page_statuses


@pytest.mark.asyncio
async def test_live_orchestration_completes_one_target(mocker):
    """Test one target passes through live service and completes."""
    definition = AuditDefinition(
        id="audit-1",
        mode=AuditMode.R3,
        targets=[{"url": "https://example.test/pdp", "locale": "en-US"}],
        rule_version="v1",
    )
    audit_repo = MemoryAuditDefinitionRepository(definition)
    run_repo = MemoryRunRepository()
    live_service = mocker.MagicMock()
    live_service.fetcher.fetch_page = mocker.AsyncMock(
        return_value=FetchedPage(
            url="https://example.test/pdp",
            html="<html></html>",
            zones=[],
            content_hash="hash-1",
            warnings=[],
            facts=PageFacts(),
        )
    )
    live_service.audit_fetched_page = mocker.AsyncMock(
        return_value=LivePageAuditResult(
            snapshot=PageSnapshot(
                id="snapshot-1",
                run_id="run-1",
                url="https://example.test/pdp",
                locale="en-US",
                content_hash="hash-1",
                extraction_version="live-0.2.0",
            ),
            results=[],
            warnings=[],
        )
    )
    live_service.close = mocker.AsyncMock()
    orchestrator = AuditOrchestrator(audit_repo, run_repo, live_service)

    run = await orchestrator.execute_audit(definition.id)

    assert run.status == RunStatus.COMPLETED
    assert run.completed_pages == 1
    assert run.failed_pages == 0
    live_service.audit_fetched_page.assert_awaited_once()
    live_service.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_live_orchestration_discloses_extra_targets(mocker):
    """Test extra targets are disclosed and not reported as scanned."""
    definition = AuditDefinition(
        id="audit-2",
        mode=AuditMode.R3,
        targets=[
            {"url": "https://example.test/one", "locale": "en-US"},
            {"url": "https://example.test/two", "locale": "en-US"},
        ],
        rule_version="v1",
        scope=CrawlScope(page_limit=1),
    )
    live_service = mocker.MagicMock()
    live_service.fetcher.fetch_page = mocker.AsyncMock(
        side_effect=[
            FetchedPage(
                url="https://example.test/one",
                html="<html></html>",
                zones=[],
                content_hash="hash-2",
                warnings=[],
                facts=PageFacts(),
            )
        ]
    )
    live_service.audit_fetched_page = mocker.AsyncMock(
        return_value=LivePageAuditResult(
            snapshot=PageSnapshot(
                id="snapshot-2",
                run_id="run-2",
                url="https://example.test/one",
                locale="en-US",
                content_hash="hash-2",
                extraction_version="live-0.2.0",
            ),
            results=[],
            warnings=[],
        )
    )
    live_service.close = mocker.AsyncMock()
    orchestrator = AuditOrchestrator(
        MemoryAuditDefinitionRepository(definition),
        MemoryRunRepository(),
        live_service,
    )

    run = await orchestrator.execute_audit(definition.id)

    assert run.status == RunStatus.PARTIAL
    assert run.completed_pages == 1
    assert run.warnings == ["crawl_skipped_pages:1"]
    live_service.audit_fetched_page.assert_awaited_once()
