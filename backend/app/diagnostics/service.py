"""Simple dependency diagnostic probes."""

import time

import aiosmtplib
from openai import OpenAIError

from app.agent.llm_provider import DSXClientProvider
from app.config import Settings
from app.diagnostics.models import DiagnosticResult, DiagnosticSummary


class DiagnosticService:
    """Run simple Mongo/DSX/SMTP diagnostics."""

    def __init__(self, config: Settings, provider: DSXClientProvider) -> None:
        self._config = config
        self._provider = provider

    def summary(
        self,
        *,
        database_reachable: bool,
        rule_available: bool,
        rule_version: str | None,
    ) -> DiagnosticSummary:
        """Build a secret-free dependency summary."""
        return DiagnosticSummary(
            mongo={
                "configured": bool(self._config.MONGODB_URI),
                "reachable": database_reachable,
            },
            rules={"available": rule_available, "version": rule_version},
            dsx={
                "configured": self._provider.is_configured,
                "model": self._config.DSX_MODEL,
            },
            smtp={"configured": bool(self._config.SMTP_HOST)},
            scheduler={"enabled": self._config.SCHEDULER_ENABLED},
            demo_mode=self._config.DEMO_MODE,
        )

    async def probe_dsx(self) -> DiagnosticResult:
        """Send one minimal bounded DSX request."""
        if self._provider.client is None:
            return DiagnosticResult(
                component="dsx",
                status="unavailable",
                error_code="DSX_UNAVAILABLE",
            )
        started = time.perf_counter()
        try:
            response = await self._provider.client.chat.completions.create(
                model=self._config.DSX_MODEL,
                messages=[
                    {"role": "system", "content": "Respond with JSON only."},
                    {"role": "user", "content": '{"diagnostic":"ok"}'},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=16,
                timeout=self._config.DSX_TIMEOUT_SECONDS,
            )
            usage = getattr(response, "usage", None)
            return DiagnosticResult(
                component="dsx",
                status="ok",
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                details={
                    "model": self._config.DSX_MODEL,
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                    "completion_tokens": (getattr(usage, "completion_tokens", 0) if usage else 0),
                },
            )
        except OpenAIError as exc:
            return self._failure("dsx", started, type(exc).__name__)
        except Exception as exc:
            return self._failure("dsx", started, type(exc).__name__)

    async def probe_smtp(self) -> DiagnosticResult:
        """Connect, authenticate, and issue SMTP NOOP without sending mail."""
        if not self._config.SMTP_HOST:
            return DiagnosticResult(
                component="smtp",
                status="unavailable",
                error_code="SMTP_NOT_CONFIGURED",
            )
        started = time.perf_counter()
        client = aiosmtplib.SMTP(
            hostname=self._config.SMTP_HOST,
            port=self._config.SMTP_PORT,
            timeout=self._config.SMTP_TIMEOUT_SECONDS,
            start_tls=self._config.SMTP_USE_TLS,
        )
        try:
            await client.connect()
            if self._config.SMTP_USERNAME:
                await client.login(self._config.SMTP_USERNAME, self._config.SMTP_PASSWORD)
            await client.noop()
            return DiagnosticResult(
                component="smtp",
                status="ok",
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
            )
        except Exception as exc:
            return self._failure("smtp", started, type(exc).__name__)
        finally:
            try:
                await client.quit()
            except Exception:
                pass

    @staticmethod
    def _failure(component: str, started: float, error_code: str) -> DiagnosticResult:
        """Build a redacted diagnostic failure."""
        return DiagnosticResult(
            component=component,
            status="failed",
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            error_code=error_code,
        )
