"""Deterministic predicates over zone text, and gates that screen text before the LLM."""

import re
from collections import Counter
from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

from app.acquisition.zone_extractor import Zone
from app.checks.models import CheckInput, Finding

MEASUREMENT_ZONES = frozenset({"dimensions_weight", "tech_specs"})
_ORDER_REQUIRED = "Height, Width, Depth, Weight, Starting weight (if applicable), Max weight (if applicable)"
_INCH_UNIT = r'(?:in\.?|inch(?:es)?|")'
_NUMBER = r"\d+(?:\.\d+)?"

_PRIME_AFTER_NUMBER = re.compile(rf'{_NUMBER}\s*["″“”]')
_IN_ABBREVIATION = re.compile(rf"{_NUMBER}\s*in\b\.?", re.IGNORECASE)
_INCH_WORD_AFTER_NUMBER = re.compile(rf"{_NUMBER}\s+inch(?:es)?\b", re.IGNORECASE)
_IMPERIAL_TOKEN = re.compile(
    rf'{_NUMBER}\s*(?:["″“”]|inch(?:es)?\b|in\b\.?|lbs?\b|pounds?\b)', re.IGNORECASE
)
_UNIT_WITHOUT_SPACE = re.compile(
    rf"(?<![\w.]){_NUMBER}(?:mm|cm|kg|lbs?|GB|TB|MB|GHz|MHz|Wh|mAh|W|Hz|inch|in)\b"
)
_DECIMAL = re.compile(r"(?<![\w.])\d+\.\d+(?!\d|\.\d|K\b)")
_LEADING_DOT = re.compile(r"(?<![\w.])\.\d+")
_PROTOCOL_PREFIX = re.compile(
    r"\b(?:bluetooth|wi-?fi|usb|pcie|hdmi|displayport|thunderbolt|gen|version|v)\s*$",
    re.IGNORECASE,
)
_DIMENSION_LABELS = (
    (0, re.compile(r"\b(?:front\s+|rear\s+)?height(?=\s*[:(\d])", re.IGNORECASE)),
    (1, re.compile(r"\bwidth(?=\s*[:(\d])", re.IGNORECASE)),
    (2, re.compile(r"\bdepth(?=\s*[:(\d])", re.IGNORECASE)),
    (
        3,
        re.compile(
            r"(?<!starting )(?<!lowest )(?<!max )(?<!maximum )\bweight(?=\s*[:(\d])",
            re.IGNORECASE,
        ),
    ),
    (4, re.compile(r"\b(?:starting|lowest)\s+weight(?=\s*[:(\d])", re.IGNORECASE)),
    (5, re.compile(r"\bmax(?:imum)?\s+weight(?=\s*[:(\d])", re.IGNORECASE)),
)
_MM_FIRST_PAIR = re.compile(
    rf"(?P<mm>{_NUMBER})\s*mm\s*\(\s*(?P<inch>{_NUMBER})\s*{_INCH_UNIT}\s*\)",
    re.IGNORECASE,
)
_INCH_FIRST_PAIR = re.compile(
    rf"(?P<inch>{_NUMBER})\s*{_INCH_UNIT}\s*\(\s*(?P<mm>{_NUMBER})\s*mm\s*\)",
    re.IGNORECASE,
)
_VALUE_WITH_UNIT = re.compile(
    rf'{_NUMBER}\s*(?:mm|cm|kg|lbs?|GB|TB|GHz|MHz|Wh|W|in|inch(?:es)?)\b|{_NUMBER}\s*"',
    re.IGNORECASE,
)
_COPILOT = re.compile(r"copilot", re.IGNORECASE)
_PEACE_OF_MIND = re.compile(r"peace of mind", re.IGNORECASE)
_SUPERLATIVE_WORDS = "|".join(
    (
        "most",
        "best",
        "thinnest",
        "lightest",
        "fastest",
        "greatest",
        "largest",
        "biggest",
        "smallest",
        "lowest",
        "highest",
        "ultimate",
        "unmatched",
        "unrivall?ed",
        "unbeatable",
        "leading",
        "premier",
        "finest",
    )
)
_SUPERLATIVE = re.compile(
    rf"\b(?:{_SUPERLATIVE_WORDS}|world[’']?s)\b|#1|\bnumber one\b", re.IGNORECASE
)
_BRANDS = (
    ("Intel", "®"),
    ("vPro", "®"),
    ("NVIDIA", "®"),
    ("Qualcomm", "®"),
    ("Core", "™"),
    ("Arc", "™"),
    ("GeForce RTX", "™"),
    ("Ryzen", "™"),
    ("Adreno", "™"),
)
_BRAND_WITHOUT_SYMBOL = tuple(
    re.compile(rf"\b{re.escape(brand)}\b(?!{re.escape(symbol)})")
    for brand, symbol in _BRANDS
)


def dimension_order(check: CheckInput) -> list[Finding] | None:
    """Flag dimension labels whose first occurrences break the required order."""
    text = check.zone.text
    first_by_rank: dict[int, re.Match[str]] = {}
    for rank, pattern in _DIMENSION_LABELS:
        for match in pattern.finditer(text):
            if rank not in first_by_rank or match.start() < first_by_rank[rank].start():
                first_by_rank[rank] = match
    ordered = sorted(first_by_rank.items(), key=lambda item: item[1].start())
    if len(ordered) < 2:
        return None
    highest = -1
    for rank, match in ordered:
        if rank < highest:
            return [
                Finding(
                    problem=f"'{match.group(0)}' appears out of order. Required order: {_ORDER_REQUIRED}.",
                    evidence=match.group(0),
                    locator=check.zone.dom_locator,
                    suggestion=f"Reorder the dimensions and weight: {_ORDER_REQUIRED}.",
                )
            ]
        highest = rank
    return []


def inch_notation(check: CheckInput) -> list[Finding] | None:
    """Flag inch quote marks everywhere and 'in.' outside the dimensions zone."""
    text = check.zone.text
    if not text:
        return None
    matches = [match.group(0) for match in _PRIME_AFTER_NUMBER.finditer(text)]
    if check.zone.name != "dimensions_weight":
        matches += [match.group(0) for match in _IN_ABBREVIATION.finditer(text)]
    return _findings(
        check.zone,
        matches,
        "Spell out inch for measurements and do not use the quote mark.",
        "Write the measurement with 'inch', for example 14-inch.",
    )


def unit_spacing(check: CheckInput) -> list[Finding] | None:
    """Flag values written directly against their unit."""
    text = check.zone.text
    if not text:
        return None
    return _findings(
        check.zone,
        (match.group(0) for match in _UNIT_WITHOUT_SPACE.finditer(text)),
        "Add a space between the value and its unit.",
        "Insert one space between the number and the unit.",
    )


def decimal_places(check: CheckInput) -> list[Finding] | None:
    """Flag decimals that are not two places and decimals missing a leading zero."""
    text = check.zone.text
    if not text:
        return None
    wrong_places = [
        match.group(0)
        for match in _DECIMAL.finditer(text)
        if len(match.group(0).split(".")[1]) != 2
        and not _is_protocol_version(text, match.start())
    ]
    missing_zero = [match.group(0) for match in _LEADING_DOT.finditer(text)]
    return _findings(
        check.zone,
        wrong_places,
        "Round the value to two decimal places.",
        "Use two decimal places, for example 2.50.",
    ) + _findings(
        check.zone,
        missing_zero,
        "Add a leading zero to values below 1.00.",
        "Write the value with a leading zero, for example 0.50.",
    )


def inch_format_descriptions(check: CheckInput) -> list[Finding] | None:
    """Flag inch notation that breaks the -inch rule in product descriptions."""
    if check.zone.name in MEASUREMENT_ZONES:
        return None
    text = check.zone.text
    if not text:
        return None
    matches = [match.group(0) for match in _INCH_WORD_AFTER_NUMBER.finditer(text)]
    matches += [match.group(0) for match in _IN_ABBREVIATION.finditer(text)]
    matches += [match.group(0) for match in _PRIME_AFTER_NUMBER.finditer(text)]
    return _findings(
        check.zone,
        matches,
        "Use the -inch form in product descriptions, without 'in' or a prime symbol.",
        "Write the size as N-inch, for example 14-inch.",
    )


def metric_only_units(check: CheckInput) -> list[Finding] | None:
    """Flag inch and pound values on content that must show kg and mm only."""
    text = check.zone.text
    if not text:
        return None
    return _findings(
        check.zone,
        (match.group(0) for match in _IMPERIAL_TOKEN.finditer(text)),
        "This market shows kg and mm only; remove inch and pound values.",
        "Remove the inch or pound value and keep kg and mm.",
    )


def copilot_absent(check: CheckInput) -> list[Finding] | None:
    """Flag any Copilot reference in China content."""
    text = check.zone.text
    if not text:
        return None
    return _findings(
        check.zone,
        (match.group(0) for match in _COPILOT.finditer(text)),
        "Copilot references are not allowed in China content.",
        "Remove the Copilot reference.",
    )


def inch_mm_pairs(check: CheckInput) -> list[Finding] | None:
    """Flag inch and millimetre pairs that do not convert at 1 in = 25.4 mm."""
    text = check.zone.text
    pairs = sorted(
        [*_MM_FIRST_PAIR.finditer(text), *_INCH_FIRST_PAIR.finditer(text)],
        key=lambda match: match.start(),
    )
    if not pairs:
        return None
    findings: list[Finding] = []
    for match in pairs:
        mm, inch = match.group("mm"), match.group("inch")
        expected = _expected_inch(mm, inch)
        if expected is None:
            continue
        suggestion = (
            f"{mm} mm ({expected} in)"
            if match.re is _MM_FIRST_PAIR
            else f"{expected} in ({mm} mm)"
        )
        findings.append(
            Finding(
                problem=f"{inch} in does not match {mm} mm; 1 in = 25.4 mm gives {expected} in.",
                evidence=match.group(0),
                locator=check.zone.dom_locator,
                suggestion=suggestion,
            )
        )
    return findings


def peace_of_mind_removed(check: CheckInput) -> list[Finding] | None:
    """Flag the Peace of Mind module, which APJC pages must not show."""
    text = check.zone.text
    if not text:
        return None
    return _findings(
        check.zone,
        (match.group(0) for match in _PEACE_OF_MIND.finditer(text)),
        "The Peace of Mind module must be removed for APJC.",
        "Remove the Peace of Mind module.",
    )


def tech_specs_list(check: CheckInput) -> list[Finding] | None:
    """Flag tech specs that show several unit values in a paragraph instead of a list."""
    text = check.zone.text
    if "list_items" not in check.zone.metadata or not text:
        return None
    values = list(_VALUE_WITH_UNIT.finditer(text))
    if len(values) < 2:
        return None
    if check.zone.metadata["list_items"]:
        return []
    start = values[0].start()
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    line = text[line_start : len(text) if line_end == -1 else line_end].strip()
    return [
        Finding(
            problem="Tech specs values are written as a paragraph, not a list.",
            evidence=line,
            locator=check.zone.dom_locator,
            suggestion="Show each specification value as its own list item.",
        )
    ]


def superlative_candidates(check: CheckInput) -> list[str]:
    """Return superlative words that a superlative claim must contain."""
    return _distinct(match.group(0) for match in _SUPERLATIVE.finditer(check.zone.text))


def brand_symbol_candidates(check: CheckInput) -> list[str]:
    """Return brand mentions that lack their required trademark symbol."""
    return _distinct(
        match.group(0)
        for pattern in _BRAND_WITHOUT_SYMBOL
        for match in pattern.finditer(check.zone.text)
    )


def imperial_candidates(check: CheckInput) -> list[str]:
    """Return inch and pound values that a non-imperial market must localize."""
    return _distinct(
        match.group(0) for match in _IMPERIAL_TOKEN.finditer(check.zone.text)
    )


def _findings(
    zone: Zone,
    matches: Iterable[str],
    problem: str,
    suggestion: str,
) -> list[Finding]:
    return [
        Finding(
            problem=problem if count == 1 else f"{problem} Found {count} times.",
            evidence=evidence,
            locator=zone.dom_locator,
            suggestion=suggestion,
        )
        for evidence, count in Counter(matches).items()
    ]


def _distinct(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _is_protocol_version(text: str, start: int) -> bool:
    return _PROTOCOL_PREFIX.search(text[max(0, start - 20) : start]) is not None


def _expected_inch(mm: str, inch: str) -> str | None:
    decimals = len(inch.split(".")[1]) if "." in inch else 0
    expected = (Decimal(mm) / Decimal("25.4")).quantize(
        Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP
    )
    return None if expected == Decimal(inch) else str(expected)
