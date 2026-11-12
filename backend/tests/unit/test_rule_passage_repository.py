import pytest

from app.domain.models import AuditMode, RulePassage
from app.persistence.repositories import RulePassageRepository


class FakeCollection:
    def __init__(self):
        self.docs: list[dict] = []

    async def delete_many(self, query):
        self.docs = [
            doc for doc in self.docs if doc.get("version") != query.get("version")
        ]

    async def insert_many(self, docs):
        self.docs.extend(docs)

        class Result:
            inserted_ids = list(range(len(docs)))

        return Result()

    async def replace_one(self, query, doc, upsert=False):
        self.docs = [item for item in self.docs if item.get("_id") != query.get("_id")]
        self.docs.append(doc)


class FakeDb:
    def __init__(self):
        self.rule_passages = FakeCollection()
        self.rule_catalog = FakeCollection()


def _passage(rule_id: str, version: str = "v1") -> RulePassage:
    return RulePassage(
        id=rule_id,
        version=version,
        heading_path=["Section", rule_id],
        source_range=(1, 2),
        original_text="Text.",
        modes=[AuditMode.R3],
    )


@pytest.mark.asyncio
async def test_replace_version_does_not_duplicate_on_restart():
    db = FakeDb()
    repo = RulePassageRepository(db)
    passages = [_passage("A"), _passage("B")]

    await repo.replace_version("v1", passages)
    await repo.replace_version("v1", passages)

    assert len(db.rule_passages.docs) == 2


@pytest.mark.asyncio
async def test_replace_version_keeps_other_versions():
    db = FakeDb()
    repo = RulePassageRepository(db)
    await repo.replace_version("v0", [_passage("OLD", "v0")])
    await repo.replace_version("v1", [_passage("NEW", "v1")])

    assert {doc["version"] for doc in db.rule_passages.docs} == {"v0", "v1"}
