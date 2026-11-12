from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.models import (
    AuditMode,
    CrawlScope,
    DeliveryAttempt,
    PageCoverage,
    PageTarget,
    RunStatus,
    Schedule,
)


class AuditCreateRequest(BaseModel):
    mode: AuditMode
    targets: list[PageTarget] = Field(min_length=1, max_length=5)
    rule_version: str | None = None
    scope: CrawlScope = Field(default_factory=CrawlScope)


class AuditCreateResponse(BaseModel):
    id: str
    mode: AuditMode
    targets: list[PageTarget]
    rule_version: str
    scope: CrawlScope
    created_at: datetime


class RunCreateResponse(BaseModel):
    run_id: str
    audit_definition_id: str
    status: RunStatus
    total_pages: int


class PageRunProgress(BaseModel):
    url: str
    locale: str
    status: str
    reason: str | None = None


class RunStatusResponse(BaseModel):
    run_id: str
    audit_definition_id: str
    status: RunStatus
    progress: int
    total_pages: int
    completed_pages: int
    failed_pages: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
    coverage: PageCoverage = Field(default_factory=PageCoverage)
    pages: list[PageRunProgress] = Field(default_factory=list)


class IssueResponse(BaseModel):
    id: str
    run_id: str
    severity: str
    status: str
    rule: str
    category: str
    page: str
    locale: str
    snippet: str
    problem: str
    correction: str
    proof: str
    locator: str
    evaluator: str
    confidence: float
    review_required: bool
    reasoning: str | None = None
    reminder: str | None = None
    capture_url: str | None = None
    issue_key: str | None = None


class ReportResponse(BaseModel):
    run: RunStatusResponse
    findings: list[IssueResponse]
    summary: dict[str, int]


class CrossPageValueResponse(BaseModel):
    locale: str
    url: str
    value: str | None = None


class CrossPageFieldResponse(BaseModel):
    field: str
    label: str
    category: Literal["invariant", "market_sensitive"]
    status: Literal["consistent", "actionable", "expected"]
    values: list[CrossPageValueResponse]


class ComparisonResponse(BaseModel):
    run_id: str
    previous_run_id: str | None = None
    statuses: dict[str, list[IssueResponse]] = Field(default_factory=dict)
    cross_page: list[CrossPageFieldResponse] = Field(default_factory=list)


class TraceEntry(BaseModel):
    """One dynamic rule-trace entry for a completed run."""

    rule: str
    zone: str
    outcome: str
    evaluator: str
    detail: str
    reasoning: str | None = None
    locale: str | None = None
    locales: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


ChecklistStatus = Literal[
    "pending", "pass", "issues", "error", "not_evaluated", "not_applicable"
]


class ChecklistCounts(BaseModel):
    total: int = 0
    checked: int = 0
    issues: int = 0
    not_evaluated: int = 0
    pending: int = 0
    not_applicable: int = 0


class ChecklistCheckpoint(BaseModel):
    id: str
    label: str
    status: ChecklistStatus
    issues: int = 0
    pages: int = 0


class ChecklistGroup(BaseModel):
    title: str
    counts: ChecklistCounts
    checkpoints: list[ChecklistCheckpoint] = Field(default_factory=list)


class ChecklistResponse(BaseModel):
    run_id: str
    rule_version: str
    mode: AuditMode
    run_status: RunStatus
    counts: ChecklistCounts
    groups: list[ChecklistGroup] = Field(default_factory=list)


class ScheduleCreateRequest(BaseModel):
    audit_definition_id: str
    frequency: Literal["daily", "weekly"]
    local_time: str
    timezone: str
    recipients: list[str] = Field(min_length=1, max_length=50)


class ScheduleUpdateRequest(BaseModel):
    enabled: bool | None = None
    frequency: Literal["daily", "weekly"] | None = None
    local_time: str | None = None
    timezone: str | None = None
    recipients: list[str] | None = Field(default=None, min_length=1, max_length=50)


class ScheduleResponse(Schedule):
    """API response for one schedule."""


class DeliveryAttemptResponse(DeliveryAttempt):
    """API response for one delivery attempt."""


class PromptParseRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


class PromptTargetResponse(BaseModel):
    url: str
    locale: str


class PromptParseResponse(BaseModel):
    targets: list[PromptTargetResponse]
    problems: list[str]


class PromptRunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    mode: AuditMode
    scope: CrawlScope = Field(default_factory=CrawlScope)


class PromptRunResponse(BaseModel):
    audit_id: str
    run_id: str
    mode: AuditMode
    targets: list[PromptTargetResponse]
