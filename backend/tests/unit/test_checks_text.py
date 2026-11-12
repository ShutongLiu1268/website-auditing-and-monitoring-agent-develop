from app.acquisition.zone_extractor import Zone
from app.checks.models import CheckInput
from app.checks.text_rules import (
    brand_symbol_candidates,
    copilot_absent,
    decimal_places,
    dimension_order,
    imperial_candidates,
    inch_format_descriptions,
    inch_mm_pairs,
    inch_notation,
    metric_only_units,
    peace_of_mind_removed,
    superlative_candidates,
    tech_specs_list,
    unit_spacing,
)
from app.facts.models import PageFacts


def _check(
    text: str, zone: str = "features", metadata: dict | None = None
) -> CheckInput:
    return CheckInput(
        zone=Zone(
            name=zone, text=text, dom_locator=f".{zone}", metadata=metadata or {}
        ),
        facts=PageFacts(),
        locale="en-US",
    )


def _evidence(findings: list) -> list[str]:
    return [finding.evidence for finding in findings]


class TestDimensionOrder:
    def test_required_order_passes(self):
        # Arrange
        check = _check(
            "Height: 18.00 mm\nWidth: 344.72 mm\nDepth: 230.14 mm\nWeight: 2.05 kg",
            "dimensions_weight",
        )

        # Act
        findings = dimension_order(check)

        # Assert
        assert findings == []

    def test_width_before_height_is_issue(self):
        # Arrange
        check = _check("Width: 344.72 mm\nHeight: 18.00 mm", "dimensions_weight")

        # Act
        findings = dimension_order(check)

        # Assert
        assert _evidence(findings) == ["Height"]

    def test_heading_word_weight_is_not_a_label(self):
        # Arrange
        check = _check(
            "Dimensions and weight\nHeight: 18.00 mm\nWidth: 344.72 mm",
            "dimensions_weight",
        )

        # Act
        findings = dimension_order(check)

        # Assert
        assert findings == []

    def test_starting_weight_after_weight_passes(self):
        # Arrange
        check = _check(
            "Height: 18 mm\nWidth: 3 mm\nDepth: 2 mm\nWeight: 2.05 kg\nStarting weight: 1.90 kg",
            "dimensions_weight",
        )

        # Act
        findings = dimension_order(check)

        # Assert
        assert findings == []

    def test_repeated_blocks_keep_first_order(self):
        # Arrange
        check = _check(
            "Height: 1 mm\nWidth: 2 mm\nHeight: 3 mm\nWidth: 4 mm", "dimensions_weight"
        )

        # Act
        findings = dimension_order(check)

        # Assert
        assert findings == []

    def test_single_label_is_not_applicable(self):
        # Arrange
        check = _check("Height: 18.00 mm", "dimensions_weight")

        # Act
        findings = dimension_order(check)

        # Assert
        assert findings is None


class TestInchNotation:
    def test_quote_mark_after_number_is_issue(self):
        # Arrange
        check = _check('Screen 14" panel')

        # Act
        findings = inch_notation(check)

        # Assert
        assert _evidence(findings) == ['14"']

    def test_in_abbreviation_outside_dimensions_is_issue(self):
        # Arrange
        check = _check("Screen 14 in. panel")

        # Act
        findings = inch_notation(check)

        # Assert
        assert _evidence(findings) == ["14 in."]

    def test_in_abbreviation_allowed_in_dimensions_zone(self):
        # Arrange
        check = _check("18.00 mm (0.71 in.)", "dimensions_weight")

        # Act
        findings = inch_notation(check)

        # Assert
        assert findings == []

    def test_spelled_out_inch_passes(self):
        # Arrange
        check = _check("14-inch display")

        # Act
        findings = inch_notation(check)

        # Assert
        assert findings == []

    def test_empty_zone_is_not_applicable(self):
        # Arrange
        check = _check("")

        # Act
        findings = inch_notation(check)

        # Assert
        assert findings is None


class TestUnitSpacing:
    def test_value_unit_without_space_is_issue(self):
        # Arrange
        check = _check("Battery 65W, RAM 16GB, Screen 396mm")

        # Act
        findings = unit_spacing(check)

        # Assert
        assert _evidence(findings) == ["65W", "16GB", "396mm"]

    def test_spaced_units_pass(self):
        # Arrange
        check = _check("RAM 16 GB, Screen 396 mm")

        # Act
        findings = unit_spacing(check)

        # Assert
        assert findings == []


class TestDecimalPlaces:
    def test_one_decimal_is_issue(self):
        # Arrange
        check = _check("Weight 2.5 kg")

        # Act
        findings = decimal_places(check)

        # Assert
        assert _evidence(findings) == ["2.5"]

    def test_two_decimals_pass(self):
        # Arrange
        check = _check("Weight 2.05 kg")

        # Act
        findings = decimal_places(check)

        # Assert
        assert findings == []

    def test_display_resolution_is_skipped(self):
        # Arrange
        check = _check("14-inch 2.5K display")

        # Act
        findings = decimal_places(check)

        # Assert
        assert findings == []

    def test_missing_leading_zero_is_issue(self):
        # Arrange
        check = _check("Thickness .50 mm")

        # Act
        findings = decimal_places(check)

        # Assert
        assert _evidence(findings) == [".50"]

    def test_protocol_versions_are_skipped(self):
        # Arrange
        check = _check("Bluetooth 5.3 and Wi-Fi 6.0 support")

        # Act
        findings = decimal_places(check)

        # Assert
        assert findings == []

    def test_three_part_version_numbers_are_skipped(self):
        # Arrange
        check = _check("Firmware version 1.2.3 installed")

        # Act
        findings = decimal_places(check)

        # Assert
        assert findings == []


class TestInchFormatDescriptions:
    def test_space_separated_inch_is_issue(self):
        # Arrange
        check = _check("Enjoy the 14 inch display")

        # Act
        findings = inch_format_descriptions(check)

        # Assert
        assert _evidence(findings) == ["14 inch"]

    def test_hyphenated_inch_passes(self):
        # Arrange
        check = _check("Enjoy the 14-inch display")

        # Act
        findings = inch_format_descriptions(check)

        # Assert
        assert findings == []

    def test_prime_symbol_is_issue(self):
        # Arrange
        check = _check('Display 14"')

        # Act
        findings = inch_format_descriptions(check)

        # Assert
        assert _evidence(findings) == ['14"']

    def test_measurement_zone_is_not_applicable(self):
        # Arrange
        check = _check("Width 13.57 in", "dimensions_weight")

        # Act
        findings = inch_format_descriptions(check)

        # Assert
        assert findings is None


class TestMetricOnlyUnits:
    def test_inch_and_pounds_are_issues(self):
        # Arrange
        check = _check("Width 13.57 in\nWeight 4.50 lb", "dimensions_weight")

        # Act
        findings = metric_only_units(check)

        # Assert
        assert _evidence(findings) == ["13.57 in", "4.50 lb"]

    def test_metric_only_passes(self):
        # Arrange
        check = _check("Width 344.72 mm\nWeight 2.05 kg", "dimensions_weight")

        # Act
        findings = metric_only_units(check)

        # Assert
        assert findings == []


class TestCopilotAbsent:
    def test_copilot_in_any_case_is_issue(self):
        # Arrange
        check = _check("Try Copilot and copilot+ PC")

        # Act
        findings = copilot_absent(check)

        # Assert
        assert _evidence(findings) == ["Copilot", "copilot"]

    def test_page_without_copilot_passes(self):
        # Arrange
        check = _check("Laptop with a 14-inch display")

        # Act
        findings = copilot_absent(check)

        # Assert
        assert findings == []


class TestInchMmPairs:
    def test_matching_mm_first_pair_passes(self):
        # Arrange
        check = _check('344.72 mm (13.57")', "dimensions_weight")

        # Act
        findings = inch_mm_pairs(check)

        # Assert
        assert findings == []

    def test_mismatched_mm_first_pair_is_issue(self):
        # Arrange
        check = _check('344.72 mm (13.60")', "dimensions_weight")

        # Act
        findings = inch_mm_pairs(check)

        # Assert
        assert _evidence(findings) == ['344.72 mm (13.60")']

    def test_matching_inch_first_pair_passes(self):
        # Arrange
        check = _check("13.57 in (344.72 mm)", "dimensions_weight")

        # Act
        findings = inch_mm_pairs(check)

        # Assert
        assert findings == []

    def test_one_decimal_inch_uses_one_decimal_rounding(self):
        # Arrange
        check = _check("320 mm (12.6 in)", "dimensions_weight")

        # Act
        findings = inch_mm_pairs(check)

        # Assert
        assert findings == []

    def test_text_without_pairs_is_not_applicable(self):
        # Arrange
        check = _check("Width 344.72 mm", "dimensions_weight")

        # Act
        findings = inch_mm_pairs(check)

        # Assert
        assert findings is None


class TestPeaceOfMindRemoved:
    def test_module_text_is_issue(self):
        # Arrange
        check = _check("Peace of Mind protection included", "features")

        # Act
        findings = peace_of_mind_removed(check)

        # Assert
        assert _evidence(findings) == ["Peace of Mind"]

    def test_absent_module_passes(self):
        # Arrange
        check = _check("Accidental damage protection", "support")

        # Act
        findings = peace_of_mind_removed(check)

        # Assert
        assert findings == []


class TestTechSpecsList:
    def test_paragraph_values_are_issue(self):
        # Arrange
        check = _check(
            "Memory: 16 GB, storage: 512 GB, weight: 1.5 kg",
            "tech_specs",
            {"list_items": 0},
        )

        # Act
        findings = tech_specs_list(check)

        # Assert
        assert _evidence(findings) == ["Memory: 16 GB, storage: 512 GB, weight: 1.5 kg"]

    def test_list_items_pass(self):
        # Arrange
        check = _check("Memory 16 GB\nStorage 512 GB", "tech_specs", {"list_items": 4})

        # Act
        findings = tech_specs_list(check)

        # Assert
        assert findings == []

    def test_missing_structure_metadata_is_not_applicable(self):
        # Arrange
        check = _check("Memory: 16 GB, storage: 512 GB", "tech_specs")

        # Act
        findings = tech_specs_list(check)

        # Assert
        assert findings is None

    def test_single_value_is_not_applicable(self):
        # Arrange
        check = _check("Memory 16 GB", "tech_specs", {"list_items": 0})

        # Act
        findings = tech_specs_list(check)

        # Assert
        assert findings is None


class TestSuperlativeCandidates:
    def test_superlatives_are_candidates_in_order(self):
        # Arrange
        check = _check("The thinnest and most powerful laptop")

        # Act
        candidates = superlative_candidates(check)

        # Assert
        assert candidates == ["thinnest", "most"]

    def test_plain_copy_has_no_candidates(self):
        # Arrange
        check = _check("Affordable laptop for students")

        # Act
        candidates = superlative_candidates(check)

        # Assert
        assert candidates == []


class TestBrandSymbolCandidates:
    def test_brands_without_required_symbol_are_candidates(self):
        # Arrange
        check = _check("Intel Core i7 with NVIDIA® graphics")

        # Act
        candidates = brand_symbol_candidates(check)

        # Assert
        assert candidates == ["Intel", "Core"]

    def test_brands_with_required_symbols_are_not_candidates(self):
        # Arrange
        check = _check("Intel® Core™ Ultra with Ryzen™ graphics")

        # Act
        candidates = brand_symbol_candidates(check)

        # Assert
        assert candidates == []


class TestImperialCandidates:
    def test_imperial_tokens_are_candidates(self):
        # Arrange
        check = _check('Screen 14 inch, weight 4.5 lb, panel 13.57"')

        # Act
        candidates = imperial_candidates(check)

        # Assert
        assert candidates == ["14 inch", "4.5 lb", '13.57"']

    def test_metric_only_copy_has_no_candidates(self):
        # Arrange
        check = _check("Screen 396 mm, weight 2.05 kg")

        # Act
        candidates = imperial_candidates(check)

        # Assert
        assert candidates == []
