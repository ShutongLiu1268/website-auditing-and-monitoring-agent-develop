"""Unit tests for simple infrastructure diagnostics."""

from types import SimpleNamespace

import pytest

from app.agent.llm_provider import DSXClientProvider
from app.config import Settings
from app.diagnostics.service import DiagnosticService


def _settings(**overrides) -> Settings:
    """Build diagnostic settings without reading env files."""
    values = {
        "MONGODB_URI": "mongodb://localhost:27017",
        "SMTP_HOST": "smtp.example.test",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.asyncio
async def test_dsx_probe_returns_latency_and_usage(mocker):
    """Test successful DSX diagnostic response."""
    provider = mocker.MagicMock(spec=DSXClientProvider)
    provider.client = mocker.MagicMock()
    provider.is_configured = True
    provider.client.chat.completions.create = mocker.AsyncMock(
        return_value=SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=4, completion_tokens=2),
        )
    )

    result = await DiagnosticService(_settings(), provider).probe_dsx()

    assert result.status == "ok"
    assert result.details["prompt_tokens"] == 4
    provider.client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_dsx_probe_is_unavailable_without_client(mocker):
    """Test missing DSX configuration is safe."""
    provider = mocker.MagicMock(spec=DSXClientProvider)
    provider.client = None
    provider.is_configured = False

    result = await DiagnosticService(_settings(), provider).probe_dsx()

    assert result.status == "unavailable"
    assert result.error_code == "DSX_UNAVAILABLE"


@pytest.mark.asyncio
async def test_smtp_probe_connection(mocker):
    """Test SMTP connectivity probe does not send a message."""
    smtp_client = mocker.patch("app.diagnostics.service.aiosmtplib.SMTP")
    smtp_client.return_value.connect = mocker.AsyncMock()
    smtp_client.return_value.noop = mocker.AsyncMock()
    smtp_client.return_value.quit = mocker.AsyncMock()

    result = await DiagnosticService(_settings(), mocker.MagicMock()).probe_smtp()

    assert result.status == "ok"
    smtp_client.return_value.noop.assert_awaited_once()


@pytest.mark.asyncio
async def test_smtp_probe_requires_host(mocker):
    """Test missing SMTP configuration."""
    result = await DiagnosticService(_settings(SMTP_HOST=""), mocker.MagicMock()).probe_smtp()

    assert result.status == "unavailable"
    assert result.error_code == "SMTP_NOT_CONFIGURED"
