"""
Shared error envelope and application-specific error codes.
"""

from typing import Any

from pydantic import BaseModel


class AppError(Exception):
    """Base application error with code and details."""

    def __init__(
        self,
        code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
        retryable: bool = False,
    ):
        self.code = code
        self.message = message
        self.details = details or []
        self.retryable = retryable
        super().__init__(message)


class ErrorEnvelope(BaseModel):
    """Standard error response envelope."""

    error: "ErrorDetail"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = []
    request_id: str | None = None
    retryable: bool = False


# Error codes
class ErrorCode:
    # Validation
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_URL = "INVALID_URL"
    INVALID_LOCALE = "INVALID_LOCALE"
    TOO_MANY_URLS = "TOO_MANY_URLS"

    # Rule document
    RULE_DOCUMENT_INVALID = "RULE_DOCUMENT_INVALID"
    RULE_INDEX_FAILED = "RULE_INDEX_FAILED"
    RULE_NOT_FOUND = "RULE_NOT_FOUND"

    # Acquisition
    URL_POLICY_VIOLATION = "URL_POLICY_VIOLATION"
    SSRF_REJECTED = "SSRF_REJECTED"
    REDIRECT_REJECTED = "REDIRECT_REJECTED"
    PLAYWRIGHT_TIMEOUT = "PLAYWRIGHT_TIMEOUT"
    PLAYWRIGHT_ERROR = "PLAYWRIGHT_ERROR"

    # Extraction
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    ZONE_NOT_FOUND = "ZONE_NOT_FOUND"

    # DSX
    DSX_UNAVAILABLE = "DSX_UNAVAILABLE"
    DSX_RATE_LIMITED = "DSX_RATE_LIMITED"
    DSX_MALFORMED_OUTPUT = "DSX_MALFORMED_OUTPUT"
    DSX_CONTEXT_EXCEEDED = "DSX_CONTEXT_EXCEEDED"

    # Persistence
    PERSISTENCE_ERROR = "PERSISTENCE_ERROR"
    DUPLICATE_RUN = "DUPLICATE_RUN"

    # Comparison
    COMPARISON_MISMATCH = "COMPARISON_MISMATCH"
