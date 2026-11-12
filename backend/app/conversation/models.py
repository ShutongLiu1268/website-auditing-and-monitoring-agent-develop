"""Typed conversation commands and responses."""

from typing import Literal

from pydantic import BaseModel, Field

from app.domain.models import AuditMode, CrawlScope, PageTarget


class ChatCommand(BaseModel):
    """Validated command extracted from one chat message."""

    action: Literal[
        "audit_create",
        "findings_query",
        "comparison_query",
        "schedule_create",
        "unknown",
    ]
    mode: AuditMode | None = None
    targets: list[PageTarget] = Field(default_factory=list)
    scope: CrawlScope = Field(default_factory=CrawlScope)
    query: str | None = None
    clarification: str | None = None


class ChatResponse(BaseModel):
    """Typed chat response returned by the API."""

    type: Literal["clarification", "confirmation", "accepted", "query"]
    message: str
    command: ChatCommand | None = None
    audit_id: str | None = None
    run_id: str | None = None
    data: dict[str, object] = Field(default_factory=dict)
