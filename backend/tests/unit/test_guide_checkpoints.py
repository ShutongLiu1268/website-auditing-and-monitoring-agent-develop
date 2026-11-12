from collections import Counter
from pathlib import Path

import pytest

from app.acquisition.zone_extractor import PAGE_ZONE
from app.audits.live_page_service import LivePageAuditService
from app.domain.models import AuditMode, RuleEvaluatorType
from app.rule_knowledge.ingestion import RuleIngestor
from app.rule_knowledge.selection import RuleSelector

GUIDE = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "rule_knowledge"
    / "npl-pdp-audit-guide.md"
)


@pytest.fixture(scope="module")
def catalog():
    return RuleIngestor(GUIDE).ingest()


@pytest.fixture(scope="module")
def selector(catalog):
    return RuleSelector(catalog.passages, catalog.groups)


DUPLICATE_IDS = {
    "R2G-02",
    "R2G-03",
    "R2G-05",
    "R2G-10",
    "R2G-11",
    "R2G-12",
    "R2G-13",
    "R2G-14",
    "R2G-16",
    "R3R-01",
    "R3R-02",
    "R3R-07",
    "R3R-11",
}


def _ids(rules):
    return {rule.id for rule in rules}


def test_guide_declares_52_checkpoints_per_profile(catalog):
    assert len(catalog.passages) == 52
    counts = {
        mode: sum(mode in p.modes for p in catalog.passages) for mode in AuditMode
    }
    assert counts == {AuditMode.SPRINT_LAUNCH: 23, AuditMode.R2: 22, AuditMode.R3: 22}


def test_removed_duplicates_stay_out_of_the_guide(catalog):
    assert {passage.id for passage in catalog.passages}.isdisjoint(DUPLICATE_IDS)


def test_english_pages_get_checkpoints(selector):
    assert "D6" in _ids(selector.select(AuditMode.R2, "en-US", "hero"))
    assert "D1" in _ids(selector.select(AuditMode.R3, "en-US", "hero"))
    assert "SPR-05" in _ids(selector.select(AuditMode.SPRINT_LAUNCH, "en-CA", "hero"))


def test_en_us_only_checkpoints_stay_on_en_us(selector):
    assert "R2G-04" in _ids(selector.select(AuditMode.R2, "en-US", "features"))
    assert "R2G-04" not in _ids(selector.select(AuditMode.R2, "en-CA", "features"))


def test_imperial_and_metric_checks_split_by_market(selector):
    en_ca = _ids(selector.select(AuditMode.R3, "en-CA", "dimensions_weight"))
    fr_fr = _ids(selector.select(AuditMode.R3, "fr-FR", "dimensions_weight"))
    assert "R3R-04" in en_ca and "R3R-03" not in en_ca
    assert "R3R-03" in fr_fr and "R3R-04" not in fr_fr


def test_china_copilot_check_only_on_zh_cn(selector):
    assert "D8" in _ids(selector.select(AuditMode.R2, "zh-CN", "features"))
    assert "D8" not in _ids(selector.select(AuditMode.R2, "en-US", "features"))


def test_footnote_zone_checks_only_run_in_their_zone(selector):
    footnotes = _ids(
        selector.select(AuditMode.SPRINT_LAUNCH, "en-US", "footnotes_disclaimers")
    )
    footer = _ids(selector.select(AuditMode.SPRINT_LAUNCH, "en-US", "global_footer"))
    assert "SPR-20" in footnotes
    assert "SPR-20" not in footer


def test_guide_evaluator_split_is_code_first(catalog):
    counts = Counter(passage.evaluator_type for passage in catalog.passages)
    assert counts == {
        RuleEvaluatorType.CODE: 15,
        RuleEvaluatorType.HYBRID: 6,
        RuleEvaluatorType.LLM: 31,
    }


def test_code_and_gate_checkpoints_name_a_check(catalog):
    named = {passage.id for passage in catalog.passages if passage.check}
    declared = {
        passage.id
        for passage in catalog.passages
        if passage.evaluator_type in (RuleEvaluatorType.CODE, RuleEvaluatorType.HYBRID)
    }
    assert named == declared


def test_page_scope_checkpoints_are_code(catalog):
    page = {passage.id for passage in catalog.passages if passage.zones == [PAGE_ZONE]}
    assert page == {"SPR-12", "SPR-13", "R3R-08", "R3R-09"}
    assert {
        passage.evaluator_type for passage in catalog.passages if passage.id in page
    } == {RuleEvaluatorType.CODE}


def test_page_checks_run_only_at_page_scope(selector):
    assert "SPR-12" in _ids(
        selector.select(AuditMode.SPRINT_LAUNCH, "en-US", PAGE_ZONE)
    )
    assert "SPR-12" not in _ids(
        selector.select(AuditMode.SPRINT_LAUNCH, "en-US", "hero")
    )


def test_link_probe_needed_only_where_broken_links_is_declared(selector, mocker):
    service = LivePageAuditService(
        mocker.MagicMock(),
        selector,
        mocker.MagicMock(),
        mocker.MagicMock(),
        mocker.MagicMock(),
    )

    assert service.needs_link_probe(AuditMode.R2, ["en-US", "fr-FR", "zh-CN"]) is False
    assert service.needs_link_probe(AuditMode.SPRINT_LAUNCH, ["en-US"]) is True
    assert service.needs_link_probe(AuditMode.R3, ["en-CA"]) is True


def test_inch_notation_code_check_runs_on_every_zone(selector):
    assert "SPR-14" in _ids(
        selector.select(AuditMode.SPRINT_LAUNCH, "en-US", "features")
    )
