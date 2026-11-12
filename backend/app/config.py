"""
Application configuration using Pydantic Settings.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "npl_pdp_audit"
    MONGODB_COLLECTION_PREFIX: str = "pdp"

    # DSX (Dell GenAI gateway through csoutils DSXClient)
    DSX_BASE_URL: str = ""
    DSX_CLIENT_ID: str = ""
    DSX_CLIENT_SECRET: str = ""
    DSX_API_KEY: str = ""
    DSX_AUTH_METHOD: Literal["client", "server"] = "client"
    DSX_MODEL: str = "gpt-oss-120b"
    DSX_VERIFY_TLS: bool = True
    DSX_CA_BUNDLE: str = ""
    DSX_JSON_MODE: bool = True
    DSX_TIMEOUT_SECONDS: float = 60.0
    DSX_MAX_CONCURRENT: int = 4

    # Playwright and crawling
    PLAYWRIGHT_TIMEOUT_MS: int = 30000
    PLAYWRIGHT_IDLE_MS: int = 5000
    PLAYWRIGHT_MAX_CONCURRENT: int = 3
    PLAYWRIGHT_SAME_HOST_DELAY_MS: int = 2000
    PLAYWRIGHT_HEADLESS: bool = True
    HTML_CAPTURE_MAX_BYTES: int = 5_000_000
    CRAWL_MAX_CONCURRENT: int = 3
    CRAWL_SAME_HOST_DELAY_MS: int = 2000
    CRAWL_MAX_DEPTH: int = 2
    CRAWL_DEFAULT_PAGE_LIMIT: int = 25
    LINK_PROBE_MAX_URLS: int = 100
    LINK_PROBE_CONCURRENCY: int = 8
    LINK_PROBE_TIMEOUT_MS: int = 10000
    LINK_PROBE_CACHE_SECONDS: int = 900
    RUN_HEARTBEAT_SECONDS: int = 10
    RUN_STALE_SECONDS: int = 60

    # SMTP delivery
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_FROM: str = ""
    SMTP_TIMEOUT_SECONDS: float = 30.0

    # Scheduling
    SCHEDULER_ENABLED: bool = False
    SCHEDULER_POLL_SECONDS: int = 30
    SCHEDULER_TIMEZONE: str = "UTC"

    # Audit execution
    DEMO_MODE: bool = True
    REPORT_BRAND_NAME: str = "NPL PDP Audit Copilot"

    # Application
    APP_NAME: str = "NPL PDP Audit"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False


settings = Settings()
