"""Declared checkpoint headers and market groups for the bundled guide."""

import re
from dataclasses import dataclass

from app.acquisition.zone_extractor import PAGE_ZONE, ZoneExtractor
from app.checks.registry import CODE_CHECKS, GATE_CHECKS
from app.domain.models import AuditMode, RuleEvaluatorType
from app.rule_knowledge.markets import COMPLEMENT_GROUPS

KNOWN_ZONES = frozenset({*ZoneExtractor.ZONE_SELECTORS, PAGE_ZONE})
REQUIRED_KEYS = ("id", "profiles", "markets", "zones", "evaluator", "review")
REVIEW_VALUES = frozenset({"never", "always"})
LOCALE_TAG = re.compile(r"^[a-z]{2,3}-[a-z]{2}$", re.IGNORECASE)


class CheckpointHeaderError(ValueError):
    """Raised when a checkpoint header or market group is invalid."""


@dataclass(frozen=True)
class CheckpointHeader:
    id: str
    profiles: tuple[AuditMode, ...]
    markets: tuple[str, ...]
    zones: tuple[str, ...]
    evaluator: RuleEvaluatorType
    check: str | None
    review: str
    reminder: str | None
    topics: tuple[str, ...]


def build_header(block: str, group_names: frozenset[str]) -> CheckpointHeader:
    values = _parse_key_values(block)
    missing = [key for key in REQUIRED_KEYS if key not in values]
    if missing:
        raise CheckpointHeaderError(f"{values.get('id', '?')}: missing keys {missing}")
    checkpoint_id = values["id"]
    try:
        profiles = tuple(AuditMode(item) for item in _split(values["profiles"]))
        evaluator = RuleEvaluatorType(values["evaluator"])
    except ValueError as exc:
        raise CheckpointHeaderError(f"{checkpoint_id}: {exc}") from exc
    markets = tuple(_split(values["markets"]))
    if not profiles or not markets:
        raise CheckpointHeaderError(f"{checkpoint_id}: profiles and markets must not be empty")
    for token in markets:
        if token != "global" and token not in group_names and not LOCALE_TAG.match(token):
            raise CheckpointHeaderError(f"{checkpoint_id}: unknown market {token}")
    zones = () if values["zones"] == "all" else tuple(_split(values["zones"]))
    unknown_zones = sorted(set(zones) - KNOWN_ZONES)
    if unknown_zones:
        raise CheckpointHeaderError(f"{checkpoint_id}: unknown zones {unknown_zones}")
    check = values.get("check") or None
    _validate_check(checkpoint_id, evaluator, check, zones)
    review = values["review"]
    if review not in REVIEW_VALUES and not LOCALE_TAG.match(review):
        raise CheckpointHeaderError(f"{checkpoint_id}: invalid review {review}")
    return CheckpointHeader(
        id=checkpoint_id,
        profiles=profiles,
        markets=markets,
        zones=zones,
        evaluator=evaluator,
        check=check,
        review=review,
        reminder=values.get("reminder") or None,
        topics=tuple(_split(values.get("topics", ""))),
    )


def parse_market_groups(block: str) -> dict[str, tuple[str, ...]]:
    groups: dict[str, tuple[str, ...]] = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        name, separator, value = line.partition(":")
        name = name.strip()
        if not separator or name in groups:
            raise CheckpointHeaderError(f"invalid or duplicate market group: {line!r}")
        if name in COMPLEMENT_GROUPS:
            groups[name] = ()
            continue
        tags = tuple(_split(value))
        bad = [tag for tag in tags if not LOCALE_TAG.match(tag)]
        if bad:
            raise CheckpointHeaderError(f"group {name} has non-locale entries {bad}")
        groups[name] = tags
    return groups


def _validate_check(
    checkpoint_id: str,
    evaluator: RuleEvaluatorType,
    check: str | None,
    zones: tuple[str, ...],
) -> None:
    if PAGE_ZONE in zones and (zones != (PAGE_ZONE,) or evaluator != RuleEvaluatorType.CODE):
        raise CheckpointHeaderError(
            f"{checkpoint_id}: page scope needs zones: page alone and evaluator: code"
        )
    if evaluator == RuleEvaluatorType.LLM and check is not None:
        raise CheckpointHeaderError(f"{checkpoint_id}: llm checkpoint takes no check")
    if evaluator == RuleEvaluatorType.CODE and (check is None or check not in CODE_CHECKS):
        raise CheckpointHeaderError(
            f"{checkpoint_id}: code checkpoint needs a registered code check, got {check}"
        )
    if evaluator == RuleEvaluatorType.HYBRID and (check is None or check not in GATE_CHECKS):
        raise CheckpointHeaderError(
            f"{checkpoint_id}: hybrid checkpoint needs a registered gate check, got {check}"
        )


def _parse_key_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise CheckpointHeaderError(f"header line has no key: {line!r}")
        values[key.strip()] = value.strip()
    return values


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
