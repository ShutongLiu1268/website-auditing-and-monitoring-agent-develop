# Live One-Page PDP Audit Design

## Status

Proposed for review.

## Goal

Implement the first real live-audit vertical slice for one PDP target while preserving the existing fixture-backed demo path.

The slice proves this flow:

```text
Live URL
  → rendered Playwright page
  → semantic zones
  → applicable rule passages
  → DSX evaluation
  → persisted page snapshot and check results
  → run progress/status
```

This slice does not implement multi-page concurrency, deterministic fact tools, quote verification, issue-history reconciliation, caching, scheduling, or email delivery.

## Scope

### Included

- Python 3.12 project baseline using `backend/.python-version`.
- `uv`-based environment and verification workflow.
- Hatchling package discovery fix so `uv run` can build the backend.
- Structured rendered-page acquisition result.
- Semantic zone extraction while a Playwright page remains open.
- Stable SHA-256 page content hashing.
- Rule passage listing and preservation of inferred evaluator metadata.
- Rule retrieval by audit mode, locale, and zone.
- One-page live evaluation through the existing async DSX evaluator.
- Persistence of page snapshots and check results.
- Explicit `not_evaluated` results for code-only rules whose fact tools are not yet implemented.
- Mocked unit/integration coverage for the live path.
- Existing fixture mode and existing frontend API behavior unchanged.

### Deferred

- Processing all configured targets in live mode.
- Crawl discovery, included/excluded paths, and page limits.
- Deterministic checks for links, images, dimensions, units, footnotes, trademarks, and accessibility.
- Evidence quote verification.
- Finding deduplication and stable issue identity reconciliation.
- Previous-run comparison.
- Result caching and cross-page result reuse.
- Bounded parallel DSX calls.
- Scheduler, report email, and mailbox delivery.

## Runtime baseline

- `backend/.python-version` contains `3.12`, matching the inventory-ai project standard.
- `backend/pyproject.toml` keeps `requires-python = ">=3.12"`, Ruff target `py312`, and BasedPyright version `3.12`.
- `uv` is the only package and environment command. No direct `pip` commands are used.
- Hatchling explicitly packages the `app` directory.
- Playwright browser installation remains a deployment/setup prerequisite.

## Architecture

### Existing boundaries retained

- `AuditOrchestrator` owns run lifecycle, status transitions, and page progress.
- `PageFetcher` owns Playwright browser lifecycle and navigation errors.
- `ZoneExtractor` owns semantic DOM-zone extraction.
- `RuleRetriever` owns applicability filtering.
- `DSXEvaluator` owns prompt construction, async gateway calls, JSON parsing, validation, retries, and token usage.
- Repositories own MongoDB persistence.

### New composition boundary

Add a `LivePageAuditService` responsible for one target:

```text
LivePageAuditService.audit_page(run, target)
  ├─ PageFetcher.fetch_page(target.url)
  ├─ PageSnapshot persistence
  ├─ RuleRetriever.retrieve(mode, locale, zone)
  ├─ DSXEvaluationRequest construction
  ├─ DSXEvaluator.evaluate(request)
  ├─ build_check_result(...)
  └─ CheckResult persistence
```

`AuditOrchestrator` receives this service through constructor injection. It does not construct DSX clients, retrieve rules, parse zones, or build evaluation prompts directly.

## Acquisition contract

`PageFetcher.fetch_page()` returns a typed `FetchedPage` value rather than raw HTML:

```python
class FetchedPage:
    url: str
    html: str
    zones: list[Zone]
    content_hash: str
    warnings: list[str]
```

Acquisition behavior:

1. Start or reuse Chromium.
2. Open a new page.
3. Navigate using configured timeout and `networkidle`.
4. Wait for page stabilization.
5. Run `ZoneExtractor` while the Playwright page is open.
6. Capture HTML.
7. Compute SHA-256 from UTF-8 HTML bytes.
8. Close the page in `finally`.
9. Return `FetchedPage`.

No Playwright `Page` object escapes the acquisition layer. The existing timeout and fetch errors remain mapped to `AppError` error codes.

## Rule metadata contract

Extend `RulePassage` with persisted metadata:

- `evaluator_type`: `code`, `llm`, or `hybrid`
- `review_required`: boolean
- `reminder`: optional text

`RuleIngestor` must preserve these values when constructing passages. The metadata inference remains deterministic and based on guide section content; no LLM is used during ingestion.

`RulePassageRepository` adds a `list()` operation for the retriever. The list operation returns all currently ingested passages. Version-specific retrieval remains available through `get_by_version()`.

For this slice, a rule is eligible for DSX when its evaluator type is `llm` or `hybrid`. A `code` rule is represented as a persisted `CheckResult` with:

```text
outcome = not_evaluated
error = deterministic_checks_not_implemented
```

A code-only rule must never be recorded as `pass` merely because its deterministic tool is deferred.

## Live page audit flow

For the first configured target:

1. Load the audit definition and its mode.
2. Acquire the rendered page and zones.
3. Persist one `PageSnapshot` containing URL, locale, stable content hash, extraction version, and warnings.
4. For each extracted zone, retrieve applicable passages using audit mode, target locale, and zone name.
5. For each retrieved passage:
   - create a deterministic `not_evaluated` result for `code` rules;
   - create a bounded `DSXEvaluationRequest` for `llm` and `hybrid` rules;
   - call `DSXEvaluator.evaluate()` asynchronously;
   - map the response using `build_check_result()`;
   - persist the result.
6. Increment completed-page progress only after snapshot and all page results are persisted.
7. If acquisition fails, increment failed pages and retain the run as partial when other work can complete.
8. If DSX is unavailable, persist `not_evaluated` results with `DSX_UNAVAILABLE`; do not fail the entire page solely because language evaluation is unavailable.

The first live implementation evaluates rules sequentially. This keeps behavior deterministic and avoids introducing rate-limit assumptions before the first real audit measurement.

## Orchestrator behavior

`AuditOrchestrator` constructor dependencies become:

```text
AuditDefinitionRepository
AuditRunRepository
PageSnapshotRepository
CheckResultRepository
LivePageAuditService
```

Mode behavior:

- `AUDIT_EXECUTION_MODE=fixture`: existing seeded path remains unchanged.
- `AUDIT_EXECUTION_MODE=live`: execute only the first configured target for this vertical slice.
- If an audit contains additional targets, record a run warning that multi-page live execution is not implemented yet. Do not silently claim those pages were scanned.
- Existing queued → running → completed/partial transitions remain unchanged.
- Existing status polling response shape remains unchanged.

## Error handling

- Fetch timeout/error: page is failed; error is captured as a warning and run can become partial.
- Rule retrieval error: page is failed unless a safe empty rule set can be returned; no false passes are generated.
- DSX unavailable: applicable language rules become `not_evaluated`.
- DSX malformed output after retry: result becomes `error` with `DSX_MALFORMED_OUTPUT`.
- Persistence errors are raised to the run boundary and mark the run failed/partial according to existing lifecycle behavior.
- No credentials, raw prompts, page secrets, or full gateway exception bodies are logged.

## Testing strategy

Use `pytest`, `pytest-asyncio`, and `pytest-mock` only.

### Unit tests

- `FetchedPage` contains zones and stable SHA-256 hash.
- Page fetcher closes pages after success and failure.
- Rule repository list operation returns typed passages.
- Rule metadata survives ingestion and persistence mapping.
- Live service retrieves rules with correct mode/locale/zone.
- One DSX request is generated per applicable LLM/hybrid rule.
- DSX output becomes a persisted `CheckResult` with model and token usage.
- Code-only rules become `not_evaluated`, not `pass`.
- Missing DSX client produces `not_evaluated` results.
- Fixture mode remains unaffected.

### Integration test

Use in-memory repositories and mocked acquisition/evaluation services to verify:

```text
create audit
  → create run
  → execute live run
  → snapshot persisted
  → check results persisted
  → completed/partial status persisted
```

No real website, MongoDB instance, Playwright browser, or DSX credential is required for automated tests.

## Verification

From `backend/`:

```powershell
uv run pytest
ruff format .
ruff check .
basedpyright app
```

Expected outcome:

- Existing and new tests pass.
- Ruff reports no errors.
- BasedPyright reports no errors introduced by this slice.
- `uv run` can build and execute the package using Python 3.12.

## Acceptance criteria

1. `backend/.python-version` selects Python 3.12.
2. `uv run pytest` executes the test suite successfully.
3. Fixture mode produces the same deterministic findings as before.
4. Live mode can execute one configured public URL with mocked acquisition/evaluation in automated tests.
5. Live mode persists one snapshot and typed check results for that page.
6. LLM/hybrid rules call DSX asynchronously with temperature 0 and record token usage.
7. Code-only rules are explicitly `not_evaluated` until deterministic tools exist.
8. DSX unavailability does not become a false pass.
9. Additional configured live targets are disclosed as not yet implemented.
10. No vector database, embeddings, or RAG is introduced.
