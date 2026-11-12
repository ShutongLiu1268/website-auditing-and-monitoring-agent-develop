"""Dell GenAI gateway client provider built on csoutils DSXClient."""

import logging
import ssl
from typing import Any

from app.config import Settings

try:
    from cso.ai import DSXClient
except ImportError:  # csoutils[ai] is optional for tests
    DSXClient = None

logger = logging.getLogger(__name__)


def missing_dsx_settings(config: Settings) -> list[str]:
    """Return names of settings required before a DSX client can be built."""
    required = {
        "DSX_BASE_URL": config.DSX_BASE_URL,
        "DSX_CLIENT_ID": config.DSX_CLIENT_ID,
        "DSX_CLIENT_SECRET": config.DSX_CLIENT_SECRET,
        "DSX_MODEL": config.DSX_MODEL,
    }
    return [name for name, value in required.items() if not value.strip()]


def tls_verification(config: Settings) -> ssl.SSLContext | bool:
    """Return TLS verification for DSX traffic.

    Verification stays on and uses the operating-system trust store, which carries
    Dell corporate CAs that certifi lacks, or an explicit PEM bundle when configured.
    csoutils forwards this value to httpx ``verify``, which accepts an SSLContext.
    """
    if not config.DSX_VERIFY_TLS:
        return False
    return ssl.create_default_context(cafile=config.DSX_CA_BUNDLE or None)


class DSXClientProvider:
    """Builds one async OpenAI-compatible DSX client, or none when unavailable."""

    def __init__(self, config: Settings) -> None:
        self.model: str = config.DSX_MODEL
        self.client: Any | None = self._build_client(config)

    @property
    def is_configured(self) -> bool:
        return self.client is not None

    async def aclose(self) -> None:
        if self.client is not None:
            await self.client.close()

    @staticmethod
    def _build_client(config: Settings) -> Any | None:
        missing = missing_dsx_settings(config)
        if missing:
            logger.warning(
                "DSX client not initialized; missing settings: %s", ", ".join(missing)
            )
            return None
        if DSXClient is None:
            logger.warning("DSX client not initialized; csoutils[ai] is not installed")
            return None
        try:
            return DSXClient(
                base_url=config.DSX_BASE_URL,
                client_id=config.DSX_CLIENT_ID,
                client_secret=config.DSX_CLIENT_SECRET,
                auth_method=config.DSX_AUTH_METHOD,
                api_key=config.DSX_API_KEY,
                verify_tls=tls_verification(
                    config
                ),  # pyright: ignore[reportArgumentType]
            ).aopenai
        except Exception as exc:
            logger.error("DSX client initialization failed: %s", type(exc).__name__)
            return None
