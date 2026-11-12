"""Named checks that checkpoint headers reference by name."""

from collections.abc import Callable

from app.checks import page_rules, text_rules
from app.checks.models import CheckInput, Finding

CodeCheck = Callable[[CheckInput], list[Finding] | None]
GateCheck = Callable[[CheckInput], list[str]]

CODE_CHECKS: dict[str, CodeCheck] = {
    "dimension_order": text_rules.dimension_order,
    "inch_notation": text_rules.inch_notation,
    "unit_spacing": text_rules.unit_spacing,
    "decimal_places": text_rules.decimal_places,
    "inch_format_descriptions": text_rules.inch_format_descriptions,
    "metric_only_units": text_rules.metric_only_units,
    "copilot_absent": text_rules.copilot_absent,
    "inch_mm_pairs": text_rules.inch_mm_pairs,
    "peace_of_mind_removed": text_rules.peace_of_mind_removed,
    "tech_specs_list": text_rules.tech_specs_list,
    "broken_links": page_rules.broken_links,
    "broken_media": page_rules.broken_media,
    "en_us_links": page_rules.en_us_links,
}

GATE_CHECKS: dict[str, GateCheck] = {
    "superlative_candidates": text_rules.superlative_candidates,
    "brand_symbol_candidates": text_rules.brand_symbol_candidates,
    "imperial_candidates": text_rules.imperial_candidates,
}
