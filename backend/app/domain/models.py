"""
Domain models for NPL PDP Audit.

All models use Pydantic v2 for validation and serialization.
"""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class AuditMode(str, Enum):
    SPRINT_LAUNCH = "sprint_launch"
    R2 = "r2"
    R3 = "r3"


class RuleEvaluatorType(str, Enum):
    CODE = "code"
    LLM = "llm"
    HYBRID = "hybrid"


class CheckOutcome(str, Enum):
    PASS = "pass"
    ISSUE = "issue"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUATED = "not_evaluated"
    ERROR = "error"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComparisonStatus(str, Enum):
    NEW = "new"
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    NOT_RECHECKED = "not_rechecked"
    CHANGED_PAGE = "changed_page"


class CrawlScope(BaseModel):
    include_paths: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)
    page_limit: int = Field(default=25, ge=1, le=500)
    max_depth: int = Field(default=0, ge=0, le=10)


class CrawlPage(BaseModel):
    url: str
    canonical_url: str
    depth: int
    status: str
    reason: str | None = None
    discovered_from: str | None = None


class PageCoverage(BaseModel):
    scanned: int = 0
    skipped: int = 0
    inaccessible: int = 0
    duplicate: int = 0
    timeout: int = 0


class PageTarget(BaseModel):
    url: HttpUrl
    locale: str = Field(..., description="BCP 47 locale tag, e.g., en-US, fr-CA")
    country: str | None = Field(None, description="ISO 3166-1 alpha-2 country code")


class AuditDefinition(BaseModel):
    id: str
    mode: AuditMode
    targets: list[PageTarget]
    rule_version: str
    scope: CrawlScope = Field(default_factory=CrawlScope)
    comparison_key: str = Field(default="", description="Key for run comparability")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditRun(BaseModel):
    id: str
    audit_definition_id: str
    status: RunStatus
    trigger_type: str = Field(default="manual")
    started_at: datetime | None = None
    completed_at: datetime | None = None
    previous_run_id: str | None = None
    total_pages: int = 0
    completed_pages: int = 0
    failed_pages: int = 0
    warnings: list[str] = Field(default_factory=list)
    coverage: PageCoverage = Field(default_factory=PageCoverage)
    coverage_pages: list[CrawlPage] = Field(default_factory=list)
    previous_comparable_run_id: str | None = None
    comparison_key: str = Field(default="", description="Key for run comparability")
    active_page_progress: float = 0.0
    page_statuses: list[str] = Field(default_factory=list)
    heartbeat_at: datetime | None = None

    def progress_percent(self) -> int:
        if self.total_pages == 0:
            return 0
        finished = (
            self.completed_pages
            + self.failed_pages
            + self.coverage.skipped
            + self.coverage.duplicate
        )
        return min(
            100, round((finished + self.active_page_progress) / self.total_pages * 100)
        )


class PageSnapshot(BaseModel):
    id: str
    run_id: str
    url: str
    locale: str
    content_hash: str
    extraction_version: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[str] = Field(default_factory=list)
    html_capture_id: str | None = None
    html_capture_size: int | None = None
    html_capture_hash: str | None = None
    product_fields: dict[str, str] = Field(default_factory=dict)


class RulePassage(BaseModel):
    id: str
    version: str
    heading_path: list[str]
    source_range: tuple[int, int]
    original_text: str
    modes: list[AuditMode]
    markets: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    zones: list[str] = Field(default_factory=list)
    severity: Severity | None = None
    evaluator_type: RuleEvaluatorType = RuleEvaluatorType.LLM
    check: str | None = None
    review: str = "never"
    reminder: str | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def plus(self, other: "TokenUsage | None") -> "TokenUsage":
        if other is None:
            return self
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class CheckResult(BaseModel):
    id: str
    run_id: str
    page_snapshot_id: str
    rule_passage_id: str
    zone: str
    outcome: CheckOutcome
    problem: str | None = None
    suggested_correction: str | None = None
    proof_text: str | None = None
    severity: Severity | None = None
    rule_quote: str | None = None
    evidence_quote: str | None = None
    dom_locator: str | None = None
    confidence: float = 0.0
    review_required: bool = False
    reminder: str | None = None
    reasoning: str | None = None
    error: str | None = None
    model: str | None = None
    token_usage: TokenUsage | None = None
    occurrence: int = 0


class IssueIdentity(BaseModel):
    id: str
    url: str
    locale: str
    rule_passage_id: str
    zone: str
    locator: str
    normalized_subject: str


class IssueObservation(BaseModel):
    id: str
    issue_identity_id: str
    run_id: str
    page_snapshot_id: str
    zone: str = ""
    rule_quote: str
    evidence_quote: str
    dom_locator: str
    problem: str
    suggested_correction: str
    proof_text: str
    severity: Severity
    confidence: float
    review_required: bool
    reasoning: str | None = None
    reminder: str | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Schedule(BaseModel):
    id: str
    audit_definition_id: str
    enabled: bool = True
    frequency: str
    local_time: str
    timezone: str
    recipients: list[str]
    next_run_at_utc: datetime
    lease_until_utc: datetime | None = None
    last_run_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DeliveryAttempt(BaseModel):
    id: str
    schedule_id: str
    run_id: str
    recipients: list[str]
    status: str
    provider_message_id: str | None = None
    error_code: str | None = None
    attempted_at: datetime | None = None
    completed_at: datetime | None = None
