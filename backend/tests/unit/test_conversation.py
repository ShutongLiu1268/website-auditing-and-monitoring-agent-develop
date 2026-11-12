"""Unit tests for typed chat parsing and service."""

import pytest

from app.conversation.parser import ChatCommandParser
from app.conversation.service import ConversationService
from app.domain.models import AuditMode


def test_parser_extracts_audit_urls_mode_and_locales():
    """Test complete multi-target audit command parsing."""
    command = ChatCommandParser().parse(
        "Review https://example.test/us and https://example.test/ca against R3 for en-US and en-CA."
    )

    assert command.action == "audit_create"
    assert command.mode == AuditMode.R3
    assert len(command.targets) == 2
    assert [target.locale for target in command.targets] == ["en-US", "en-CA"]
    assert command.clarification is None


def test_parser_requests_clarification_for_missing_mode():
    """Test incomplete audit setup."""
    command = ChatCommandParser().parse("Audit https://example.test/pdp")

    assert command.action == "audit_create"
    assert command.clarification is not None


def test_parser_recognizes_result_query():
    """Test findings query intent."""
    command = ChatCommandParser().parse("Show high severity issues")

    assert command.action == "findings_query"
    assert command.query == "Show high severity issues"


@pytest.mark.asyncio
async def test_conversation_service_creates_audit(mocker):
    """Test complete command creates an audit definition."""
    audit_repo = mocker.MagicMock()
    audit_repo.create = mocker.AsyncMock()
    rule_repo = mocker.MagicMock()
    rule_repo.get_latest_version = mocker.AsyncMock(return_value="guide-v1")

    response = await ConversationService(audit_repo, rule_repo).handle(
        "Review https://example.test/pdp against R3 for en-US"
    )

    assert response.type == "accepted"
    assert response.audit_id is not None
    audit_repo.create.assert_awaited_once()
