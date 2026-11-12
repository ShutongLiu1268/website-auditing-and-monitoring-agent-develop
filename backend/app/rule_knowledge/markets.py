"""Market matching for declared checkpoint headers."""

from collections.abc import Mapping

COMPLEMENT_GROUPS = frozenset({"NON_IMPERIAL", "NON_ENGLISH"})


class MarketGroups:
    """Named locale groups from the guide, plus the two complement groups."""

    def __init__(self, groups: Mapping[str, tuple[str, ...]]) -> None:
        self._groups = {
            name: frozenset(tag.lower() for tag in tags) for name, tags in groups.items()
        }

    @property
    def names(self) -> frozenset[str]:
        return frozenset(self._groups) | COMPLEMENT_GROUPS

    def matches(self, markets: tuple[str, ...], locale: str) -> bool:
        if not markets or "global" in markets:
            return True
        tag = locale.lower()
        return any(self._token_matches(token, tag) for token in markets)

    def _token_matches(self, token: str, tag: str) -> bool:
        if token == "NON_IMPERIAL":
            return tag not in self._groups.get("IMPERIAL", frozenset())
        if token == "NON_ENGLISH":
            return tag.split("-", 1)[0] != "en"
        if token in self._groups:
            return tag in self._groups[token]
        return token.lower() == tag
