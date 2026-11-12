"""Diagnostic API contracts."""

from pydantic import BaseModel, Field


class DiagnosticResult(BaseModel):
    """Result of one dependency diagnostic."""

    component: str
    status: str
    latency_ms: float | None = None
    error_code: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class DiagnosticSummary(BaseModel):
    """Read-only dependency configuration summary."""

    mongo: dict[str, object]
    rules: dict[str, object]
    dsx: dict[str, object]
    smtp: dict[str, object]
    scheduler: dict[str, object]
    demo_mode: bool
