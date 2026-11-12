"""Inputs and findings shared by deterministic checkpoints and gates."""

from dataclasses import dataclass

from app.acquisition.zone_extractor import Zone
from app.facts.models import PageFacts


@dataclass(frozen=True)
class CheckInput:
    """One zone or page scope with its probed facts."""

    zone: Zone
    facts: PageFacts
    locale: str


@dataclass(frozen=True)
class Finding:
    """One deterministic violation with exact evidence and a locator."""

    problem: str
    evidence: str
    locator: str
    suggestion: str | None = None
