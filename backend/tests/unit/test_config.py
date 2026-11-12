"""Unit tests for application configuration."""

from app.config import Settings


def test_defaults_do_not_require_external_services():
    """Default settings start without DSX or SMTP credentials."""
    config = Settings(_env_file=None)

    assert config.SMTP_HOST == ""
    assert config.DSX_VERIFY_TLS is True
    assert config.DEMO_MODE is True


def test_scheduler_timezone_is_configurable():
    """Scheduler timezone is read from environment/settings."""
    config = Settings(_env_file=None, SCHEDULER_TIMEZONE="America/New_York")

    assert config.SCHEDULER_TIMEZONE == "America/New_York"
