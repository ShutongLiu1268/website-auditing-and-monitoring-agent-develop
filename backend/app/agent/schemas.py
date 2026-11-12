"""
Agent schemas for DSX evaluation and audit orchestration.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.domain.models import TokenUsage


class DSXEvaluationRequest(BaseModel):
    """Request to DSX for single checkpoint evaluation."""

    url: str
    locale: str
    zone: str
    checkpoint_text: str
    checkpoint_id: str
    page_text: str
    deterministic_facts: dict[str, object] = Field(default_factory=dict)
    context: dict[str, object] = Field(default_factory=dict)


class DSXEvaluationResponse(BaseModel):
    """Expected response from DSX evaluation."""

    outcome: Literal["pass", "issue", "not_evaluated"]
    problem: str | None = None
    suggested_correction: str | None = None
    proof_text: str | None = None
    severity: Literal["critical", "high", "medium", "low"] | None = None
    rule_quote: str | None = Field(None, description="Exact checkpoint text")
    evidence_quote: str | None = Field(None, description="Exact page text")
    dom_locator: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    review_required: bool = False
    reasoning: str | None = Field(
        None, description="Why the outcome follows from the evidence"
    )

    @field_validator("outcome", "severity", mode="before")
    @classmethod
    def normalize_label(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class DSXEvaluation(BaseModel):
    """Evaluator result with provenance for persistence and cost tracking."""

    model: str
    attempts: int = 0
    response: DSXEvaluationResponse | None = None
    token_usage: TokenUsage | None = None
    error_code: str | None = None
    error_reason: str | None = None


class AuditPlan(BaseModel):
    """Plan for evaluating a page: zone × checkpoint matrix."""

    page_url: str
    locale: str
    zone_tasks: list["ZoneTask"] = Field(default_factory=list)


class ZoneTask(BaseModel):
    """Tasks for a single zone: applicable checkpoints."""

    zone: str
    checkpoint_ids: list[str] = Field(default_factory=list)
