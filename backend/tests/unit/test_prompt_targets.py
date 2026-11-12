from app.conversation.parser import extract_prompt_targets


def test_takes_locale_from_url_path():
    result = extract_prompt_targets(
        "Audit https://www.dell.com/en-ca/shop/laptops and https://www.dell.com/fr-ca/shop/laptops"
    )

    assert [(str(target.url), target.locale) for target in result.targets] == [
        ("https://www.dell.com/en-ca/shop/laptops", "en-CA"),
        ("https://www.dell.com/fr-ca/shop/laptops", "fr-CA"),
    ]
    assert result.problems == []


def test_takes_locale_written_next_to_url_when_path_has_none():
    result = extract_prompt_targets("Check https://www.dell.com/shop/laptops (fr-CA)")

    assert [target.locale for target in result.targets] == ["fr-CA"]
    assert result.problems == []


def test_reports_url_without_any_locale():
    result = extract_prompt_targets("Check https://www.dell.com/shop/laptops")

    assert result.targets == []
    assert len(result.problems) == 1
    assert "https://www.dell.com/shop/laptops" in result.problems[0]


def test_ignores_non_https_urls():
    result = extract_prompt_targets("Look at http://example.com/en-us and say hi")

    assert result.targets == []
    assert result.problems == []


def test_locale_from_one_url_does_not_leak_into_the_next_url():
    result = extract_prompt_targets(
        "Check https://www.dell.com/shop/laptops and https://www.dell.com/en-us/shop/laptops"
    )

    assert [(str(target.url), target.locale) for target in result.targets] == [
        ("https://www.dell.com/en-us/shop/laptops", "en-US"),
    ]
    assert len(result.problems) == 1
    assert "https://www.dell.com/shop/laptops" in result.problems[0]


def test_repeated_url_is_listed_once():
    result = extract_prompt_targets(
        "Audit https://www.dell.com/en-ca/shop/laptops and https://www.dell.com/fr-ca/shop/laptops\n"
        "https://www.dell.com/fr-ca/shop/laptops\n"
        "https://www.dell.com/fr-ca/shop/laptops"
    )

    assert [(str(target.url), target.locale) for target in result.targets] == [
        ("https://www.dell.com/en-ca/shop/laptops", "en-CA"),
        ("https://www.dell.com/fr-ca/shop/laptops", "fr-CA"),
    ]
    assert result.problems == []


def test_same_url_with_conflicting_locales_is_reported():
    result = extract_prompt_targets(
        "Check https://www.dell.com/shop/laptops (en-US) and https://www.dell.com/shop/laptops (fr-CA)"
    )

    assert result.targets == []
    assert len(result.problems) == 1
    assert "https://www.dell.com/shop/laptops" in result.problems[0]
    assert "en-US" in result.problems[0]
    assert "fr-CA" in result.problems[0]
