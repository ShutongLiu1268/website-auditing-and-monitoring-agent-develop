"""Conversation application service."""

import hashlib
import uuid

from app.conversation.models import ChatCommand, ChatResponse
from app.conversation.parser import ChatCommandParser
from app.domain.models import AuditDefinition
from app.persistence.repositories import (
    AuditDefinitionRepository,
    RulePassageRepository,
)


class ConversationService:
    """Parse chat and create validated audit definitions."""

    def __init__(
        self,
        audit_repo: AuditDefinitionRepository,
        rule_repo: RulePassageRepository,
        parser: ChatCommandParser | None = None,
    ) -> None:
        self._audit_repo = audit_repo
        self._rule_repo = rule_repo
        self._parser = parser or ChatCommandParser()

    async def handle(self, message: str) -> ChatResponse:
        """Handle one chat message."""
        command = self._parser.parse(message)
        if command.clarification:
            return ChatResponse(
                type="clarification",
                message=command.clarification,
                command=command,
            )
        if command.action == "audit_create":
            return await self._create_audit(command)
        if command.action in {"findings_query", "comparison_query"}:
            return ChatResponse(
                type="query", message="Query accepted.", command=command
            )
        if command.action == "schedule_create":
            return ChatResponse(
                type="clarification",
                message="Provide schedule time, timezone, and recipients.",
                command=command,
            )
        return ChatResponse(
            type="clarification",
            message=command.clarification or "Please provide an audit request.",
            command=command,
        )

    async def _create_audit(self, command: ChatCommand) -> ChatResponse:
        """Create an audit definition from a complete command."""
        assert command.mode is not None
        rule_version = await self._rule_repo.get_latest_version() or "unversioned"
        comparison_key = hashlib.sha256(
            "|".join(
                [
                    command.mode.value,
                    rule_version,
                    "identity-v2",
                    str(command.scope.model_dump()),
                    *[f"{target.url}:{target.locale}" for target in command.targets],
                ]
            ).encode("utf-8")
        ).hexdigest()
        definition = AuditDefinition(
            id=str(uuid.uuid4()),
            mode=command.mode,
            targets=command.targets,
            rule_version=rule_version,
            scope=command.scope,
            comparison_key=comparison_key,
        )
        await self._audit_repo.create(definition)
        return ChatResponse(
            type="accepted",
            message="Audit configuration accepted. Start the audit when ready.",
            command=command,
            audit_id=definition.id,
        )
