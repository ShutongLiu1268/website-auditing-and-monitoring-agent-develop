"""Select checkpoints for one profile, locale, and page zone."""

from collections.abc import Sequence

from app.acquisition.zone_extractor import PAGE_ZONE
from app.domain.models import AuditMode, RulePassage
from app.rule_knowledge.markets import MarketGroups


class RuleSelector:
    """Return the checkpoints that apply to one audit context."""

    def __init__(self, passages: Sequence[RulePassage], groups: MarketGroups) -> None:
        self._passages = tuple(passages)
        self._groups = groups

    def select(self, profile: AuditMode, locale: str, zone: str) -> list[RulePassage]:
        return [
            passage
            for passage in self._passages
            if profile in passage.modes
            and self._groups.matches(tuple(passage.markets), locale)
            and _zone_applies(passage.zones, zone)
        ]


def _zone_applies(declared: Sequence[str], zone: str) -> bool:
    if zone == PAGE_ZONE:
        return PAGE_ZONE in declared
    return PAGE_ZONE not in declared and (not declared or zone in declared)
