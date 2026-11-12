from pathlib import Path

from app.domain.models import AuditMode
from app.rule_knowledge.ingestion import RuleIngestor
from app.rule_knowledge.selection import RuleSelector

GUIDE = Path(__file__).resolve().parents[2] / "app" / "rule_knowledge" / "npl-pdp-audit-guide.md"


def test_startup_catalog_builds_a_selector_that_finds_english_checkpoints():
    catalog = RuleIngestor(GUIDE).ingest()
    selector = RuleSelector(catalog.passages, catalog.groups)

    assert selector.select(AuditMode.R2, "en-US", "features")
    assert selector.select(AuditMode.R3, "en-CA", "dimensions_weight")
