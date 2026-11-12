from app.domain.models import AuditMode, RulePassage
from app.rule_knowledge.markets import MarketGroups
from app.rule_knowledge.selection import RuleSelector

GROUPS = MarketGroups({"IMPERIAL": ("en-US", "en-CA", "fr-CA")})


def _passage(
    rule_id: str,
    profiles: list[AuditMode],
    markets: list[str],
    zones: list[str],
) -> RulePassage:
    return RulePassage(
        id=rule_id,
        version="v1",
        heading_path=["Section", rule_id],
        source_range=(1, 2),
        original_text=f"Text for {rule_id}.",
        modes=profiles,
        markets=markets,
        zones=zones,
    )


PASSAGES = [
    _passage("global-all", [AuditMode.R2], ["global"], []),
    _passage("en-us-only", [AuditMode.R2], ["en-US"], []),
    _passage("r3-only", [AuditMode.R3], ["global"], []),
    _passage("footer-only", [AuditMode.R2], ["global"], ["global_footer"]),
    _passage("imperial", [AuditMode.R2], ["IMPERIAL"], ["dimensions_weight"]),
]


def _ids(rules):
    return [rule.id for rule in rules]


def test_profile_must_match():
    selected = RuleSelector(PASSAGES, GROUPS).select(AuditMode.R2, "en-GB", "hero")
    assert "r3-only" not in _ids(selected)


def test_global_passage_applies_to_every_locale_in_profile():
    selected = RuleSelector(PASSAGES, GROUPS).select(AuditMode.R2, "ja-JP", "hero")
    assert "global-all" in _ids(selected)


def test_locale_tag_passage_applies_only_to_that_locale():
    selector = RuleSelector(PASSAGES, GROUPS)
    assert "en-us-only" in _ids(selector.select(AuditMode.R2, "en-US", "hero"))
    assert "en-us-only" not in _ids(selector.select(AuditMode.R2, "en-CA", "hero"))


def test_empty_zone_list_applies_to_every_zone():
    selector = RuleSelector(PASSAGES, GROUPS)
    assert "global-all" in _ids(
        selector.select(AuditMode.R2, "en-US", "footer_anything")
    )


def test_zone_list_restricts_to_listed_zones():
    selector = RuleSelector(PASSAGES, GROUPS)
    assert "footer-only" in _ids(
        selector.select(AuditMode.R2, "en-US", "global_footer")
    )
    assert "footer-only" not in _ids(selector.select(AuditMode.R2, "en-US", "hero"))


def test_group_passage_uses_group_membership():
    selector = RuleSelector(PASSAGES, GROUPS)
    assert "imperial" in _ids(
        selector.select(AuditMode.R2, "en-US", "dimensions_weight")
    )
    assert "imperial" not in _ids(
        selector.select(AuditMode.R2, "fr-FR", "dimensions_weight")
    )


def test_page_checkpoint_runs_only_at_page_scope():
    selector = RuleSelector(
        [_passage("page-only", [AuditMode.R2], ["global"], ["page"])], GROUPS
    )
    assert "page-only" in _ids(selector.select(AuditMode.R2, "en-US", "page"))
    assert "page-only" not in _ids(selector.select(AuditMode.R2, "en-US", "hero"))


def test_all_zone_checkpoint_does_not_run_at_page_scope():
    selector = RuleSelector(
        [_passage("all-zones", [AuditMode.R2], ["global"], [])], GROUPS
    )
    assert "all-zones" in _ids(selector.select(AuditMode.R2, "en-US", "hero"))
    assert "all-zones" not in _ids(selector.select(AuditMode.R2, "en-US", "page"))
