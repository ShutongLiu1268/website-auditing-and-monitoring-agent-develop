"""Test script to send an email using configured SMTP settings."""

import asyncio
from email.message import EmailMessage

import aiosmtplib

from app.config import settings


async def send_test_email():
    """Send a test email to verify SMTP configuration."""
    recipient = "shutong.liu@dell.com"

    print(f"Sending test email to {recipient}...")
    print(f"SMTP Host: {settings.SMTP_HOST}")
    print(f"SMTP Port: {settings.SMTP_PORT}")
    print(f"SMTP Username: {settings.SMTP_USERNAME}")
    print(f"SMTP From: {settings.SMTP_FROM}")

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = recipient
    message["Subject"] = "Test Email from NPL PDP Audit Application"
    message.set_content("This is a test email to verify SMTP configuration.")
    message.add_alternative(
        """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email to verify SMTP configuration.</p>
            <p>If you received this, the email configuration is working correctly!</p>
        </body>
        </html>
        """,
        subtype="html",
    )

    try:
        # Try with authentication first
        try:
            response = await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME or None,
                password=settings.SMTP_PASSWORD or None,
                start_tls=settings.SMTP_USE_TLS,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            )
            print(f"Email sent successfully with authentication!")
            print(f"  Response: {response}")
            return True
        except Exception as auth_error:
            print(f"Authentication failed: {auth_error}")
            print("Trying without authentication...")

            # Try without authentication
            response = await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=None,
                password=None,
                start_tls=settings.SMTP_USE_TLS,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            )
            print(f"Email sent successfully without authentication!")
            print(f"  Response: {response}")
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(send_test_email())
