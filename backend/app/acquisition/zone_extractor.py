"""Zone extraction: splits PDP DOM into semantic zones with locators."""

from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page

PAGE_ZONE = "page"
_LIST_ITEM_COUNT = (
    "element => ({ list_items: element.querySelectorAll('li, dt, tr').length })"
)


@dataclass
class Zone:
    """A semantic zone extracted from a PDP."""

    name: str
    text: str
    dom_locator: str
    metadata: dict[str, Any]


class ZoneExtractor:
    """Extracts semantic zones from a PDP page."""

    # Zone selectors and their canonical names
    ZONE_SELECTORS = {
        "hero": "[data-testid='pdp-hero'], .pdp-hero, .hero-section",
        "breadcrumbs": ".breadcrumbs, .breadcrumb",
        "media_gallery": ".media-gallery, .product-gallery",
        "configuration_selector": ".configuration-selector, .config-selector",
        "configuration_cards": ".configuration-cards, .config-cards",
        "tech_specs": ".tech-specs, .technical-specifications",
        "features": ".features, .product-features",
        "dimensions_weight": ".dimensions-weight, .dimensions-and-weight",
        "ports_slots": ".ports-slots, .connectivity",
        "reviews": ".reviews, .customer-reviews",
        "support": ".support, .support-section",
        "footnotes_disclaimers": ".footnotes, .disclaimers, .legal-text",
        "global_footer": ".global-footer, footer",
        "legal_trademarks": ".legal-trademarks, .trademark-notice",
    }

    async def extract(self, page: Page) -> list[Zone]:
        """Extract all zones from the page."""
        zones: list[Zone] = []

        for zone_name, selector in self.ZONE_SELECTORS.items():
            try:
                element = page.locator(selector).first
                if await element.count() == 0:
                    continue

                text = await element.inner_text()
                structure = await element.evaluate(_LIST_ITEM_COUNT)
                dom_locator = f"{selector} >> nth=0"

                zone = Zone(
                    name=zone_name,
                    text=text.strip(),
                    dom_locator=dom_locator,
                    metadata={"selector": selector, **structure},
                )
                zones.append(zone)
            except Exception:
                continue

        return zones

    async def extract_zone(self, page: Page, zone_name: str) -> Zone | None:
        """Extract a specific zone by name."""
        selector = self.ZONE_SELECTORS.get(zone_name)
        if not selector:
            return None

        try:
            element = page.locator(selector).first
            if await element.count() == 0:
                return None

            text = await element.inner_text()
            return Zone(
                name=zone_name,
                text=text.strip(),
                dom_locator=f"{selector} >> nth=0",
                metadata={"selector": selector},
            )
        except Exception:
            return None
