"""
URL policy and validation for PDP crawling.
"""

from urllib.parse import urlparse

from app.errors import AppError, ErrorCode


class URLPolicy:
    """Validates URLs against Dell PDP policy."""

    ALLOWED_HOSTS = {"www.dell.com", "dell.com"}
    MAX_URLS = 5

    @staticmethod
    def validate_urls(urls: list[str]) -> list[str]:
        """Validate list of URLs against policy."""
        if len(urls) > URLPolicy.MAX_URLS:
            raise AppError(
                ErrorCode.TOO_MANY_URLS,
                f"Maximum {URLPolicy.MAX_URLS} URLs allowed",
            )

        validated = []
        seen = set()

        for url in urls:
            if url in seen:
                raise AppError(ErrorCode.INVALID_URL, f"Duplicate URL: {url}")
            seen.add(url)

            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme != "https":
                raise AppError(ErrorCode.INVALID_URL, f"URL must use HTTPS: {url}")

            # Check host
            if parsed.netloc not in URLPolicy.ALLOWED_HOSTS:
                raise AppError(
                    ErrorCode.URL_POLICY_VIOLATION,
                    f"Host not allowed: {parsed.netloc}",
                )

            # Check for private/reserved IPs
            if URLPolicy._is_private_ip(parsed.netloc):
                raise AppError(
                    ErrorCode.SSRF_REJECTED,
                    f"Private IP rejected: {parsed.netloc}",
                )

            validated.append(url)

        return validated

    @staticmethod
    def is_public_http_url(url: str) -> bool:
        """Return True for http(s) URLs whose host is not a private address."""
        parsed = urlparse(url)
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
            and not URLPolicy._is_private_ip(parsed.netloc)
        )

    @staticmethod
    def _is_private_ip(host: str) -> bool:
        """Check if host is a private IP address."""
        # Simple check for common private IP patterns
        private_patterns = [
            "0.",
            "127.",
            "169.254.",
            "[",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
            "192.168.",
            "localhost",
        ]

        host_lower = host.lower()
        for pattern in private_patterns:
            if host_lower.startswith(pattern):
                return True

        return False

    @staticmethod
    def extract_locale(url: str) -> str:
        """Extract locale from URL path (e.g., /en-us/ -> en-US)."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) >= 1:
            # Format: /en-us/ or /en-ca/
            locale_part = path_parts[0]
            if "-" in locale_part:
                return locale_part.replace("-", "-").lower()

        # Default to en-US if not found
        return "en-us"
