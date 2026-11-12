# Audit Definition BSON Serialization Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent `POST /api/audits` from failing when PyMongo serializes a Pydantic `HttpUrl` inside an audit definition.

**Architecture:** Keep Pydantic Python-mode serialization at the audit-definition repository boundary so Mongo-native datetimes remain datetimes. Normalize only `targets[*].url` to strings in the document passed to `insert_one`; leave the domain model unchanged.

**Tech Stack:** Python 3.12+, Pydantic v2, Motor/PyMongo BSON, pytest, pytest-asyncio, pytest-mock, Ruff, basedpyright.

---

### Task 1: Add BSON-boundary regression test

**Files:**
- Create: `backend/tests/unit/test_repositories.py`
- Test: `backend/tests/unit/test_repositories.py::TestAuditDefinitionRepository::test_create_stores_bson_encodable_target_url`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_repositories.py` with all imports at module scope and a class-based pytest test:

```python
from datetime import datetime

import pytest
from bson import BSON
from pytest_mock import MockerFixture

from app.domain.models import AuditDefinition, AuditMode, PageTarget
from app.persistence.repositories import AuditDefinitionRepository


class TestAuditDefinitionRepository:
    @pytest.mark.asyncio
    async def test_create_stores_bson_encodable_target_url(
        self, mocker: MockerFixture
    ):
        # Arrange
        collection = mocker.Mock(insert_one=mocker.AsyncMock())
        database = mocker.Mock(audit_definitions=collection)
        repository = AuditDefinitionRepository(database)
        definition = AuditDefinition(
            id="audit-1",
            mode=AuditMode.R3,
            targets=[
                PageTarget(
                    url="https://www.dell.com/en-ca/shop/laptops",
                    locale="en-CA",
                )
            ],
            rule_version="v1",
        )

        # Act
        result = await repository.create(definition)

        # Assert
        stored_document = collection.insert_one.await_args.args[0]
        BSON.encode(stored_document)
        assert stored_document["targets"][0]["url"] == str(definition.targets[0].url)
        assert isinstance(stored_document["created_at"], datetime)
        assert result is definition
```

- [ ] **Step 2: Run test to verify it fails**

Run from `backend`:

```bash
uv run pytest tests/unit/test_repositories.py::TestAuditDefinitionRepository::test_create_stores_bson_encodable_target_url -q
```

Expected: FAIL at `BSON.encode(stored_document)` with `bson.errors.InvalidDocument` because the inserted document still contains a Pydantic `HttpUrl`.

### Task 2: Normalize audit target URLs before Mongo insertion

**Files:**
- Modify: `backend/app/persistence/repositories.py:32-36`
- Test: `backend/tests/unit/test_repositories.py::TestAuditDefinitionRepository::test_create_stores_bson_encodable_target_url`

- [ ] **Step 1: Implement the minimal repository change**

Replace the current document preparation in `AuditDefinitionRepository.create()`:

```python
        doc = definition.model_dump()
        await self.collection.insert_one(doc)
```

with:

```python
        doc = definition.model_dump()
        doc["targets"] = [
            {**target, "url": str(target["url"])} for target in doc["targets"]
        ]
        await self.collection.insert_one(doc)
```

Do not use `model_dump(mode="json")`; it would serialize `created_at` as a string. Do not mutate `definition`.

- [ ] **Step 2: Run the targeted test to verify it passes**

Run:

```bash
uv run pytest tests/unit/test_repositories.py::TestAuditDefinitionRepository::test_create_stores_bson_encodable_target_url -q
```

Expected: PASS. The test must confirm BSON encoding succeeds, the URL is a string, `created_at` remains a `datetime`, and the original definition is returned.

### Task 3: Run complete verification

**Files:**
- Verify: `backend/app/persistence/repositories.py`
- Verify: `backend/tests/unit/test_repositories.py`

- [ ] **Step 1: Run all backend tests**

From `backend`, run:

```bash
uv run pytest
```

Expected: All tests pass, including the new repository regression test.

- [ ] **Step 2: Run Ruff checks**

From `backend`, run:

```bash
uv run ruff format --check .
uv run ruff check .
```

Expected: Formatting check and lint check pass without modifying unrelated files.

- [ ] **Step 3: Run basedpyright**

From `backend`, run:

```bash
uv run basedpyright app
```

Expected: No type errors in application code.

- [ ] **Step 4: Run the available Snyk code scan**

Run the repository's configured `snyk_code_scan` tool if available. If no Snyk tool is exposed in this environment, record that limitation and run the available local security check without changing security configuration.

Expected: No new findings from modified first-party Python code.

- [ ] **Step 5: Review the final diff and working tree**

Run:

```bash
git diff -- backend/app/persistence/repositories.py backend/tests/unit/test_repositories.py
git status --short
```

Confirm only the intended backend files are part of the fix. Do not stage or modify the user's `.vscode`, frontend, or `Pipfile` changes.

- [ ] **Step 6: Commit only the fix files**

After verification passes, stage only the implementation and regression test:

```bash
git add -- backend/app/persistence/repositories.py backend/tests/unit/test_repositories.py
git commit -m "fix(persistence): serialize audit target URLs"
```

Do not push.
