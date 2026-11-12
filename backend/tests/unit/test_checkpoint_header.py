import pytest

from app.domain.models import AuditMode, RuleEvaluatorType
from app.rule_knowledge.checkpoint_header import (
    CheckpointHeaderError,
    build_header,
    parse_market_groups,
)

GROUP_NAMES = frozenset({"EMEA", "APJC", "IMPERIAL", "NON_IMPERIAL", "NON_ENGLISH"})

VALID = """
id: SPR-20
profiles: sprint_launch
markets: global
zones: footnotes_disclaimers
evaluator: hybrid
check: superlative_candidates
review: never
reminder: Check that: the notes match
topics: footnote, link
"""


def test_build_header_reads_every_key():
    header = build_header(VALID, GROUP_NAMES)

    assert header.id == "SPR-20"
    assert header.profiles == (AuditMode.SPRINT_LAUNCH,)
    assert header.markets == ("global",)
    assert header.zones == ("footnotes_disclaimers",)
    assert header.evaluator == RuleEvaluatorType.HYBRID
    assert header.check == "superlative_candidates"
    assert header.review == "never"
    assert header.reminder == "Check that: the notes match"
    assert header.topics == ("footnote", "link")


def test_zones_all_means_empty_tuple():
    header = build_header(
        VALID.replace("zones: footnotes_disclaimers", "zones: all"), GROUP_NAMES
    )
    assert header.zones == ()


def test_review_accepts_a_locale_tag():
    header = build_header(VALID.replace("review: never", "review: en-CA"), GROUP_NAMES)
    assert header.review == "en-CA"


def test_missing_key_is_rejected():
    with pytest.raises(CheckpointHeaderError, match="missing keys"):
        build_header(VALID.replace("evaluator: hybrid\n", ""), GROUP_NAMES)


def test_unknown_zone_is_rejected():
    with pytest.raises(CheckpointHeaderError, match="unknown zones"):
        build_header(VALID.replace("footnotes_disclaimers", "footer_nav"), GROUP_NAMES)


def test_unknown_market_is_rejected():
    with pytest.raises(CheckpointHeaderError, match="unknown market"):
        build_header(VALID.replace("markets: global", "markets: MOON"), GROUP_NAMES)


def test_unknown_evaluator_is_rejected():
    with pytest.raises(CheckpointHeaderError):
        build_header(
            VALID.replace("evaluator: hybrid", "evaluator: guess"), GROUP_NAMES
        )


def test_market_groups_parse_explicit_and_complement_groups():
    groups = parse_market_groups(
        "EMEA: en-GB, fr-FR\nNON_IMPERIAL: every locale not in IMPERIAL\nIMPERIAL: en-US, en-CA"
    )

    assert groups == {
        "EMEA": ("en-GB", "fr-FR"),
        "NON_IMPERIAL": (),
        "IMPERIAL": ("en-US", "en-CA"),
    }


def test_market_group_with_non_locale_entry_is_rejected():
    with pytest.raises(CheckpointHeaderError, match="non-locale"):
        parse_market_groups("EMEA: en-GB, United Kingdom")


def test_code_checkpoint_needs_a_registered_code_check():
    with pytest.raises(CheckpointHeaderError, match="code check"):
        build_header(VALID.replace("evaluator: hybrid", "evaluator: code"), GROUP_NAMES)


def test_code_checkpoint_accepts_registered_check_on_page_scope():
    block = (
        VALID.replace("evaluator: hybrid", "evaluator: code")
        .replace("check: superlative_candidates", "check: broken_links")
        .replace("zones: footnotes_disclaimers", "zones: page")
    )

    header = build_header(block, GROUP_NAMES)

    assert header.evaluator == RuleEvaluatorType.CODE
    assert header.check == "broken_links"
    assert header.zones == ("page",)


def test_hybrid_checkpoint_needs_a_gate_check():
    with pytest.raises(CheckpointHeaderError, match="gate check"):
        build_header(
            VALID.replace("check: superlative_candidates", "check: broken_links"),
            GROUP_NAMES,
        )


def test_llm_checkpoint_takes_no_check():
    with pytest.raises(CheckpointHeaderError, match="no check"):
        build_header(VALID.replace("evaluator: hybrid", "evaluator: llm"), GROUP_NAMES)


def test_page_zone_requires_code_evaluator():
    with pytest.raises(CheckpointHeaderError, match="page"):
        build_header(
            VALID.replace("zones: footnotes_disclaimers", "zones: page"), GROUP_NAMES
        )


def test_page_zone_cannot_be_combined_with_other_zones():
    block = (
        VALID.replace("evaluator: hybrid", "evaluator: code")
        .replace("check: superlative_candidates", "check: broken_links")
        .replace("zones: footnotes_disclaimers", "zones: page, hero")
    )

    with pytest.raises(CheckpointHeaderError, match="page"):
        build_header(block, GROUP_NAMES)
