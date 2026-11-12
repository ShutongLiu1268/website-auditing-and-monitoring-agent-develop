"""
Unit tests for deterministic fact tools.
"""

import pytest

from app.tools.units import UnitParser


def test_parse_length_metric():
    """Test parsing metric length."""
    result = UnitParser.parse_length("396 mm")
    assert result == (396.0, "mm")

    result = UnitParser.parse_length("15.6 mm")
    assert result == (15.6, "mm")


def test_parse_length_imperial():
    """Test parsing imperial length."""
    result = UnitParser.parse_length("15.6 inches")
    assert result == (15.6, "in")

    result = UnitParser.parse_length('15.6"')
    assert result == (15.6, "in")


def test_parse_weight_metric():
    """Test parsing metric weight."""
    result = UnitParser.parse_weight("1.98 kg")
    assert result == (1.98, "kg")


def test_parse_weight_imperial():
    """Test parsing imperial weight."""
    result = UnitParser.parse_weight("4.37 lb")
    assert result == (4.37, "lb")


def test_inches_to_mm():
    """Test inches to millimeters conversion."""
    assert UnitParser.inches_to_mm(1.0) == 25.4
    assert UnitParser.inches_to_mm(15.6) == pytest.approx(396.24, abs=0.01)


def test_mm_to_inches():
    """Test millimeters to inches conversion."""
    assert UnitParser.mm_to_inches(25.4) == pytest.approx(1.0, abs=0.01)
    assert UnitParser.mm_to_inches(396.24) == pytest.approx(15.6, abs=0.01)


def test_lb_to_kg():
    """Test pounds to kilograms conversion."""
    assert UnitParser.lb_to_kg(1.0) == pytest.approx(0.453592, abs=0.001)
    assert UnitParser.lb_to_kg(4.37) == pytest.approx(1.984, abs=0.01)


def test_kg_to_lb():
    """Test kilograms to pounds conversion."""
    assert UnitParser.kg_to_lb(1.0) == pytest.approx(2.20462, abs=0.01)
    assert UnitParser.kg_to_lb(1.98) == pytest.approx(4.365, abs=0.01)


def test_are_close():
    """Test value comparison with tolerance."""
    assert UnitParser.are_close(1.0, 1.0) is True
    assert UnitParser.are_close(1.0, 1.005) is True
    assert UnitParser.are_close(1.0, 1.02) is False
