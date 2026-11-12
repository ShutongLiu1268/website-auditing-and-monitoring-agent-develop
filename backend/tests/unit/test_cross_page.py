from app.comparison.cross_page import compare_pages
from app.domain.models import PageSnapshot


def _page(locale: str, **product_fields: str) -> PageSnapshot:
    return PageSnapshot(
        id=f"run-1:{locale}",
        run_id="run-1",
        url=f"https://www.dell.com/{locale}/shop/laptops",
        locale=locale,
        content_hash="hash",
        extraction_version="fixture-0.1.0",
        product_fields=product_fields,
    )


def _fields_by_key(pages: list[PageSnapshot]):
    return {field.key: field for field in compare_pages(pages)}


def test_invariant_mismatch_is_actionable():
    fields = _fields_by_key([_page("en-ca", memory="16 GB"), _page("fr-ca", memory="8 GB")])

    assert fields["memory"].status == "actionable"
    assert fields["memory"].category == "invariant"
    assert [value.value for value in fields["memory"].values] == ["16 GB", "8 GB"]


def test_market_sensitive_mismatch_is_expected():
    fields = _fields_by_key(
        [_page("en-us", price="US$1,299.00"), _page("en-ca", price="CA$1,449.00")]
    )

    assert fields["price"].status == "expected"
    assert fields["price"].category == "market_sensitive"


def test_matching_values_ignore_case_and_spacing():
    fields = _fields_by_key([_page("en-ca", memory="16 GB"), _page("en-us", memory=" 16  gb ")])

    assert fields["memory"].status == "consistent"


def test_invariant_missing_on_one_page_is_actionable():
    fields = _fields_by_key([_page("en-ca", storage="512 GB"), _page("fr-ca")])

    assert fields["storage"].status == "actionable"
    assert fields["storage"].values[1].value is None


def test_fields_missing_on_every_page_are_omitted():
    fields = _fields_by_key([_page("en-ca", memory="16 GB"), _page("en-us", memory="16 GB")])

    assert "price" not in fields


def test_single_page_has_nothing_to_compare():
    assert compare_pages([_page("en-ca", memory="16 GB")]) == []
