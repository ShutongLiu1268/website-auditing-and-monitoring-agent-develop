"""Deterministic checks over probed links and media load state."""

import re

from app.checks.models import CheckInput, Finding
from app.facts.models import LinkFact

_EN_US_PATH = re.compile(r"/en-us(?=[/?#]|$)", re.IGNORECASE)


def broken_links(check: CheckInput) -> list[Finding] | None:
    """Flag probed links that answered with an error status."""
    probed = [
        link for link in _unique_links(check.facts.links) if link.reachable is not None
    ]
    if not probed:
        return None
    return [
        Finding(
            problem=f"Link is broken (HTTP {link.status_code}).",
            evidence=link.href,
            locator=link.locator,
            suggestion="Fix the link or remove it.",
        )
        for link in probed
        if link.reachable is False
    ]


def broken_media(check: CheckInput) -> list[Finding] | None:
    """Flag video sources that failed to load."""
    if not check.facts.media:
        return None
    return [
        Finding(
            problem="Video failed to load.",
            evidence=media.src,
            locator=media.locator,
            suggestion="Fix the video source or replace the video.",
        )
        for media in check.facts.media
        if media.broken and media.src
    ]


def en_us_links(check: CheckInput) -> list[Finding] | None:
    """Flag en-US links on a non-English page."""
    links = _unique_links(check.facts.links)
    if not links:
        return None
    return [
        Finding(
            problem="EN-US link on a non-English page.",
            evidence=link.href,
            locator=link.locator,
            suggestion="Link to the localized page for this market.",
        )
        for link in links
        if _EN_US_PATH.search(link.href)
    ]


def _unique_links(links: list[LinkFact]) -> list[LinkFact]:
    unique: dict[str, LinkFact] = {}
    for link in links:
        if link.href and link.href not in unique:
            unique[link.href] = link
    return list(unique.values())
