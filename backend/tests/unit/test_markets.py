from app.rule_knowledge.markets import MarketGroups

GROUPS = MarketGroups(
    {
        "EMEA": ("en-GB", "fr-FR", "de-DE"),
        "IMPERIAL": ("en-US", "en-CA", "fr-CA"),
        "NON_IMPERIAL": (),
        "NON_ENGLISH": (),
    }
)


def test_global_matches_every_locale():
    assert GROUPS.matches(("global",), "ja-JP")


def test_empty_markets_matches_every_locale():
    assert GROUPS.matches((), "ja-JP")


def test_locale_tag_matches_case_insensitively():
    assert GROUPS.matches(("en-US",), "EN-us")
    assert not GROUPS.matches(("en-US",), "en-CA")


def test_group_name_expands_to_its_locales():
    assert GROUPS.matches(("EMEA",), "fr-FR")
    assert not GROUPS.matches(("EMEA",), "en-US")


def test_imperial_group_is_exact():
    assert GROUPS.matches(("IMPERIAL",), "fr-CA")
    assert not GROUPS.matches(("IMPERIAL",), "fr-FR")


def test_non_imperial_is_the_complement_of_imperial():
    assert GROUPS.matches(("NON_IMPERIAL",), "fr-FR")
    assert not GROUPS.matches(("NON_IMPERIAL",), "en-US")


def test_non_english_excludes_every_english_locale():
    assert GROUPS.matches(("NON_ENGLISH",), "de-DE")
    assert not GROUPS.matches(("NON_ENGLISH",), "en-GB")


def test_names_include_groups_and_complement_groups():
    assert {"EMEA", "NON_IMPERIAL", "NON_ENGLISH"} <= GROUPS.names
