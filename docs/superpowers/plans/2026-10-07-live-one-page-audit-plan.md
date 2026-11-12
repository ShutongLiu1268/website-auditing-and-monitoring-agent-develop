# Live One-Page PDP Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one real PDP target from rendered Playwright acquisition through zone-aware rule selection, async DSX evaluation, and persisted check results while preserving fixture mode.

**Architecture:** Keep `AuditOrchestrator` responsible for run lifecycle and inject a focused `LivePageAuditService` for one-page work. `PageFetcher` returns a typed rendered-page result containing HTML, semantic zones, warnings, and a stable SHA-256 hash; the service retrieves rules, sends LLM/hybrid rules to `DSXEvaluator`, records code rules as `not_evaluated`, and persists snapshots/results.

**Tech Stack:** Python 3.12, uv, FastAPI, Pydantic v2, Motor/MongoDB, Playwright, `csoutils[ai]` DSXClient, pytest, pytest-asyncio, pytest-mock, Ruff, BasedPyright.

---

## File map

### Create

- `backend/.python-version` — pins the backend environment to Python 3.12.
- `backend/app/audits/live_page_service.py` — one-target live audit application service.
- `backend/tests/unit/test_live_page_service.py` — isolated live-service tests with mocked dependencies.
- `backend/tests/unit/test_playwright_fetcher.py` — page-fetch lifecycle, hashing, and zone extraction tests.
- `backend/tests/integration/test_live_audit.py` — in-memory one-page live pipeline integration test.

### Modify

- `backend/pyproject.toml` — explicit Hatchling package selection.
- `backend/app/domain/models.py` — evaluator metadata and run warnings.
- `backend/app/rule_knowledge/ingestion.py` — preserve metadata, correct mode inference, and source ranges.
- `backend/app/rule_knowledge/retriever.py` — repository listing, canonical zone matching, and locale behavior.
- `backend/app/persistence/repositories.py` — list rule passages and persist run warnings.
- `backend/app/acquisition/playwright_fetcher.py` — return structured rendered-page results and own Playwright lifecycle.
- `backend/app/audits/orchestrator.py` — inject and invoke the live page service.
- `backend/app/main.py` — compose dependencies in startup order.
- `backend/app/api/schemas.py` — expose run warnings when the live slice skips extra targets.
- `backend/tests/integration/test_audit_api.py` — update orchestrator construction and memory repositories.
- `backend/tests/unit/test_ingestion.py` — assert metadata and source ranges.
- `backend/tests/unit/test_retriever.py` — assert canonical zone and locale behavior.

---

### Task 1: Pin Python 3.12 and repair uv packaging

**Files:**
- Create: `backend/.python-version`
- Modify: `backend/pyproject.toml:27-42`

- [ ] **Step 1: Add the Python version file.**

Create `backend/.python-version` with exactly:

```text
3.12
```

- [ ] **Step 2: Add explicit Hatchling package selection.**

Append this table to `backend/pyproject.toml` after the build-system configuration:

```toml
[tool.hatch.build.targets.wheel]
packages = ["app"]
```

This fixes the current `Unable to determine which files to ship` error from `uv run`.

- [ ] **Step 3: Recreate/synchronize the environment with Python 3.12.**

Run from `backend/`:

```powershell
uv python install 3.12
uv sync --python 3.12 --extra dev
uv run python --version
```

Expected output contains `Python 3.12`.

- [ ] **Step 4: Verify the package can import.**

Run:

```powershell
uv run python -c "import app; print(app.__file__)"
```

Expected: a path under `backend/app` and exit code 0.

- [ ] **Step 5: Commit the environment repair.**

```powershell
git add backend/.python-version backend/pyproject.toml
git commit -m "build: pin backend to Python 3.12"
```

---

### Task 2: Make rule metadata part of the domain contract

**Files:**
- Modify: `backend/app/domain/models.py:13-17,66-101`
- Modify: `backend/app/rule_knowledge/ingestion.py:14-31,103-138,188-302`
- Modify: `backend/tests/unit/test_ingestion.py`

- [ ] **Step 1: Add the domain evaluator enum and run warnings.**

In `backend/app/domain/models.py`, add this enum after `AuditMode`:

```python
class RuleEvaluatorType(str, Enum):
    CODE = "code"
    LLM = "llm"
    HYBRID = "hybrid"
```

Add `warnings` to `AuditRun`:

```python
class AuditRun(BaseModel):
    id: str
    audit_definition_id: str
    status: RunStatus
    trigger_type: str = Field(default="manual")
    started_at: datetime | None = None
    completed_at: datetime | None = None
    previous_run_id: str | None = None
    total_pages: int = 0
    completed_pages: int = 0
    failed_pages: int = 0
    warnings: list[str] = Field(default_factory=list)
```

Extend `RulePassage`:

```python
class RulePassage(BaseModel):
    id: str
    version: str
    heading_path: list[str]
    source_range: tuple[int, int]
    original_text: str
    modes: list[AuditMode]
    locales: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    zones: list[str] = Field(default_factory=list)
    severity: Severity | None = None
    evaluator_type: RuleEvaluatorType = RuleEvaluatorType.LLM
    review_required: bool = False
    reminder: str | None = None
```

- [ ] **Step 2: Use the domain enum from ingestion.**

Remove the local `EvaluatorType` enum from `ingestion.py` and import `RuleEvaluatorType` from `app.domain.models`. Change `RuleMetadata.evaluator_type` to `RuleEvaluatorType`.

- [ ] **Step 3: Preserve inferred metadata when creating passages.**

Update the `RulePassage` construction in `_parse_section()`:

```python
passage = RulePassage(
    id=passage_id,
    version=self.version,
    heading_path=[title, subsection_title],
    source_range=(start_line, end_line),
    original_text=text,
    modes=metadata.modes,
    locales=sorted(set(metadata.locales)),
    topics=sorted(set(metadata.topics)),
    zones=sorted(set(metadata.zones)),
    severity=metadata.severity,
    evaluator_type=metadata.evaluator_type,
    review_required=metadata.review_required,
    reminder=metadata.reminder,
)
```

Refactor `_split_sections()` and `_split_subsections()` to return line ranges along with text so `source_range` identifies the original guide lines. Preserve the current plain-uppercase headers and `SECTION X — Title` handling.

- [ ] **Step 4: Correct mode inference order.**

In `_infer_section_metadata()`, evaluate the combined section before individual modes:

```python
if "r2" in title_lower and "r3" in title_lower:
    metadata.modes = [AuditMode.R2, AuditMode.R3]
elif "sprint" in title_lower or "launch" in title_lower:
    metadata.modes = [AuditMode.SPRINT_LAUNCH]
elif "r2" in title_lower:
    metadata.modes = [AuditMode.R2]
elif "r3" in title_lower:
    metadata.modes = [AuditMode.R3]
```

Use `RuleEvaluatorType.CODE`, `.LLM`, and `.HYBRID` everywhere instead of string literals.

- [ ] **Step 5: Add ingestion assertions.**

Extend `tests/unit/test_ingestion.py` with a guide containing R2, R3, combined R2/R3, dimensions, and tone text. Assert:

```python
assert passage.evaluator_type == RuleEvaluatorType.HYBRID
assert passage.review_required is True
assert passage.reminder == "Native speaker review required"
assert passage.source_range[0] > 0
assert passage.source_range[1] > passage.source_range[0]
assert set(combined_passage.modes) == {AuditMode.R2, AuditMode.R3}
```

- [ ] **Step 6: Run the focused tests.**

```powershell
uv run pytest tests/unit/test_ingestion.py -q
```

Expected: all ingestion tests pass.

---

### Task 3: Complete rule repository and retriever behavior

**Files:**
- Modify: `backend/app/persistence/repositories.py:99-122`
- Modify: `backend/app/rule_knowledge/retriever.py`
- Modify: `backend/tests/unit/test_retriever.py`

- [ ] **Step 1: Add a repository list operation.**

Add this method to `RulePassageRepository`:

```python
async def list(self, version: str | None = None) -> list[RulePassage]:
    """List rule passages, optionally restricted to one version."""
    query = {"version": version} if version else {}
    cursor = self.collection.find(query).sort("source_range.0", 1)
    return [RulePassage(**doc) async for doc in cursor]
```

- [ ] **Step 2: Canonicalize zone names.**

Add to `RuleRetriever`:

```python
_ZONE_ALIASES = {
    "dimensions_weight": "dimensions",
    "tech_specs": "tech specs",
    "configuration_selector": "configuration",
    "configuration_cards": "configuration",
}

@staticmethod
def _canonical_zone(zone: str) -> str:
    normalized = zone.strip().lower().replace("_", " ")
    return RuleRetriever._ZONE_ALIASES.get(normalized, normalized)
```

Compare canonical rule zones and query zones so guide metadata such as `tech specs` matches extracted zone names such as `tech_specs`.

- [ ] **Step 3: Make locale fallback explicit.**

Use exact locale matching first. Permit language-only fallback for non-English languages (`fr-CA` can match `fr-FR`), but keep region-specific English rules exact so `en-GB` does not match `en-US`.

- [ ] **Step 4: Add retriever tests.**

Add cases for:

```python
assert [rule.id for rule in await retriever.retrieve(AuditMode.R3, "en-US", zone="tech_specs")] == ["tech-rule"]
assert [rule.id for rule in await retriever.retrieve(AuditMode.R3, "fr-CA")] == ["fr-rule"]
assert await retriever.retrieve(AuditMode.R3, "en-US") == []  # does not inherit en-GB-only rule
```

- [ ] **Step 5: Run focused tests and lint.**

```powershell
uv run pytest tests/unit/test_retriever.py -q
ruff check app/persistence/repositories.py app/rule_knowledge/retriever.py tests/unit/test_retriever.py
```

---

### Task 4: Return structured rendered pages from Playwright

**Files:**
- Modify: `backend/app/acquisition/playwright_fetcher.py`
- Modify: `backend/app/acquisition/zone_extractor.py` only if type/selector integration requires it
- Create: `backend/tests/unit/test_playwright_fetcher.py`

- [ ] **Step 1: Add the `FetchedPage` value object.**

Add to `playwright_fetcher.py`:

```python
from dataclasses import dataclass
from hashlib import sha256

from app.acquisition.zone_extractor import Zone, ZoneExtractor


@dataclass(frozen=True)
class FetchedPage:
    url: str
    html: str
    zones: list[Zone]
    content_hash: str
    warnings: list[str]
```

- [ ] **Step 2: Own Playwright startup and shutdown.**

Store both handles:

```python
self._playwright = None
self.browser: Browser | None = None
```

`start()` calls `async_playwright().start()` once and launches Chromium. `stop()` closes the browser and then stops the Playwright handle. Repeated `stop()` calls must be safe.

- [ ] **Step 3: Inject the zone extractor.**

Use:

```python
def __init__(self, zone_extractor: ZoneExtractor | None = None) -> None:
    self._zone_extractor = zone_extractor or ZoneExtractor()
    self._playwright = None
    self.browser: Browser | None = None
```

- [ ] **Step 4: Change `fetch_page()` to return `FetchedPage`.**

Inside the page context, after navigation:

```python
html = await page.content()
zones = await self._zone_extractor.extract(page)
return FetchedPage(
    url=url,
    html=html,
    zones=zones,
    content_hash=sha256(html.encode("utf-8")).hexdigest(),
    warnings=[],
)
```

Keep page closing in `finally`. Preserve the existing `PLAYWRIGHT_TIMEOUT_MS`, timeout mapping, and fetch error mapping.

- [ ] **Step 5: Test without launching a browser.**

Mock `async_playwright`, browser, page, and `ZoneExtractor`. Assert:

- `goto()` receives the configured URL and timeout.
- `content_hash` equals `sha256(html.encode("utf-8")).hexdigest()`.
- extracted zones are returned.
- `page.close()` runs on success and fetch failure.
- `stop()` closes browser and Playwright handles.

- [ ] **Step 6: Run focused tests.**

```powershell
uv run pytest tests/unit/test_playwright_fetcher.py -q
```

---

### Task 5: Implement the one-page live audit service

**Files:**
- Create: `backend/app/audits/live_page_service.py`
- Create: `backend/tests/unit/test_live_page_service.py`

- [ ] **Step 1: Define the service result.**

Create:

```python
from dataclasses import dataclass

from app.domain.models import CheckResult, PageSnapshot


@dataclass(frozen=True)
class LivePageAuditResult:
    snapshot: PageSnapshot
    results: list[CheckResult]
    warnings: list[str]
```

- [ ] **Step 2: Define service dependencies and constructor.**

```python
class LivePageAuditService:
    """Execute acquisition, rule selection, and evaluation for one target."""

    def __init__(
        self,
        fetcher: PageFetcher,
        retriever: RuleRetriever,
        evaluator: DSXEvaluator,
        snapshot_repo: PageSnapshotRepository,
        result_repo: CheckResultRepository,
    ) -> None:
        self._fetcher = fetcher
        self._retriever = retriever
        self._evaluator = evaluator
        self._snapshot_repo = snapshot_repo
        self._result_repo = result_repo
```

- [ ] **Step 3: Implement `audit_page()`.**

Use this flow:

```python
async def audit_page(
    self,
    run: AuditRun,
    target: PageTarget,
    mode: AuditMode,
) -> LivePageAuditResult:
    fetched = await self._fetcher.fetch_page(str(target.url))
    snapshot = PageSnapshot(
        id=str(uuid.uuid4()),
        run_id=run.id,
        url=fetched.url,
        locale=target.locale,
        content_hash=fetched.content_hash,
        extraction_version="live-0.2.0",
        warnings=fetched.warnings,
    )
    await self._snapshot_repo.create(snapshot)

    results: list[CheckResult] = []
    warnings = list(fetched.warnings)
    for zone in fetched.zones:
        rules = await self._retriever.retrieve(mode, target.locale, zone=zone.name)
        for rule in rules:
            result_id = str(uuid.uuid4())
            if rule.evaluator_type == RuleEvaluatorType.CODE:
                result = CheckResult(
                    id=result_id,
                    run_id=run.id,
                    page_snapshot_id=snapshot.id,
                    rule_passage_id=rule.id,
                    zone=zone.name,
                    outcome=CheckOutcome.NOT_EVALUATED,
                    error="deterministic_checks_not_implemented",
                )
            else:
                evaluation = await self._evaluator.evaluate(
                    DSXEvaluationRequest(
                        url=fetched.url,
                        locale=target.locale,
                        zone=zone.name,
                        checkpoint_text=rule.original_text,
                        checkpoint_id=rule.id,
                        page_text=zone.text,
                        context={"heading_path": rule.heading_path},
                    )
                )
                result = build_check_result(
                    evaluation,
                    result_id=result_id,
                    run_id=run.id,
                    page_snapshot_id=snapshot.id,
                    rule_passage_id=rule.id,
                    zone=zone.name,
                )
            await self._result_repo.create(result)
            results.append(result)

    return LivePageAuditResult(snapshot=snapshot, results=results, warnings=warnings)
```

The implementation must retain `review_required` and `reminder` in the result/reporting path where the current result model supports them. If DSX is unavailable, the evaluator-generated result remains `not_evaluated`; it is never converted to `pass`.

- [ ] **Step 4: Test the happy path.**

Mock one fetched page with `hero` and `tech_specs` zones, one hybrid rule, one code rule, and one valid DSX response. Assert:

```python
assert snapshot_repo.create.await_count == 1
assert result_repo.create.await_count == 2
assert outcomes == [CheckOutcome.ISSUE, CheckOutcome.NOT_EVALUATED]
assert persisted_issue.token_usage is not None
```

- [ ] **Step 5: Test DSX unavailable behavior.**

Use `DSXEvaluator(None, model="gpt-oss-120b")`. Assert the result is `CheckOutcome.NOT_EVALUATED` with an error beginning with `DSX_UNAVAILABLE`.

- [ ] **Step 6: Run focused service tests.**

```powershell
uv run pytest tests/unit/test_live_page_service.py -q
```

---

### Task 6: Integrate the service into orchestration and startup

**Files:**
- Modify: `backend/app/audits/orchestrator.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/persistence/repositories.py`
- Modify: `backend/app/api/schemas.py`
- Modify: `backend/tests/integration/test_audit_api.py`

- [ ] **Step 1: Inject the live service into the orchestrator.**

Change the constructor to accept:

```python
live_page_service: LivePageAuditService,
```

Store it as `self.live_page_service`.

- [ ] **Step 2: Replace the raw live fetch loop.**

For `AUDIT_EXECUTION_MODE == "live"`, process `targets[0]` through `LivePageAuditService.audit_page()`. If `len(targets) > 1`, append:

```text
live_mode_one_page_limit: additional targets were not evaluated
```

Set `run.warnings` and persist them through `update_status()`.

On success, increment `completed_pages`. On `AppError` or unexpected page failure, increment `failed_pages` and append a page-specific warning. Always update run progress after the target attempt.

- [ ] **Step 3: Persist warnings.**

Extend `AuditRunRepository.update_status()` with `warnings: list[str] | None = None` and include it in `$set` when provided.

Add `warnings: list[str]` to `RunStatusResponse` and map `run.warnings` in `get_run_status()`.

- [ ] **Step 4: Compose dependencies in correct startup order.**

In `lifespan()`:

1. Construct Mongo repositories.
2. Construct DSX provider/evaluator.
3. Construct `RuleRetriever`.
4. Construct `PageFetcher` and `LivePageAuditService`.
5. Construct `AuditOrchestrator` with the service.
6. Ingest the guide.

This ensures the orchestrator receives fully composed dependencies and fixture mode still has access to the same repositories.

- [ ] **Step 5: Update memory repositories and fixture integration setup.**

Add `list()` to the integration memory rule repository. Add `warnings` handling to the memory run repository. Pass a mocked/live service or a no-op service to `AuditOrchestrator`; fixture tests must not call Playwright or DSX.

- [ ] **Step 6: Add a live API integration test.**

Use in-memory repositories and mocked `LivePageAuditService.audit_page()`. Create one target, queue a run, set `AUDIT_EXECUTION_MODE=live`, poll status, and assert:

```python
assert status.status == "completed"
assert status.completed_pages == 1
assert status.failed_pages == 0
assert service.audit_page.await_count == 1
```

Add a two-target case asserting `status.warnings` includes `live_mode_one_page_limit` and only one target is evaluated.

- [ ] **Step 7: Run the complete backend suite.**

```powershell
uv run pytest tests/unit tests/integration -q
```

Expected: all tests pass, including the unchanged fixture API integration test.

---

### Task 7: Format, type-check, and validate the complete slice

**Files:**
- Modify only files reported by automated formatting or linting.

- [ ] **Step 1: Format Python files.**

```powershell
ruff format app tests
```

Expected: formatter completes without an error.

- [ ] **Step 2: Run Ruff.**

```powershell
ruff check .
```

Expected: `All checks passed!`

- [ ] **Step 3: Run BasedPyright.**

```powershell
basedpyright app
```

Expected: 0 errors. Existing warnings may be reviewed, but no new errors may remain.

- [ ] **Step 4: Run the full test suite through uv.**

```powershell
uv run pytest
```

Expected: all unit and integration tests pass.

- [ ] **Step 5: Run the frontend regression checks.**

From the repository root:

```powershell
cd frontend
npm run lint
npm run build
```

Expected: both commands pass; no frontend files should change from this backend slice.

- [ ] **Step 6: Review the final diff.**

```powershell
cd ..
git status --short
git diff --stat
git diff --check
```

Confirm that changes are limited to the live one-page audit scope, Python 3.12 setup, tests, and documentation required by the implementation.

- [ ] **Step 7: Commit the implementation.**

```powershell
git add backend docs/superpowers/plans/2026-10-07-live-one-page-audit-plan.md
git commit -m "feat: add one-page live audit pipeline"
```

---

## Deferred follow-up plan

After this plan passes, implement these as separate slices:

1. Deterministic fact tools for links, images, dimensions, units, footnotes, trademarks, and accessibility.
2. Quote verifier that rejects DSX issues whose rule/evidence quotes are absent from source data.
3. Stable issue identity and run reconciliation for new, unresolved, resolved, and not-rechecked statuses.
4. Bounded concurrency with a semaphore and retry/backoff metrics.
5. Cache keyed by rule ID/version, zone hash, facts hash, prompt version, and model.
6. Multi-page execution, crawl scope, page limits, scheduling, and email delivery.
