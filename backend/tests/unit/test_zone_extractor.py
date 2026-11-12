"""Unit tests for zone extractor."""

import pytest
from pytest_mock import MockerFixture

from app.acquisition.zone_extractor import ZoneExtractor


def test_zone_extractor_has_zone_selectors():
    """Test that extractor has zone selectors defined."""
    extractor = ZoneExtractor()
    assert len(extractor.ZONE_SELECTORS) > 0
    assert "hero" in extractor.ZONE_SELECTORS
    assert "tech_specs" in extractor.ZONE_SELECTORS
    assert "dimensions_weight" in extractor.ZONE_SELECTORS


@pytest.mark.asyncio
async def test_extract_records_list_item_count(mocker: MockerFixture):
    """Test zones record how many list items or table rows they contain."""
    element = mocker.Mock(
        count=mocker.AsyncMock(return_value=1),
        inner_text=mocker.AsyncMock(return_value=" Memory 16 GB "),
        evaluate=mocker.AsyncMock(return_value={"list_items": 3}),
    )
    page = mocker.Mock(locator=mocker.Mock(return_value=mocker.Mock(first=element)))

    zones = await ZoneExtractor().extract(page)

    tech_specs = next(zone for zone in zones if zone.name == "tech_specs")
    assert tech_specs.text == "Memory 16 GB"
    assert tech_specs.metadata["list_items"] == 3
