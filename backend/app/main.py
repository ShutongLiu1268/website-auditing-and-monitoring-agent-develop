"""FastAPI application entry point and audit API."""

import asyncio
import hashlib
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient

from app.acquisition.capture import sanitize_capture_html, with_base_url
from app.acquisition.playwright_fetcher import PageFetcher
from app.acquisition.url_policy import URLPolicy
from app.agent.evaluator import DSXEvaluator
from app.agent.llm_provider import DSXClientProvider
from app.api.checklist import build_checklist
from app.api.mappers import (
    to_cross_page_responses,
    to_issue_responses,
    to_observation_response,
    to_trace_entries,
)
from app.api.schemas import (
    AuditCreateRequest,
    AuditCreateResponse,
    ChecklistResponse,
    ComparisonResponse,
    DeliveryAttemptResponse,
    IssueResponse,
    PageRunProgress,
    PromptParseRequest,
    PromptParseResponse,
    PromptRunRequest,
    PromptRunResponse,
    PromptTargetResponse,
    ReportResponse,
    RunCreateResponse,
    RunStatusResponse,
    ScheduleCreateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
    TraceEntry,
)
from app.audits.activity import RunActivityLog
from app.audits.live_page_service import LivePageAuditService
from app.audits.orchestrator import AuditOrchestrator
from app.comparison.cross_page import compare_pages
from app.comparison.transitions import load_run_transitions
from app.config import settings
from app.conversation.parser import extract_prompt_targets
from app.conversation.service import ConversationService
from app.delivery.service import DeliveryService
from app.delivery.smtp import SMTPTransport
from app.diagnostics.models import DiagnosticResult, DiagnosticSummary
from app.diagnostics.service import DiagnosticService
from app.domain.models import AuditDefinition, RunStatus
from app.errors import AppError, ErrorDetail, ErrorEnvelope
from app.persistence.repositories import (
    AuditDefinitionRepository,
    AuditRunRepository,
    CheckResultRepository,
    DeliveryAttemptRepository,
    IssueIdentityRepository,
    IssueObservationRepository,
    PageCaptureRepository,
    PageSnapshotRepository,
    RulePassageRepository,
    ScheduleRepository,
)
from app.reporting.generator import ReportGenerator
from app.rule_knowledge.ingestion import RuleIngestor
from app.rule_knowledge.selection import RuleSelector
from app.schedules.service import ScheduleService


class HealthDatabase(TypedDict):
    configured: bool
    reachable: bool


class HealthRules(TypedDict):
    available: bool
    version: str | None


class HealthLlm(TypedDict):
    configured: bool
    model: str


class HealthSmtp(TypedDict):
    configured: bool


class HealthResponse(TypedDict):
    status: str
    version: str
    database: HealthDatabase
    rules: HealthRules
    llm: HealthLlm
    smtp: HealthSmtp
    demo_mode: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Mongo repositories, rule knowledge, and in-process jobs."""
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
    app.state.mongo_client = mongo_client
    app.state.mongo_db = mongo_client[settings.MONGODB_DB_NAME]
    run_tasks: set[asyncio.Task[None]] = set()
    app.state.run_tasks = run_tasks

    app.state.audit_def_repo = AuditDefinitionRepository(app.state.mongo_db)
    app.state.run_repo = AuditRunRepository(app.state.mongo_db)
    app.state.snapshot_repo = PageSnapshotRepository(app.state.mongo_db)
    app.state.capture_repo = PageCaptureRepository(app.state.mongo_db)
    app.state.rule_passage_repo = RulePassageRepository(app.state.mongo_db)
    app.state.result_repo = CheckResultRepository(app.state.mongo_db)
    app.state.issue_identity_repo = IssueIdentityRepository(app.state.mongo_db)
    app.state.issue_observation_repo = IssueObservationRepository(app.state.mongo_db)
    app.state.schedule_repo = ScheduleRepository(app.state.mongo_db)
    app.state.delivery_repo = DeliveryAttemptRepository(app.state.mongo_db)
    app.state.dsx_provider = DSXClientProvider(settings)
    app.state.dsx_evaluator = DSXEvaluator(
        app.state.dsx_provider.client,
        model=settings.DSX_MODEL,
        use_json_mode=settings.DSX_JSON_MODE,
        timeout_seconds=settings.DSX_TIMEOUT_SECONDS,
    )
    app.state.conversation_service = ConversationService(
        app.state.audit_def_repo,
        app.state.rule_passage_repo,
    )
    app.state.report_generator = ReportGenerator()
    app.state.schedule_service = ScheduleService(app.state.schedule_repo)
    app.state.smtp_transport = SMTPTransport(settings)
    app.state.delivery_service = DeliveryService(
        app.state.delivery_repo,
        app.state.smtp_transport,
        app.state.report_generator,
        settings,
    )
    app.state.diagnostics = DiagnosticService(settings, app.state.dsx_provider)
    app.state.activity = RunActivityLog()
    rule_path = Path(__file__).parent / "rule_knowledge" / "npl-pdp-audit-guide.md"
    catalog = RuleIngestor(rule_path).ingest()
    await app.state.rule_passage_repo.replace_version(catalog.version, catalog.passages)
    app.state.rule_selector = RuleSelector(catalog.passages, catalog.groups)
    print(f"Ingested {len(catalog.passages)} checkpoints (version: {catalog.version})")
    app.state.live_page_service = LivePageAuditService(
        PageFetcher(),
        app.state.rule_selector,
        app.state.dsx_evaluator,
        app.state.snapshot_repo,
        app.state.result_repo,
        identity_repo=app.state.issue_identity_repo,
        observation_repo=app.state.issue_observation_repo,
        capture_repo=app.state.capture_repo,
        activity=app.state.activity,
    )
    app.state.orchestrator = AuditOrchestrator(
        app.state.audit_def_repo,
        app.state.run_repo,
        app.state.live_page_service,
        activity=app.state.activity,
    )
    if interrupted := await app.state.run_repo.fail_stale(settings.RUN_STALE_SECONDS):
        print(f"Marked {interrupted} interrupted audit runs as failed")
    if settings.SCHEDULER_ENABLED:
        app.state.run_tasks.add(
            asyncio.create_task(
                app.state.schedule_service.run_forever(_execute_due_schedule)
            )
        )

    yield

    for task in app.state.run_tasks:
        task.cancel()
    if app.state.run_tasks:
        await asyncio.gather(*app.state.run_tasks, return_exceptions=True)
    await app.state.dsx_provider.aclose()
    mongo_client.close()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _execute_due_schedule(schedule):
    """Run and deliver one claimed schedule occurrence."""
    run = await app.state.orchestrator.execute_audit(schedule.audit_definition_id)
    report = await get_run_report(run.id)
    await app.state.delivery_service.deliver(schedule, run, report)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle application errors with standard envelope."""
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=getattr(request.state, "request_id", None),
            retryable=exc.retryable,
        )
    )
    return JSONResponse(status_code=400, content=envelope.model_dump())


@app.get("/health")
async def health(request: Request) -> HealthResponse:
    provider = getattr(request.app.state, "dsx_provider", None)
    mongo_db = getattr(request.app.state, "mongo_db", None)
    database_reachable = False
    if mongo_db is not None:
        try:
            await mongo_db.command("ping")
            database_reachable = True
        except Exception:
            database_reachable = False
    rule_path = Path(__file__).parent / "rule_knowledge" / "npl-pdp-audit-guide.md"
    rule_repo = getattr(request.app.state, "rule_passage_repo", None)
    rule_version = await rule_repo.get_latest_version() if rule_repo else None
    return {
        "status": "ok" if database_reachable else "degraded",
        "version": settings.APP_VERSION,
        "database": {
            "configured": bool(settings.MONGODB_URI),
            "reachable": database_reachable,
        },
        "rules": {"available": rule_path.exists(), "version": rule_version},
        "llm": {
            "configured": bool(provider and provider.is_configured),
            "model": settings.DSX_MODEL,
        },
        "smtp": {"configured": bool(settings.SMTP_HOST and settings.SMTP_FROM)},
        "demo_mode": settings.DEMO_MODE,
    }


@app.get("/health/live")
async def health_live():
    """Return process liveness without external dependency calls."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/health/ready")
async def health_ready(request: Request):
    """Return dependency readiness without active DSX or SMTP probes."""
    return await health(request)


@app.get("/api/diagnostics/mongo", response_model=DiagnosticResult)
async def diagnostics_mongo():
    """Test MongoDB connectivity."""
    started = time.perf_counter()
    try:
        await app.state.mongo_db.command("ping")
        return DiagnosticResult(
            component="mongo",
            status="ok",
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )
    except Exception as exc:
        return DiagnosticResult(
            component="mongo",
            status="failed",
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            error_code=type(exc).__name__,
        )


@app.get("/api/diagnostics/dsx", response_model=DiagnosticResult)
async def diagnostics_dsx():
    """Test DSX connectivity with one minimal request."""
    return await app.state.diagnostics.probe_dsx()


@app.get("/api/diagnostics/smtp", response_model=DiagnosticResult)
async def diagnostics_smtp():
    """Test SMTP connectivity without sending email."""
    return await app.state.diagnostics.probe_smtp()


@app.get("/api/diagnostics", response_model=DiagnosticSummary)
async def diagnostics(request: Request):
    """Return a simple secret-free dependency summary."""
    readiness = await health(request)
    return app.state.diagnostics.summary(
        database_reachable=readiness["database"]["reachable"],
        rule_available=readiness["rules"]["available"],
        rule_version=readiness["rules"]["version"],
    )


@app.get("/api/framework")
async def get_framework():
    version = await app.state.rule_passage_repo.get_latest_version()
    if not version:
        return {"version": None, "status": "not_ingested", "passage_count": 0}
    passages = await app.state.rule_passage_repo.get_by_version(version)
    return {"version": version, "status": "ingested", "passage_count": len(passages)}


@app.post("/api/chat")
async def chat(request: Request):
    """Parse and validate a chat command."""
    payload = await request.json()
    message = payload.get("message", "")
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=422, detail="message is required")
    response = await app.state.conversation_service.handle(message)
    return response.model_dump(mode="json")


@app.post("/api/audits", response_model=AuditCreateResponse)
async def create_audit(payload: AuditCreateRequest):
    """Persist an audit definition after URL policy validation."""
    urls = [str(target.url) for target in payload.targets]
    URLPolicy.validate_urls(urls)
    rule_version = (
        payload.rule_version or await app.state.rule_passage_repo.get_latest_version()
    )
    rule_version = rule_version or "unversioned"
    comparison_key = hashlib.sha256(
        "|".join(
            [
                payload.mode.value,
                rule_version,
                "identity-v2",
                str(payload.scope.model_dump()),
                *[f"{target.url}:{target.locale}" for target in payload.targets],
            ]
        ).encode()
    ).hexdigest()
    definition = AuditDefinition(
        id=str(uuid.uuid4()),
        mode=payload.mode,
        targets=payload.targets,
        rule_version=rule_version,
        scope=payload.scope,
        comparison_key=comparison_key,
    )
    await app.state.audit_def_repo.create(definition)
    return AuditCreateResponse.model_validate(definition.model_dump())


async def _execute_and_mark_failed(run_id: str):
    try:
        await app.state.orchestrator.execute_run(run_id)
    except Exception:
        await app.state.run_repo.update_status(
            run_id,
            RunStatus.FAILED.value,
            completed_at=datetime.now(UTC),
        )


def _queue_run(run_id: str) -> None:
    task = asyncio.create_task(_execute_and_mark_failed(run_id))
    app.state.run_tasks.add(task)
    task.add_done_callback(app.state.run_tasks.discard)


async def _get_run_status_response(run_id: str) -> RunStatusResponse:
    run = await app.state.run_repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    definition = await app.state.audit_def_repo.get(run.audit_definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Audit definition not found")
    progress = run.progress_percent()
    page_statuses = [
        PageRunProgress(
            url=str(target.url),
            locale=target.locale,
            status=(
                run.page_statuses[index] if index < len(run.page_statuses) else "queued"
            ),
        )
        for index, target in enumerate(definition.targets)
    ]
    return RunStatusResponse(
        run_id=run.id,
        audit_definition_id=run.audit_definition_id,
        status=run.status,
        progress=progress,
        total_pages=run.total_pages,
        completed_pages=run.completed_pages,
        failed_pages=run.failed_pages,
        started_at=run.started_at,
        completed_at=run.completed_at,
        warnings=run.warnings,
        coverage=run.coverage,
        pages=page_statuses,
    )


@app.post("/api/audits/{audit_id}/runs", response_model=RunCreateResponse)
async def create_run(audit_id: str):
    """Create and queue a manual audit run."""
    definition = await app.state.audit_def_repo.get(audit_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Audit definition not found")
    run = await app.state.orchestrator.create_run(audit_id)
    _queue_run(run.id)
    return RunCreateResponse(
        run_id=run.id,
        audit_definition_id=run.audit_definition_id,
        status=run.status,
        total_pages=run.total_pages,
    )


@app.post("/api/prompt/parse", response_model=PromptParseResponse)
async def parse_prompt(payload: PromptParseRequest):
    """Show which PDP URLs and locales the agent reads from a prompt."""
    extracted = extract_prompt_targets(payload.prompt)
    return PromptParseResponse(
        targets=[
            PromptTargetResponse(url=str(target.url), locale=target.locale)
            for target in extracted.targets
        ],
        problems=extracted.problems,
    )


@app.post("/api/prompt/runs", response_model=PromptRunResponse)
async def create_prompt_run(payload: PromptRunRequest):
    """Create and queue an audit from the PDP URLs written in the prompt."""
    extracted = extract_prompt_targets(payload.prompt)
    if extracted.problems or not extracted.targets:
        raise HTTPException(
            status_code=422,
            detail=extracted.problems
            or "Add at least one HTTPS PDP URL to the prompt.",
        )
    if len(extracted.targets) > 5:
        raise HTTPException(
            status_code=422, detail="Audit up to five PDP URLs per run."
        )
    audit = await create_audit(
        AuditCreateRequest(
            mode=payload.mode, targets=extracted.targets, scope=payload.scope
        )
    )
    run = await create_run(audit.id)
    return PromptRunResponse(
        audit_id=audit.id,
        run_id=run.run_id,
        mode=payload.mode,
        targets=[
            PromptTargetResponse(url=str(target.url), locale=target.locale)
            for target in extracted.targets
        ],
    )


@app.get("/api/runs/{run_id}/events")
async def stream_run_events(run_id: str):
    """Stream the bot's activity for one run as server-sent events."""
    run = await app.state.run_repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    if run.status.value in {"completed", "partial", "failed", "cancelled"} and not (
        app.state.activity.knows(run_id)
    ):
        await app.state.activity.close(run_id)
    return StreamingResponse(
        app.state.activity.stream(run_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/api/runs/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str):
    return await _get_run_status_response(run_id)


@app.get("/api/runs/{run_id}/snapshots/{snapshot_id}/html", response_class=HTMLResponse)
async def get_snapshot_html(run_id: str, snapshot_id: str):
    """Return a sanitized captured DOM for an audited snapshot."""
    snapshot = await app.state.snapshot_repo.get(snapshot_id)
    if not snapshot or snapshot.run_id != run_id or not snapshot.html_capture_id:
        raise HTTPException(status_code=404, detail="Captured page not found")
    html = await app.state.capture_repo.get(snapshot.html_capture_id)
    return HTMLResponse(
        content=with_base_url(
            sanitize_capture_html(html.decode("utf-8", errors="replace")),
            snapshot.url,
        ),
        headers={
            "Content-Security-Policy": "default-src 'none'; img-src https: data:; style-src 'unsafe-inline' https:; font-src https: data:; media-src https:; frame-src https:; base-uri https:; form-action 'none'",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/api/runs/{run_id}/issues", response_model=list[IssueResponse])
async def get_run_issues(
    run_id: str,
    severity: str | None = Query(default=None),
    page: str | None = Query(default=None),
    locale: str | None = Query(default=None),
    category: str | None = None,
    status: str | None = None,
    rule: str | None = None,
):
    await _get_run_status_response(run_id)
    results = await app.state.result_repo.get_by_run(run_id)
    snapshots = {
        snapshot.id: snapshot
        for snapshot in await app.state.snapshot_repo.get_by_run(run_id)
    }
    transitions = await load_run_transitions(
        run_id,
        app.state.run_repo,
        app.state.snapshot_repo,
        app.state.issue_observation_repo,
        app.state.issue_identity_repo,
    )
    issues = to_issue_responses(results, snapshots, transitions.identity_statuses())
    return [
        issue
        for issue in issues
        if (severity is None or issue.severity == severity)
        and (page is None or issue.page == page)
        and (locale is None or issue.locale == locale)
        and (category is None or issue.category == category)
        and (status is None or issue.status == status)
        and (rule is None or issue.rule == rule)
    ]


@app.get("/api/runs/{run_id}/report", response_model=ReportResponse)
async def get_run_report(run_id: str):
    await _get_run_status_response(run_id)
    run_model = await app.state.run_repo.get(run_id)
    if not run_model:
        raise HTTPException(status_code=404, detail="Audit run not found")
    results = await app.state.result_repo.get_by_run(run_id)
    snapshots = {
        snapshot.id: snapshot
        for snapshot in await app.state.snapshot_repo.get_by_run(run_id)
    }
    return app.state.report_generator.build(run_model, results, snapshots)


@app.get("/api/runs/{run_id}/comparison", response_model=ComparisonResponse)
async def get_run_comparison(run_id: str):
    run = await app.state.run_repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    transitions = await load_run_transitions(
        run_id,
        app.state.run_repo,
        app.state.snapshot_repo,
        app.state.issue_observation_repo,
        app.state.issue_identity_repo,
    )
    statuses = {
        status.value: [
            to_observation_response(
                observation,
                transitions.snapshots.get(observation.page_snapshot_id),
                status.value,
                transitions.issue_keys.get((observation.run_id, observation.id)),
            )
            for observation in observations
        ]
        for status, observations in transitions.grouped.items()
    }
    current_pages = sorted(transitions.current_snapshots, key=lambda page: page.locale)
    return ComparisonResponse(
        run_id=run_id,
        previous_run_id=transitions.previous_run_id,
        statuses=statuses,
        cross_page=to_cross_page_responses(compare_pages(current_pages)),
    )


@app.get("/api/runs/{run_id}/trace", response_model=list[TraceEntry])
async def get_run_trace(run_id: str):
    """Return dynamic rule-evaluation trace for one run."""
    await _get_run_status_response(run_id)
    results = await app.state.result_repo.get_by_run(run_id)
    locales = {
        snapshot.id: snapshot.locale
        for snapshot in await app.state.snapshot_repo.get_by_run(run_id)
    }
    return to_trace_entries(results, locales)


@app.get("/api/runs/{run_id}/checklist", response_model=ChecklistResponse)
async def get_run_checklist(run_id: str):
    """Return the guide checklist for one run, filled from its results."""
    run = await app.state.run_repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    definition = await app.state.audit_def_repo.get(run.audit_definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Audit definition not found")
    return build_checklist(
        run.id,
        definition.rule_version,
        definition.mode,
        run.status,
        await app.state.rule_passage_repo.get_by_version(definition.rule_version),
        await app.state.result_repo.get_by_run(run_id),
    )


@app.post("/api/schedules", response_model=ScheduleResponse)
async def create_schedule(payload: ScheduleCreateRequest):
    """Create a recurring report schedule."""
    definition = await app.state.audit_def_repo.get(payload.audit_definition_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Audit definition not found")
    schedule = await app.state.schedule_service.create(
        definition,
        payload.frequency,
        payload.local_time,
        payload.timezone,
        payload.recipients,
    )
    return ScheduleResponse.model_validate(schedule.model_dump())


@app.get("/api/schedules", response_model=list[ScheduleResponse])
async def list_schedules():
    """List recurring schedules."""
    return [
        ScheduleResponse.model_validate(schedule.model_dump())
        for schedule in await app.state.schedule_service.list()
    ]


@app.patch("/api/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: str, payload: ScheduleUpdateRequest):
    """Pause, resume, or update a schedule."""
    schedule = await app.state.schedule_repo.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    updates = payload.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(schedule, key, value)
    if payload.enabled is False:
        schedule = await app.state.schedule_service.pause(schedule)
    elif payload.enabled is True:
        schedule = await app.state.schedule_service.resume(schedule)
    else:
        schedule.updated_at = datetime.now(UTC)
        schedule = await app.state.schedule_repo.update(schedule)
    return ScheduleResponse.model_validate(schedule.model_dump())


@app.delete("/api/schedules/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str):
    """Delete one schedule."""
    schedule = await app.state.schedule_repo.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await app.state.schedule_repo.delete(schedule_id)


@app.post("/api/deliveries/{attempt_id}/retry", response_model=DeliveryAttemptResponse)
async def retry_delivery(attempt_id: str):
    """Retry a failed delivery without creating another audit run."""
    attempt = await app.state.delivery_repo.get(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Delivery attempt not found")
    schedule = await app.state.schedule_repo.get(attempt.schedule_id)
    run = await app.state.run_repo.get(attempt.run_id)
    if not schedule or not run:
        raise HTTPException(status_code=404, detail="Schedule or run not found")
    report = await get_run_report(run.id)
    retried = await app.state.delivery_service.retry(schedule, run, report)
    return DeliveryAttemptResponse.model_validate(retried.model_dump())


@app.get(
    "/api/schedules/{schedule_id}/deliveries",
    response_model=list[DeliveryAttemptResponse],
)
async def list_schedule_deliveries(schedule_id: str):
    """List delivery attempts for a schedule."""
    schedule = await app.state.schedule_repo.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return [
        DeliveryAttemptResponse.model_validate(attempt.model_dump())
        for attempt in await app.state.delivery_repo.list_by_schedule(schedule_id)
    ]


@app.post(
    "/api/schedules/{schedule_id}/run-now", response_model=DeliveryAttemptResponse
)
async def run_schedule_now(schedule_id: str):
    """Execute one schedule occurrence immediately for demos and operators."""
    schedule = await app.state.schedule_repo.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    run = await app.state.orchestrator.execute_audit(schedule.audit_definition_id)
    report = await get_run_report(run.id)
    attempt = await app.state.delivery_service.deliver(schedule, run, report)
    schedule.last_run_id = run.id
    schedule.updated_at = datetime.now(UTC)
    await app.state.schedule_repo.update(schedule)
    return DeliveryAttemptResponse.model_validate(attempt.model_dump())
