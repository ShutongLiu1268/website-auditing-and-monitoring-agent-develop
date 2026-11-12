"""
Deterministic fact tools: unit parsing and conversion.
"""

import re


class UnitParser:
    """Parse and convert dimension/weight units."""

    IMPERIAL_LENGTH: re.Pattern[str] = re.compile(
        r"(\d+\.?\d*)\s*(?:inches?|in|\"|')", re.IGNORECASE
    )
    METRIC_LENGTH: re.Pattern[str] = re.compile(
        r"(\d+\.?\d*)\s*(?:mm|millimeters?)", re.IGNORECASE
    )
    IMPERIAL_WEIGHT: re.Pattern[str] = re.compile(
        r"(\d+\.?\d*)\s*(?:lb|pounds?)", re.IGNORECASE
    )
    METRIC_WEIGHT: re.Pattern[str] = re.compile(
        r"(\d+\.?\d*)\s*(?:kg|kilograms?)", re.IGNORECASE
    )

    @staticmethod
    def parse_length(text: str) -> tuple[float, str] | None:
        """Parse length value and unit from text."""
        match = UnitParser.METRIC_LENGTH.search(text)
        if match:
            return float(match.group(1)), "mm"

        match = UnitParser.IMPERIAL_LENGTH.search(text)
        if match:
            return float(match.group(1)), "in"

        return None

    @staticmethod
    def parse_weight(text: str) -> tuple[float, str] | None:
        """Parse weight value and unit from text."""
        match = UnitParser.METRIC_WEIGHT.search(text)
        if match:
            return float(match.group(1)), "kg"

        match = UnitParser.IMPERIAL_WEIGHT.search(text)
        if match:
            return float(match.group(1)), "lb"

        return None

    @staticmethod
    def inches_to_mm(inches: float) -> float:
        """Convert inches to millimeters."""
        return inches * 25.4

    @staticmethod
    def mm_to_inches(mm: float) -> float:
        """Convert millimeters to inches."""
        return mm / 25.4

    @staticmethod
    def lb_to_kg(lb: float) -> float:
        """Convert pounds to kilograms."""
        return lb * 0.453592

    @staticmethod
    def kg_to_lb(kg: float) -> float:
        """Convert kilograms to pounds."""
        return kg / 0.453592

    @staticmethod
    def are_close(value1: float, value2: float, tolerance: float = 0.01) -> bool:
        """Check if two values are close within tolerance."""
        return abs(value1 - value2) <= tolerance
