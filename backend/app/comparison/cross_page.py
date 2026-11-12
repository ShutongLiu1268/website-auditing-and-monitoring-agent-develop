from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from app.domain.models import PageSnapshot

FieldCategory = Literal["invariant", "market_sensitive"]
FieldStatus = Literal["consistent", "actionable", "expected"]

FIELD_DEFINITIONS: tuple[tuple[str, str, FieldCategory], ...] = (
    ("model_code", "Model code", "invariant"),
    ("memory", "Memory", "invariant"),
    ("storage", "Storage", "invariant"),
    ("price", "Price", "market_sensitive"),
    ("keyboard", "Keyboard", "market_sensitive"),
)


@dataclass(frozen=True)
class PageValue:
    locale: str
    url: str
    value: str | None


@dataclass(frozen=True)
class CrossPageField:
    key: str
    label: str
    category: FieldCategory
    status: FieldStatus
    values: tuple[PageValue, ...]


def compare_pages(snapshots: Sequence[PageSnapshot]) -> list[CrossPageField]:
    if len(snapshots) < 2:
        return []
    comparisons: list[CrossPageField] = []
    for key, label, category in FIELD_DEFINITIONS:
        values = tuple(
            PageValue(snapshot.locale, snapshot.url, snapshot.product_fields.get(key))
            for snapshot in snapshots
        )
        if all(item.value is None for item in values):
            continue
        distinct = {_normalize(item.value) for item in values}
        comparisons.append(
            CrossPageField(key, label, category, _status(category, distinct), values)
        )
    return comparisons


def _normalize(value: str | None) -> str | None:
    return None if value is None else " ".join(value.lower().split())


def _status(category: FieldCategory, distinct: set[str | None]) -> FieldStatus:
    if len(distinct) == 1:
        return "consistent"
    return "actionable" if category == "invariant" else "expected"
