"""Playwright-based page fetcher for PDP extraction."""

import asyncio
import contextlib
import sys
import threading
from collections.abc import Coroutine
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, TypeVar

from playwright.async_api import Browser, Page, Playwright, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.acquisition.page_settle import CAPTURE_VIEWPORT, settle_for_capture
from app.acquisition.zone_extractor import Zone, ZoneExtractor
from app.config import settings
from app.errors import AppError, ErrorCode
from app.facts.collector import FactCollector
from app.facts.link_probe import LinkProber
from app.facts.models import PageFacts

_T = TypeVar("_T")


@dataclass(frozen=True)
class FetchedPage:
    """Rendered page data returned by the acquisition boundary."""

    url: str
    html: str
    zones: list[Zone]
    content_hash: str
    warnings: list[str]
    facts: PageFacts = field(default_factory=PageFacts)


class PageFetcher:
    """Fetch and render PDP pages using Playwright."""

    def __init__(
        self,
        zone_extractor: ZoneExtractor | None = None,
        fact_collector: FactCollector | None = None,
        link_prober: LinkProber | None = None,
    ) -> None:
        self._zone_extractor = zone_extractor or ZoneExtractor()
        self._fact_collector = fact_collector or FactCollector()
        self._link_prober = link_prober or LinkProber(
            max_urls=settings.LINK_PROBE_MAX_URLS,
            concurrency=settings.LINK_PROBE_CONCURRENCY,
            timeout_ms=settings.LINK_PROBE_TIMEOUT_MS,
            cache_seconds=settings.LINK_PROBE_CACHE_SECONDS,
        )
        self._playwright: Playwright | None = None
        self._start_lock: asyncio.Lock | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self.browser: Browser | None = None

    async def start(self) -> None:
        """Start one reusable Chromium instance."""
        await self._run(self._ensure_browser())

    async def stop(self) -> None:
        """Stop browser and Playwright handles safely."""
        loop, thread = self._loop, self._loop_thread
        if loop is None:
            return
        await self._run(self._stop_browser())
        self._loop, self._loop_thread = None, None
        loop.call_soon_threadsafe(loop.stop)
        if thread is not None:
            await asyncio.to_thread(thread.join)
        loop.close()

    async def fetch_page(self, url: str, *, probe_links: bool = False) -> FetchedPage:
        """Fetch one rendered page and extract its semantic zones."""
        return await self._run(self._fetch_page(url, probe_links))

    async def _run(self, coro: Coroutine[Any, Any, _T]) -> _T:
        future = asyncio.run_coroutine_threadsafe(coro, self._ensure_loop())
        return await asyncio.wrap_future(future)

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            loop = (
                asyncio.ProactorEventLoop()
                if sys.platform == "win32"
                else asyncio.new_event_loop()
            )
            self._loop_thread = threading.Thread(target=loop.run_forever, daemon=True)
            self._loop_thread.start()
            self._loop = loop
        return self._loop

    async def _ensure_browser(self) -> Browser:
        if self._start_lock is None:
            self._start_lock = asyncio.Lock()
        async with self._start_lock:
            if self.browser is None:
                self._playwright = await async_playwright().start()
                self.browser = await self._playwright.chromium.launch(
                    headless=settings.PLAYWRIGHT_HEADLESS
                )
        return self.browser

    async def _stop_browser(self) -> None:
        self._start_lock = None
        if self.browser is not None:
            await self.browser.close()
            self.browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def _fetch_page(self, url: str, probe_links: bool) -> FetchedPage:
        browser = await self._ensure_browser()
        page: Page = await browser.new_page(viewport=CAPTURE_VIEWPORT)
        response_statuses: dict[str, int] = {}
        page.on(
            "response",
            lambda response: response_statuses.__setitem__(
                response.url, response.status
            ),
        )
        try:
            await page.goto(
                url,
                timeout=settings.PLAYWRIGHT_TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            with contextlib.suppress(PlaywrightTimeoutError):
                await page.wait_for_load_state(
                    "networkidle", timeout=settings.PLAYWRIGHT_IDLE_MS
                )
            await settle_for_capture(page)
            await page.wait_for_timeout(1000)
            html = await page.content()
            zones = await self._zone_extractor.extract(page)
            facts = await self._fact_collector.collect(page, zones, response_statuses)
            probe_warnings: list[str] = []
            if probe_links:
                facts, probe_warnings = await self._link_prober.probe(
                    page.request, facts
                )
            return FetchedPage(
                url=url,
                html=html,
                zones=zones,
                content_hash=sha256(html.encode("utf-8")).hexdigest(),
                warnings=probe_warnings,
                facts=facts,
            )
        except PlaywrightTimeoutError as exc:
            raise AppError(
                ErrorCode.PLAYWRIGHT_TIMEOUT,
                f"Page load timeout: {url}",
            ) from exc
        except AppError:
            raise
        except Exception as exc:
            raise AppError(
                ErrorCode.PLAYWRIGHT_ERROR,
                f"Page fetch failed: {type(exc).__name__}",
            ) from exc
        finally:
            await page.close()
