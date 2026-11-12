"""Scoped multi-page crawler with canonical URL deduplication."""

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from app.acquisition.playwright_fetcher import FetchedPage, PageFetcher
from app.domain.models import CrawlPage, CrawlScope, PageTarget


@dataclass(frozen=True)
class CrawledPage:
    """One successfully fetched page and its target context."""

    target: PageTarget
    fetched: FetchedPage
    coverage: CrawlPage


@dataclass(frozen=True)
class CrawlResult:
    """Fetched pages plus coverage records."""

    pages: list[CrawledPage]
    coverage_pages: list[CrawlPage]


class ScopedCrawler:
    """Discover and fetch pages within an audit scope."""

    def __init__(
        self,
        fetcher: PageFetcher,
        max_concurrent: int = 2,
        on_fetched: Callable[[CrawledPage], Awaitable[None]] | None = None,
        probe_links: bool = False,
    ) -> None:
        self._fetcher = fetcher
        self._max_concurrent = max(1, max_concurrent)
        self._on_fetched = on_fetched
        self._probe_links = probe_links

    async def crawl(
        self,
        targets: list[PageTarget],
        scope: CrawlScope,
    ) -> CrawlResult:
        """Fetch target pages and same-scope linked pages."""
        queue: deque[tuple[PageTarget, str, int, str | None]] = deque(
            (target, str(target.url), 0, None) for target in targets
        )
        seen: set[str] = set()
        pages: list[CrawledPage] = []
        coverage: list[CrawlPage] = []
        semaphore = asyncio.Semaphore(self._max_concurrent)

        while queue and len(pages) < scope.page_limit:
            batch: list[tuple[PageTarget, str, int, str | None]] = []
            while (
                queue
                and len(batch) < self._max_concurrent
                and len(pages) + len(batch) < scope.page_limit
            ):
                batch.append(queue.popleft())
            results = await asyncio.gather(
                *(
                    self._fetch_one(
                        target,
                        url,
                        depth,
                        discovered_from,
                        scope,
                        seen,
                        semaphore,
                    )
                    for target, url, depth, discovered_from in batch
                )
            )
            for crawled, record, links in results:
                coverage.append(record)
                if crawled is None:
                    continue
                pages.append(crawled)
                if len(pages) >= scope.page_limit:
                    break
                for link in links:
                    if link[2] <= scope.max_depth:
                        queue.append(link)

        while queue:
            target, url, depth, discovered_from = queue.popleft()
            coverage.append(
                CrawlPage(
                    url=url,
                    canonical_url=self.normalize_url(url),
                    depth=depth,
                    status="skipped",
                    reason="page_limit_reached",
                    discovered_from=discovered_from,
                )
            )
        return CrawlResult(pages=pages, coverage_pages=coverage)

    async def _fetch_one(
        self,
        target: PageTarget,
        url: str,
        depth: int,
        discovered_from: str | None,
        scope: CrawlScope,
        seen: set[str],
        semaphore: asyncio.Semaphore,
    ) -> tuple[
        CrawledPage | None, CrawlPage, list[tuple[PageTarget, str, int, str | None]]
    ]:
        """Fetch one page and return discovered links."""
        canonical = self.normalize_url(url)
        record = CrawlPage(
            url=url,
            canonical_url=canonical,
            depth=depth,
            status="queued",
            discovered_from=discovered_from,
        )
        if canonical in seen:
            return None, record.model_copy(update={"status": "duplicate"}), []
        if not self._in_scope(url, target, scope):
            return (
                None,
                record.model_copy(
                    update={"status": "skipped", "reason": "out_of_scope"}
                ),
                [],
            )
        seen.add(canonical)
        try:
            async with semaphore:
                fetched = await self._fetcher.fetch_page(
                    url, probe_links=self._probe_links
                )
            crawled = CrawledPage(
                target=target,
                fetched=fetched,
                coverage=record.model_copy(update={"status": "scanned"}),
            )
            if self._on_fetched is not None:
                await self._on_fetched(crawled)
            links = []
            for link in fetched.facts.links:
                if not link.href:
                    continue
                link_target = urljoin(url, link.href)
                links.append((target, link_target, depth + 1, url))
            return crawled, crawled.coverage, links
        except TimeoutError:
            return None, record.model_copy(update={"status": "timeout"}), []
        except Exception as exc:
            return (
                None,
                record.model_copy(
                    update={"status": "inaccessible", "reason": type(exc).__name__}
                ),
                [],
            )

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL for duplicate detection."""
        parsed = urlparse(url)
        query = urlencode(
            sorted(
                (key, value)
                for key, value in parse_qsl(parsed.query)
                if not key.lower().startswith("utm_")
            )
        )
        path = parsed.path.rstrip("/") or "/"
        return urlunparse(
            (parsed.scheme.lower(), parsed.netloc.lower(), path, "", query, "")
        )

    @classmethod
    def _in_scope(cls, url: str, target: PageTarget, scope: CrawlScope) -> bool:
        """Check host and include/exclude path rules."""
        target_host = urlparse(str(target.url)).netloc.lower()
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc.lower() != target_host:
            return False
        path = parsed.path or "/"
        if scope.include_paths and not any(
            path.startswith(prefix) for prefix in scope.include_paths
        ):
            return False
        return not any(path.startswith(prefix) for prefix in scope.exclude_paths)
