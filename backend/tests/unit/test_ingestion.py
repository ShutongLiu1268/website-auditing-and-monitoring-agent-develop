from pathlib import Path

import pytest

from app.domain.models import AuditMode
from app.rule_knowledge.checkpoint_header import CheckpointHeaderError
from app.rule_knowledge.ingestion import RuleIngestor

GROUPS = """<!-- market-groups
EMEA: en-GB, fr-FR
IMPERIAL: en-US, en-CA, fr-CA
NON_IMPERIAL: every locale not in IMPERIAL
NON_ENGLISH: every locale whose language is not en
-->
"""

SAMPLE = """
## Sprint/Launch audit
### SPR-07 Syllables
<!-- checkpoint
id: SPR-07
profiles: sprint_launch
markets: en-US
zones: all
evaluator: llm
review: never
-->
Words with more than 3 syllables.

## Process notes
Plain text is not a checkpoint.
"""


def _guide(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "guide.md"
    path.write_text(GROUPS + body, encoding="utf-8")
    return path


def test_ingestor_reads_declared_headers(tmp_path):
    catalog = RuleIngestor(_guide(tmp_path, SAMPLE)).ingest()

    [passage] = catalog.passages
    assert passage.id == "SPR-07"
    assert passage.modes == [AuditMode.SPRINT_LAUNCH]
    assert passage.markets == ["en-US"]
    assert passage.zones == []
    assert passage.heading_path == ["Sprint/Launch audit", "SPR-07 Syllables"]
    assert passage.original_text == "Words with more than 3 syllables."
    assert catalog.groups.matches(("IMPERIAL",), "en-CA")


def test_version_changes_with_content(tmp_path):
    first = RuleIngestor(_guide(tmp_path, SAMPLE)).ingest().version
    second = RuleIngestor(_guide(tmp_path, SAMPLE + "\nMore text.\n")).ingest().version
    assert first != second


def test_heading_without_header_is_rejected(tmp_path):
    body = "\n## Sprint/Launch audit\n### SPR-01 No header\nText.\n"
    with pytest.raises(CheckpointHeaderError, match="no header"):
        RuleIngestor(_guide(tmp_path, body)).ingest()


def test_unknown_zone_is_rejected(tmp_path):
    body = SAMPLE.replace("zones: all", "zones: footer_nav")
    with pytest.raises(CheckpointHeaderError, match="unknown zones"):
        RuleIngestor(_guide(tmp_path, body)).ingest()


def test_unknown_market_is_rejected(tmp_path):
    body = SAMPLE.replace("markets: en-US", "markets: MOON")
    with pytest.raises(CheckpointHeaderError, match="unknown market"):
        RuleIngestor(_guide(tmp_path, body)).ingest()


def test_duplicate_ids_are_rejected(tmp_path):
    body = SAMPLE + SAMPLE.split("## Process notes")[0]
    with pytest.raises(CheckpointHeaderError, match="duplicate"):
        RuleIngestor(_guide(tmp_path, body)).ingest()


def test_guide_without_market_groups_is_rejected(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text(SAMPLE, encoding="utf-8")
    with pytest.raises(CheckpointHeaderError, match="market-groups"):
        RuleIngestor(path).ingest()
