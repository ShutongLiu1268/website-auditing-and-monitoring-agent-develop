"""Active reachability probes for public links inside the audited zones."""

import asyncio
import time
from collections.abc import Callable

from playwright.async_api import APIRequestContext
from playwright.async_api import Error as PlaywrightError

from app.acquisition.url_policy import URLPolicy
from app.facts.models import LinkFact, PageFacts

_UNVERIFIABLE_STATUSES = frozenset({401, 403, 429, 999})


class LinkProber:
    """Probe in-zone public links with HEAD, retrying with GET on error statuses."""

    def __init__(
        self,
        *,
        max_urls: int,
        concurrency: int,
        timeout_ms: float,
        cache_seconds: float = 0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_urls = max_urls
        self._concurrency = concurrency
        self._timeout_ms = timeout_ms
        self._cache_seconds = cache_seconds
        self._clock = clock
        self._cache: dict[str, tuple[float, int]] = {}

    async def probe(
        self,
        request: APIRequestContext,
        facts: PageFacts,
    ) -> tuple[PageFacts, list[str]]:
        """Return facts with probed link status and any probe warnings."""
        now = self._clock()
        urls = list(
            dict.fromkeys(
                link.href
                for link in facts.links
                if link.in_zone and URLPolicy.is_public_http_url(link.href)
            )
        )
        cached = {
            url: entry[1]
            for url in urls
            if (entry := self._cache.get(url)) is not None and entry[0] > now
        }
        pending = [url for url in urls if url not in cached]
        targets = pending[: self._max_urls]
        warnings = (
            [f"link_probe_capped:{len(targets)}/{len(pending)}"]
            if len(pending) > len(targets)
            else []
        )
        semaphore = asyncio.Semaphore(self._concurrency)

        async def probe_one(url: str) -> tuple[str, int | None]:
            async with semaphore:
                return url, await self._status(request, url)

        probed = dict(await asyncio.gather(*(probe_one(url) for url in targets)))
        for url, status in probed.items():
            if status is not None and self._cache_seconds > 0:
                self._cache[url] = (now + self._cache_seconds, status)
        links = [self._apply(link, {**cached, **probed}) for link in facts.links]
        return facts.model_copy(update={"links": links}), warnings

    async def _status(self, request: APIRequestContext, url: str) -> int | None:
        try:
            response = await request.head(url, timeout=self._timeout_ms)
            if response.status >= 400:
                await response.dispose()
                response = await request.get(url, timeout=self._timeout_ms)
            status = response.status
            await response.dispose()
            return status
        except PlaywrightError:
            return None

    @staticmethod
    def _apply(link: LinkFact, statuses: dict[str, int | None]) -> LinkFact:
        status = statuses.get(link.href)
        if status is None:
            return link
        return link.model_copy(
            update={"status_code": status, "reachable": _reachable(status)}
        )


def _reachable(status: int) -> bool | None:
    if status in _UNVERIFIABLE_STATUSES:
        return None
    return status < 400
