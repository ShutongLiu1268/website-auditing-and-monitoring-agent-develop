"""
Unit tests for URL policy.
"""

import pytest

from app.acquisition.url_policy import URLPolicy
from app.errors import AppError, ErrorCode


def test_validate_urls_valid():
    """Test validation of valid URLs."""
    urls = [
        "https://www.dell.com/en-us/shop/laptops",
        "https://www.dell.com/en-ca/shop/laptops",
    ]
    validated = URLPolicy.validate_urls(urls)
    assert len(validated) == 2


def test_validate_urls_too_many():
    """Test rejection of too many URLs."""
    urls = [f"https://www.dell.com/en-us/shop/laptops{i}" for i in range(6)]
    with pytest.raises(AppError) as exc:
        URLPolicy.validate_urls(urls)
    assert exc.value.code == ErrorCode.TOO_MANY_URLS


def test_validate_urls_duplicate():
    """Test rejection of duplicate URLs."""
    urls = [
        "https://www.dell.com/en-us/shop/laptops",
        "https://www.dell.com/en-us/shop/laptops",
    ]
    with pytest.raises(AppError) as exc:
        URLPolicy.validate_urls(urls)
    assert exc.value.code == ErrorCode.INVALID_URL


def test_validate_urls_non_https():
    """Test rejection of non-HTTPS URLs."""
    urls = ["http://www.dell.com/en-us/shop/laptops"]
    with pytest.raises(AppError) as exc:
        URLPolicy.validate_urls(urls)
    assert exc.value.code == ErrorCode.INVALID_URL


def test_validate_urls_invalid_host():
    """Test rejection of invalid host."""
    urls = ["https://example.com/en-us/shop/laptops"]
    with pytest.raises(AppError) as exc:
        URLPolicy.validate_urls(urls)
    assert exc.value.code == ErrorCode.URL_POLICY_VIOLATION


def test_extract_locale():
    """Test locale extraction from URL."""
    assert (
        URLPolicy.extract_locale("https://www.dell.com/en-us/shop/laptops") == "en-us"
    )
    assert (
        URLPolicy.extract_locale("https://www.dell.com/en-ca/shop/laptops") == "en-ca"
    )
    assert (
        URLPolicy.extract_locale("https://www.dell.com/fr-ca/shop/laptops") == "fr-ca"
    )


def test_extract_locale_default():
    """Test default locale when not found."""
    assert URLPolicy.extract_locale("https://www.dell.com/shop/laptops") == "en-us"


def test_public_http_url_allows_public_hosts():
    """Test public http and https links may be probed."""
    assert (
        URLPolicy.is_public_http_url("https://www.dell.com/en-us/shop/laptops") is True
    )


def test_public_http_url_rejects_private_hosts_and_other_schemes():
    """Test private addresses and non-web schemes are never probed."""
    assert URLPolicy.is_public_http_url("http://10.0.0.5/admin") is False
    assert URLPolicy.is_public_http_url("http://0.0.0.0/") is False
    assert URLPolicy.is_public_http_url("javascript:void(0)") is False
    assert URLPolicy.is_public_http_url("mailto:sales@dell.com") is False
