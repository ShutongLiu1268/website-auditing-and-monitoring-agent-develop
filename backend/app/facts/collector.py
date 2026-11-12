"""Collect deterministic DOM and network facts from a rendered page."""

from typing import Any

from playwright.async_api import Page

from app.acquisition.zone_extractor import Zone
from app.facts.models import DimensionFact, ImageFact, LinkFact, MediaFact, PageFacts
from app.tools.units import UnitParser

_UNPROBED_ZONES = frozenset({"global_footer"})

_DOM_FACTS_SCRIPT = """
(selectors) => {
  const roots = selectors.map((selector) => document.querySelector(selector)).filter((root) => root !== null);
  const inZone = (element) => roots.some((root) => root.contains(element));
  return {
    links: Array.from(document.querySelectorAll('a')).map((element, index) => ({
      href: element.href || '',
      locator: `a:nth-of-type(${index + 1})`,
      in_zone: inZone(element)
    })),
    images: Array.from(document.querySelectorAll('img')).map((element, index) => ({
      src: element.currentSrc || element.src || '',
      alt: element.hasAttribute('alt') ? element.getAttribute('alt') : null,
      loaded: element.complete && element.naturalWidth > 0,
      locator: `img:nth-of-type(${index + 1})`
    })),
    videos: Array.from(document.querySelectorAll('video')).map((element, index) => ({
      src: element.currentSrc || element.src || '',
      broken: Boolean(element.error) || (element.networkState === 3 && Boolean(element.currentSrc || element.src)),
      locator: `video:nth-of-type(${index + 1})`
    }))
  };
}
"""


class FactCollector:
    """Collect reusable facts once per rendered page."""

    async def collect(
        self,
        page: Page,
        zones: list[Zone],
        response_statuses: dict[str, int] | None = None,
    ) -> PageFacts:
        """Collect links, images, dimensions, and observed network responses."""
        response_statuses = response_statuses or {}
        selectors = [
            zone.metadata["selector"]
            for zone in zones
            if zone.name not in _UNPROBED_ZONES and "selector" in zone.metadata
        ]
        dom_data: dict[str, list[dict[str, Any]]] = await page.evaluate(
            _DOM_FACTS_SCRIPT, selectors
        )
        links = [
            LinkFact(
                href=str(item.get("href", "")),
                locator=str(item.get("locator", "")),
                status_code=response_statuses.get(str(item.get("href", ""))),
                reachable=_reachable(response_statuses.get(str(item.get("href", "")))),
                in_zone=bool(item.get("in_zone", False)),
            )
            for item in dom_data.get("links", [])
        ]
        images = [
            ImageFact(
                src=str(item.get("src", "")),
                locator=str(item.get("locator", "")),
                loaded=bool(item.get("loaded", False)),
                alt=item.get("alt"),
            )
            for item in dom_data.get("images", [])
        ]
        dimensions: list[DimensionFact] = []
        for zone in zones:
            parsed = UnitParser.parse_length(zone.text) or UnitParser.parse_weight(
                zone.text
            )
            if parsed:
                value, unit = parsed
                dimensions.append(
                    DimensionFact(
                        text=zone.text,
                        value=value,
                        unit=unit,
                        locator=zone.dom_locator,
                    )
                )
        media = [
            MediaFact(
                src=str(item.get("src", "")),
                locator=str(item.get("locator", "")),
                broken=bool(item.get("broken", False)),
            )
            for item in dom_data.get("videos", [])
        ]
        return PageFacts(links=links, images=images, dimensions=dimensions, media=media)


def _reachable(status_code: int | None) -> bool | None:
    """Convert an observed response status to reachability."""
    if status_code is None:
        return None
    return status_code < 400
