from app.acquisition.zone_extractor import PAGE_ZONE, Zone
from app.checks.models import CheckInput
from app.checks.page_rules import broken_links, broken_media, en_us_links
from app.facts.models import LinkFact, MediaFact, PageFacts


def _check(facts: PageFacts) -> CheckInput:
    return CheckInput(
        zone=Zone(name=PAGE_ZONE, text="", dom_locator="", metadata={}),
        facts=facts,
        locale="en-US",
    )


def _link(href: str, locator: str, status: int | None, reachable: bool | None) -> LinkFact:
    return LinkFact(href=href, locator=locator, status_code=status, reachable=reachable)


class TestBrokenLinks:
    def test_broken_link_is_issue_with_href_evidence(self):
        # Arrange
        facts = PageFacts(
            links=[
                _link("https://www.dell.com/missing", "a:nth-of-type(1)", 404, False),
                _link("https://www.dell.com/ok", "a:nth-of-type(2)", 200, True),
            ]
        )

        # Act
        findings = broken_links(_check(facts))

        # Assert
        assert [finding.evidence for finding in findings] == ["https://www.dell.com/missing"]
        assert findings[0].locator == "a:nth-of-type(1)"

    def test_all_reachable_links_pass(self):
        # Arrange
        facts = PageFacts(links=[_link("https://www.dell.com/ok", "a:nth-of-type(1)", 200, True)])

        # Act
        findings = broken_links(_check(facts))

        # Assert
        assert findings == []

    def test_unverified_links_are_not_applicable(self):
        # Arrange
        facts = PageFacts(links=[_link("https://www.dell.com/ok", "a:nth-of-type(1)", None, None)])

        # Act
        findings = broken_links(_check(facts))

        # Assert
        assert findings is None

    def test_page_without_links_is_not_applicable(self):
        # Arrange
        facts = PageFacts()

        # Act
        findings = broken_links(_check(facts))

        # Assert
        assert findings is None

    def test_duplicate_broken_href_is_reported_once(self):
        # Arrange
        facts = PageFacts(
            links=[
                _link("https://www.dell.com/missing", "a:nth-of-type(1)", 404, False),
                _link("https://www.dell.com/missing", "a:nth-of-type(2)", 404, False),
            ]
        )

        # Act
        findings = broken_links(_check(facts))

        # Assert
        assert len(findings) == 1


class TestBrokenMedia:
    def test_failed_video_is_issue_with_source_evidence(self):
        # Arrange
        facts = PageFacts(
            media=[
                MediaFact(
                    src="https://cdn.example.test/x.mp4",
                    locator="video:nth-of-type(1)",
                    broken=True,
                ),
                MediaFact(
                    src="https://cdn.example.test/y.mp4",
                    locator="video:nth-of-type(2)",
                    broken=False,
                ),
            ]
        )

        # Act
        findings = broken_media(_check(facts))

        # Assert
        assert [finding.evidence for finding in findings] == ["https://cdn.example.test/x.mp4"]

    def test_working_media_passes(self):
        # Arrange
        facts = PageFacts(
            media=[
                MediaFact(
                    src="https://cdn.example.test/y.mp4",
                    locator="video:nth-of-type(1)",
                    broken=False,
                )
            ]
        )

        # Act
        findings = broken_media(_check(facts))

        # Assert
        assert findings == []

    def test_page_without_media_is_not_applicable(self):
        # Arrange
        facts = PageFacts()

        # Act
        findings = broken_media(_check(facts))

        # Assert
        assert findings is None


class TestEnUsLinks:
    def test_en_us_link_is_issue(self):
        # Arrange
        facts = PageFacts(
            links=[
                _link("https://www.dell.com/en-us/shop/laptop", "a:nth-of-type(1)", 200, True),
                _link("https://www.dell.com/fr-fr/shop/laptop", "a:nth-of-type(2)", 200, True),
            ]
        )

        # Act
        findings = en_us_links(_check(facts))

        # Assert
        assert [finding.evidence for finding in findings] == [
            "https://www.dell.com/en-us/shop/laptop"
        ]

    def test_en_us_root_link_is_issue(self):
        # Arrange
        facts = PageFacts(
            links=[_link("https://www.dell.com/en-us", "a:nth-of-type(1)", 200, True)]
        )

        # Act
        findings = en_us_links(_check(facts))

        # Assert
        assert len(findings) == 1

    def test_localized_links_pass(self):
        # Arrange
        facts = PageFacts(
            links=[_link("https://www.dell.com/fr-fr/shop", "a:nth-of-type(1)", 200, True)]
        )

        # Act
        findings = en_us_links(_check(facts))

        # Assert
        assert findings == []

    def test_page_without_links_is_not_applicable(self):
        # Arrange
        facts = PageFacts()

        # Act
        findings = en_us_links(_check(facts))

        # Assert
        assert findings is None
