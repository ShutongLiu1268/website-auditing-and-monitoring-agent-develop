"""Sanitize stored HTML before iframe delivery."""

import re
from html import escape

_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
_EVENT_HANDLER_RE = re.compile(
    r"\s+on[a-z]+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE
)
_JAVASCRIPT_URL_RE = re.compile(r"javascript:", re.IGNORECASE)
_BASE_RE = re.compile(r"<base\b[^>]*>", re.IGNORECASE)
_HEAD_RE = re.compile(r"<head\b[^>]*>", re.IGNORECASE)


def sanitize_capture_html(html: str) -> str:
    """Remove executable script content, inline event handlers, and base tags."""
    sanitized = _SCRIPT_RE.sub("", html)
    sanitized = _EVENT_HANDLER_RE.sub("", sanitized)
    sanitized = _BASE_RE.sub("", sanitized)
    return _JAVASCRIPT_URL_RE.sub("#", sanitized)


def with_base_url(html: str, url: str) -> str:
    """Resolve relative stylesheet, image, and link URLs against the captured page."""
    base = f'<base href="{escape(url, quote=True)}">'
    head = _HEAD_RE.search(html)
    if head is None:
        return base + html
    return html[: head.end()] + base + html[head.end() :]
