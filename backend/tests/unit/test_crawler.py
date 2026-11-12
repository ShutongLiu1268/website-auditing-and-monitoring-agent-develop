"""Unit tests for scoped multi-page crawler."""

import pytest
from pytest_mock import MockerFixture

from app.acquisition.crawler import ScopedCrawler
from app.acquisition.playwright_fetcher import FetchedPage
from app.domain.models import CrawlScope, PageTarget
from app.facts.models import LinkFact, PageFacts


def _page(url: str, links: list[str] | None = None) -> FetchedPage:
    """Build a fetched page."""
    return FetchedPage(
        url=url,
        html="<html></html>",
        zones=[],
        content_hash=url,
        warnings=[],
        facts=PageFacts(
            links=[
                LinkFact(href=link, locator="a", status_code=200, reachable=True)
                for link in links or []
            ]
        ),
    )


@pytest.mark.asyncio
async def test_crawler_discovers_same_scope_pages(mocker: MockerFixture):
    """Test linked pages are discovered and deduplicated."""
    fetcher = mocker.MagicMock()
    fetcher.fetch_page = mocker.AsyncMock(
        side_effect=[
            _page(
                "https://example.test/",
                ["https://example.test/products", "https://example.test/products/"],
            ),
            _page("https://example.test/products"),
        ]
    )
    target = PageTarget(url="https://example.test/", locale="en-US")

    result = await ScopedCrawler(fetcher, max_concurrent=1).crawl(
        [target], CrawlScope(page_limit=5, max_depth=1)
    )

    assert [page.coverage.canonical_url for page in result.pages] == [
        "https://example.test/",
        "https://example.test/products",
    ]
    assert any(record.status == "duplicate" for record in result.coverage_pages)
    assert fetcher.fetch_page.await_count == 2


@pytest.mark.asyncio
async def test_crawler_applies_scope_and_page_limit(mocker: MockerFixture):
    """Test excluded paths and page limit coverage."""
    fetcher = mocker.MagicMock()
    fetcher.fetch_page = mocker.AsyncMock(
        return_value=_page("https://example.test/products")
    )
    target = PageTarget(url="https://example.test/", locale="en-US")

    result = await ScopedCrawler(fetcher).crawl(
        [target],
        CrawlScope(include_paths=["/products"], page_limit=1),
    )

    assert len(result.pages) == 0
    assert result.coverage_pages[0].status == "skipped"
    fetcher.fetch_page.assert_not_awaited()


@pytest.mark.asyncio
async def test_crawler_forwards_link_probe_setting(mocker: MockerFixture):
    """Test every page fetch receives the crawler's link probe setting."""
    fetcher = mocker.MagicMock()
    fetcher.fetch_page = mocker.AsyncMock(return_value=_page("https://example.test/"))
    target = PageTarget(url="https://example.test/", locale="en-US")

    await ScopedCrawler(fetcher, probe_links=True).crawl(
        [target], CrawlScope(page_limit=1)
    )

    fetcher.fetch_page.assert_awaited_once_with(
        "https://example.test/", probe_links=True
    )
