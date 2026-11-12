"""Dell SMTP relay transport."""

from email.message import EmailMessage

import aiosmtplib

from app.config import Settings


class SMTPTransport:
    """Send email through configured SMTP relay."""

    def __init__(self, config: Settings) -> None:
        self._config = config

    async def send(self, recipients: list[str], subject: str, html: str) -> str | None:
        """Send an HTML message and return provider message ID when available."""
        if not self._config.SMTP_HOST or not self._config.SMTP_FROM:
            raise RuntimeError("smtp_not_configured")
        message = EmailMessage()
        message["From"] = self._config.SMTP_FROM
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content("Open this report in an HTML-capable email client.")
        message.add_alternative(html, subtype="html")
        response = await aiosmtplib.send(
            message,
            hostname=self._config.SMTP_HOST,
            port=self._config.SMTP_PORT,
            username=self._config.SMTP_USERNAME or None,
            password=self._config.SMTP_PASSWORD or None,
            start_tls=self._config.SMTP_USE_TLS,
            timeout=self._config.SMTP_TIMEOUT_SECONDS,
        )
        return str(response[0]) if response else None
