"""Unit tests for the DSX client provider. DSXClient is always mocked."""

import ssl

import pytest

from app.agent import llm_provider
from app.agent.llm_provider import (
    DSXClientProvider,
    missing_dsx_settings,
    tls_verification,
)
from app.config import Settings


def _settings(**overrides) -> Settings:
    values = {
        "DSX_BASE_URL": "https://gateway.example.test/v1",
        "DSX_CLIENT_ID": "client-id",
        "DSX_CLIENT_SECRET": "client-secret",
        "DSX_API_KEY": "",
        "DSX_AUTH_METHOD": "client",
        "DSX_MODEL": "gpt-oss-120b",
        "DSX_VERIFY_TLS": True,
        "DSX_CA_BUNDLE": "",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_dsx_defaults_are_safe_for_audits():
    fields = Settings.model_fields
    assert fields["DSX_MODEL"].default == "gpt-oss-120b"
    assert fields["DSX_VERIFY_TLS"].default is True
    assert fields["DSX_AUTH_METHOD"].default == "client"
    assert fields["DSX_JSON_MODE"].default is True
    assert fields["DSX_TIMEOUT_SECONDS"].default == 60.0


def test_missing_dsx_settings_lists_required_values():
    config = _settings(DSX_BASE_URL="", DSX_CLIENT_SECRET=" ")
    assert missing_dsx_settings(config) == ["DSX_BASE_URL", "DSX_CLIENT_SECRET"]


def test_provider_builds_async_client_once_with_expected_arguments(mocker):
    dsx_client = mocker.patch.object(llm_provider, "DSXClient")

    provider = DSXClientProvider(_settings(DSX_API_KEY="api-key"))

    dsx_client.assert_called_once()
    kwargs = dsx_client.call_args.kwargs
    assert kwargs["base_url"] == "https://gateway.example.test/v1"
    assert kwargs["client_id"] == "client-id"
    assert kwargs["client_secret"] == "client-secret"
    assert kwargs["auth_method"] == "client"
    assert kwargs["api_key"] == "api-key"
    assert isinstance(kwargs["verify_tls"], ssl.SSLContext)
    assert provider.client is dsx_client.return_value.aopenai
    assert provider.is_configured is True
    assert provider.model == "gpt-oss-120b"


def test_tls_verification_uses_system_trust_store_by_default():
    context = tls_verification(_settings())

    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_tls_verification_uses_explicit_ca_bundle(mocker):
    create_context = mocker.patch.object(llm_provider.ssl, "create_default_context")

    context = tls_verification(_settings(DSX_CA_BUNDLE="C:/certs/dell-ca.pem"))

    create_context.assert_called_once_with(cafile="C:/certs/dell-ca.pem")
    assert context is create_context.return_value


def test_tls_verification_can_be_disabled_explicitly():
    assert tls_verification(_settings(DSX_VERIFY_TLS=False)) is False


def test_provider_stays_unconfigured_when_settings_are_missing(mocker):
    dsx_client = mocker.patch.object(llm_provider, "DSXClient")

    provider = DSXClientProvider(_settings(DSX_CLIENT_ID=""))

    dsx_client.assert_not_called()
    assert provider.client is None
    assert provider.is_configured is False


def test_provider_stays_unconfigured_when_csoutils_is_missing(mocker):
    mocker.patch.object(llm_provider, "DSXClient", None)

    provider = DSXClientProvider(_settings())

    assert provider.client is None


def test_provider_stays_unconfigured_when_client_construction_fails(mocker):
    mocker.patch.object(llm_provider, "DSXClient", side_effect=ValueError("bad auth method"))

    provider = DSXClientProvider(_settings())

    assert provider.client is None


@pytest.mark.asyncio
async def test_provider_closes_client(mocker):
    dsx_client = mocker.patch.object(llm_provider, "DSXClient")
    client = dsx_client.return_value.aopenai
    client.close = mocker.AsyncMock()

    provider = DSXClientProvider(_settings())
    await provider.aclose()

    client.close.assert_awaited_once()
