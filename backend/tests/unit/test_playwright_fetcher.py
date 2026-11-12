"""Unit tests for the Playwright acquisition boundary."""

from hashlib import sha256

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from pytest_mock import MockerFixture

from app.acquisition.playwright_fetcher import PageFetcher
from app.acquisition.zone_extractor import Zone
from app.errors import AppError, ErrorCode
from app.facts.models import PageFacts


@pytest.fixture
def playwright_mocks(mocker: MockerFixture):
    """Build mocked Playwright, browser, and page handles."""
    html = "<html><body><h1>Dell PDP</h1></body></html>"
    page = mocker.MagicMock()
    page.goto = mocker.AsyncMock()
    page.wait_for_timeout = mocker.AsyncMock()
    page.wait_for_load_state = mocker.AsyncMock()
    page.evaluate = mocker.AsyncMock()
    page.content = mocker.AsyncMock(return_value=html)
    page.close = mocker.AsyncMock()

    browser = mocker.MagicMock()
    browser.new_page = mocker.AsyncMock(return_value=page)
    browser.close = mocker.AsyncMock()

    playwright = mocker.MagicMock()
    playwright.chromium.launch = mocker.AsyncMock(return_value=browser)
    playwright.stop = mocker.AsyncMock()

    manager = mocker.MagicMock()
    manager.start = mocker.AsyncMock(return_value=playwright)
    mocker.patch(
        "app.acquisition.playwright_fetcher.async_playwright", return_value=manager
    )
    return page, browser, playwright, html


@pytest.mark.asyncio
async def test_fetch_page_returns_zones_and_stable_hash(
    playwright_mocks, mocker: MockerFixture
):
    """Test rendered page output and page lifecycle."""
    page, browser, _, html = playwright_mocks
    zone = Zone(
        name="hero",
        text="Dell PDP",
        dom_locator=".hero >> nth=0",
        metadata={"selector": ".hero"},
    )
    extractor = mocker.MagicMock()
    extractor.extract = mocker.AsyncMock(return_value=[zone])
    fact_collector = mocker.MagicMock()
    fact_collector.collect = mocker.AsyncMock(return_value=PageFacts())
    fetcher = PageFetcher(extractor, fact_collector)

    fetched = await fetcher.fetch_page("https://example.test/pdp")

    assert fetched.url == "https://example.test/pdp"
    assert fetched.html == html
    assert fetched.zones == [zone]
    assert fetched.content_hash == sha256(html.encode("utf-8")).hexdigest()
    assert fetched.facts == PageFacts()
    fact_collector.collect.assert_awaited_once()
    page.close.assert_awaited_once()
    browser.new_page.assert_awaited_once()
    extractor.extract.assert_awaited_once_with(page)


@pytest.mark.asyncio
async def test_fetch_page_maps_timeout_and_closes_page(
    playwright_mocks, mocker: MockerFixture
):
    """Test timeout mapping and cleanup."""
    page, _, _, _ = playwright_mocks
    page.goto.side_effect = PlaywrightTimeoutError("timeout")
    fetcher = PageFetcher(mocker.MagicMock())

    with pytest.raises(AppError) as error:
        await fetcher.fetch_page("https://example.test/pdp")

    assert error.value.code == ErrorCode.PLAYWRIGHT_TIMEOUT
    page.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_closes_browser_and_playwright(
    playwright_mocks, mocker: MockerFixture
):
    """Test reusable browser shutdown."""
    _, browser, playwright, _ = playwright_mocks
    fetcher = PageFetcher(mocker.MagicMock())
    await fetcher.start()

    await fetcher.stop()
    await fetcher.stop()

    browser.close.assert_awaited_once()
    playwright.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_page_probes_links_on_request(
    playwright_mocks, mocker: MockerFixture
):
    """Test link probing runs only for checkpoints that read link status."""
    extractor = mocker.MagicMock()
    extractor.extract = mocker.AsyncMock(return_value=[])
    fact_collector = mocker.MagicMock()
    fact_collector.collect = mocker.AsyncMock(return_value=PageFacts())
    link_prober = mocker.MagicMock()
    link_prober.probe = mocker.AsyncMock(return_value=(PageFacts(), []))
    fetcher = PageFetcher(extractor, fact_collector, link_prober)

    await fetcher.fetch_page("https://example.test/pdp")
    link_prober.probe.assert_not_awaited()

    await fetcher.fetch_page("https://example.test/pdp", probe_links=True)
    link_prober.probe.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_page_settles_before_capture(
    playwright_mocks, mocker: MockerFixture
):
    """Test the page is settled before its HTML is captured."""
    page, _, _, _ = playwright_mocks
    settle = mocker.patch(
        "app.acquisition.playwright_fetcher.settle_for_capture", new=mocker.AsyncMock()
    )
    extractor = mocker.MagicMock()
    extractor.extract = mocker.AsyncMock(return_value=[])
    fact_collector = mocker.MagicMock()
    fact_collector.collect = mocker.AsyncMock(return_value=PageFacts())
    fetcher = PageFetcher(extractor, fact_collector)

    await fetcher.fetch_page("https://example.test/pdp")

    settle.assert_awaited_once_with(page)
    page.content.assert_awaited_once()
