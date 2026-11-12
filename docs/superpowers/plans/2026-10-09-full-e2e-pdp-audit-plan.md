# Full End-to-End PDP Audit Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the NPL PDP Audit Copilot across multi-page audits, deterministic and DSX checks, evidence verification, issue history, chat, schedules, Dell SMTP delivery, frontend states, and demo acceptance.

**Architecture:** Extend current typed domain/repository boundaries rather than adding a second persistence model. Keep `AuditOrchestrator` responsible for run lifecycle, compose focused services for crawling, facts, verification, reconciliation, conversation, scheduling, reporting, and delivery, and keep all external clients behind injectable interfaces. Preserve fixture mode as a deterministic demo adapter while live mode uses Playwright, DSX, MongoDB, and configured Dell SMTP.

**Tech Stack:** Python 3.12, uv, FastAPI, Pydantic v2, Motor/MongoDB, Playwright, `csoutils[ai]` DSXClient, `aiosmtplib`, React/Vite/TypeScript, DDS React, pytest, pytest-asyncio, pytest-mock, Ruff, BasedPyright, npm/Oxlint.

---

## DDS-only frontend contract

All frontend controls and UI workflows must use the DDS React v3.2.0 component library and DDS MCP documentation as the source of truth. Before implementing or changing a frontend component, query DDS MCP `get_component_info_tool` for the React component and `get_foundation_tokens_tool` for typography/spacing/tokens. Do not introduce another UI component library.

### Required DDS mappings

| Workflow/UI need | DDS component or pattern |
|---|---|
| Primary/secondary actions | `DDSButton` with `size="sm"` or `size="xs"` |
| Text/URL/path input | `DDSTextInput` with `size="sm"` |
| Chat/multiline content | `DDSTextArea` with `size="sm"`, `variant="ai"` only for the agent prompt surface |
| Mode/locale/status selection | `DDSSelect` with `size="sm"` |
| Include/exclude options | `DDSCheckbox` |
| Enabled/paused schedule | `DDSSwitch` |
| Frequency/mode choice | `DDSRadioButton` |
| Date/time configuration | `DDSDatePicker` and `DDSTimePicker` |
| Menus and contextual actions | `DDSDropdown` or `DDSActionMenu` |
| Dialog confirmation | `DDSModal` |
| Detail/sidebar workflow | `DDSDrawer` |
| Result sections | `DDSTabs`, `DDSCard`, `DDSClickableCard`, or `DDSList` |
| Findings table | `DDSTable` when supported by current DDS docs; otherwise DDS cards/list composition |
| Run progress | `DDSProgressBar size="sm"` and `DDSProgressTracker` where appropriate |
| Status/severity | `DDSBadge`, `DDSTag`, and `DDSMessageBar` |
| Empty/loading states | DDS empty-state pattern, `DDSLoadingIndicator`, `DDSMessageBar` |
| Help/explanations | `DDSHelperText` and `DDSTooltip` |

### UI restrictions

- No raw `<button>`, `<input>`, `<select>`, `<textarea>`, or custom action controls.
- No custom modal, dropdown, tabs, progress, toast, form field, or loading control.
- Use DDS semantic tokens and helpers such as `var(--dds-font-family-base)`, `dds__gap--sm`, and DDS spacing classes from MCP foundations.
- Standard semantic layout elements are allowed; custom CSS is limited to page composition, evidence highlighting, and audit-specific visualization.
- Every loading, empty, error, partial, success, and disabled state uses a DDS component or documented DDS pattern.
- Frontend implementation review must include a raw-control audit and a component-to-DDS mapping check.

## DDS-only frontend contract

All frontend controls and UI workflows must use the DDS React v3.2.0 component library and DDS MCP documentation as the source of truth. Before implementing or changing a frontend component, query DDS MCP `get_component_info_tool` for the React component and `get_foundation_tokens_tool` for typography/spacing/tokens. Do not introduce another UI component library.

### Required DDS mappings

| Workflow/UI need | DDS component or pattern |
|---|---|
| Primary/secondary actions | `DDSButton` with `size="sm"` or `size="xs"` |
| Text/URL/path input | `DDSTextInput` with `size="sm"` |
| Chat/multiline content | `DDSTextArea` with `size="sm"`, `variant="ai"` only for the agent prompt surface |
| Mode/locale/status selection | `DDSSelect` with `size="sm"` |
| Include/exclude options | `DDSCheckbox` |
| Enabled/paused schedule | `DDSSwitch` |
| Frequency/mode choice | `DDSRadioButton` |
| Date/time configuration | `DDSDatePicker` and `DDSTimePicker` |
| Menus and contextual actions | `DDSDropdown` or `DDSActionMenu` |
| Dialog confirmation | `DDSModal` |
| Detail/sidebar workflow | `DDSDrawer` |
| Result sections | `DDSTabs`, `DDSCard`, `DDSClickableCard`, or `DDSList` |
| Findings table | `DDSTable` when supported by current DDS docs; otherwise DDS cards/list composition |
| Run progress | `DDSProgressBar size="sm"` for percentage progress and `DDSProgressTracker` for multi-stage progress |
| Status/severity | `DDSBadge`, `DDSTag`, and `DDSMessageBar` |
| Empty/loading states | DDS empty-state pattern, `DDSLoadingIndicator`, `DDSMessageBar` |
| Help/explanations | `DDSHelperText` and `DDSTooltip` |

### UI restrictions

- No raw `<button>`, `<input>`, `<select>`, `<textarea>`, or custom action controls.
- No custom modal, dropdown, tabs, progress, toast, form field, or loading control.
- Use DDS semantic tokens and helpers such as `var(--dds-font-family-base)`, `dds__gap--sm`, and DDS spacing classes from MCP foundations.
- Standard semantic layout elements are allowed; custom CSS is limited to page composition, evidence highlighting, and audit-specific visualization.
- Every loading, empty, error, partial, success, and disabled state uses a DDS component or documented DDS pattern.
- Frontend implementation review must include a raw-control audit and a component-to-DDS mapping check.

## File map

### Create

- `backend/app/acquisition/crawler.py` — scoped multi-page discovery, normalization, deduplication, and concurrency.
- `backend/app/facts/models.py` — typed page facts and coverage facts.
- `backend/app/facts/collector.py` — Playwright DOM/network fact collection.
- `backend/app/facts/deterministic_runner.py` — code-rule and hybrid fact evaluation.
- `backend/app/agent/verifier.py` — exact rule/evidence/locator verification.
- `backend/app/issues/reconciler.py` — stable issue identity and run transitions.
- `backend/app/reporting/generator.py` — text/HTML report generation.
- `backend/app/conversation/models.py` — typed chat state, intents, and commands.
- `backend/app/conversation/parser.py` — validated natural-language command parser.
- `backend/app/conversation/service.py` — clarification, confirmation, and result-query workflow.
- `backend/app/schedules/service.py` — timezone-aware schedule lifecycle and due-run claiming.
- `backend/app/delivery/smtp.py` — Dell SMTP transport abstraction.
- `backend/app/delivery/service.py` — delivery attempts and retry workflow.
- `backend/app/smoke_demo.py` — documented fixture-mode API smoke flow.
- `backend/tests/unit/test_config.py`
- `backend/tests/unit/test_facts.py`
- `backend/tests/unit/test_verifier.py`
- `backend/tests/unit/test_reconciler.py`
- `backend/tests/unit/test_conversation.py`
- `backend/tests/unit/test_schedules.py`
- `backend/tests/unit/test_delivery.py`
- `backend/tests/integration/test_multi_page_audit.py`
- `backend/tests/integration/test_schedule_delivery.py`
- `backend/tests/e2e/test_demo_flow.py`
- `frontend/src/hooks/useChat.ts`
- `frontend/src/hooks/useSchedules.ts`
- `frontend/src/components/chat/ChatPanel.tsx`
- `frontend/src/components/audit/ScopeEditor.tsx`
- `frontend/src/components/schedules/SchedulePanel.tsx`
- `frontend/src/components/delivery/DeliveryStatus.tsx`
- `frontend/src/components/results/CoverageBanner.tsx`
- `frontend/src/components/results/ComparisonFilters.tsx`
- `frontend/src/e2e/demo-flow.spec.ts`

### Modify

- `backend/app/config.py` — crawl, scheduler, SMTP, report, and demo settings.
- `backend/pyproject.toml` — runtime SMTP dependency and test/runtime tooling.
- `backend/app/domain/models.py` — scope, crawl, facts, schedules, deliveries, issue status.
- `backend/app/api/schemas.py` — typed request/response contracts for all new endpoints.
- `backend/app/persistence/repositories.py` — repositories and atomic schedule/delivery operations.
- `backend/app/acquisition/playwright_fetcher.py` — expose network/DOM data needed by facts.
- `backend/app/audits/live_page_service.py` — facts, deterministic results, DSX facts, verification.
- `backend/app/audits/orchestrator.py` — multi-page crawl and run-level coverage/reconciliation.
- `backend/app/comparison/engine.py` — compare stable issue observations with partial-scan rules.
- `backend/app/main.py` — service composition, scheduler lifecycle, and endpoints.
- `backend/app/api/mappers.py` — coverage, status, evaluator, and comparison mapping.
- `backend/app/tools/units.py` — locale-aware unit/dimension facts.
- `backend/app/rule_knowledge/ingestion.py` — rule tags for fact categories and applicability.
- `backend/.env.example` — complete safe configuration.
- `docker-compose.yml` — complete demo startup configuration.
- `README.md` — runbook, smoke test, live configuration, and troubleshooting.
- `frontend/src/api/types.ts`
- `frontend/src/api/client.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/results/ResultsStage.tsx`
- `frontend/src/types/audit.ts`
- `frontend/package.json` — frontend test/E2E scripts and Playwright test dependency.

---

### Task 1: Freeze configuration and demo runtime contracts

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`
- Modify: `docker-compose.yml`
- Modify: `backend/app/main.py`
- Create: `backend/app/smoke_demo.py`
- Modify: `README.md`

- [ ] **Step 1: Write configuration tests.**

Add tests asserting defaults and safe parsing:

```python
def test_demo_defaults_do_not_require_external_services():
    config = Settings(_env_file=None)
    assert config.AUDIT_EXECUTION_MODE == "fixture"
    assert config.SMTP_HOST == ""
    assert config.DSX_VERIFY_TLS is True


def test_scheduler_timezone_is_configurable():
    config = Settings(_env_file=None, SCHEDULER_TIMEZONE="America/New_York")
    assert config.SCHEDULER_TIMEZONE == "America/New_York"
```

- [ ] **Step 2: Add typed settings.**

Add:

```python
SMTP_HOST: str = ""
SMTP_PORT: int = 587
SMTP_USERNAME: str = ""
SMTP_PASSWORD: str = ""
SMTP_USE_TLS: bool = True
SMTP_FROM: str = ""
SMTP_TIMEOUT_SECONDS: float = 30.0
SCHEDULER_ENABLED: bool = False
SCHEDULER_POLL_SECONDS: int = 30
SCHEDULER_TIMEZONE: str = "UTC"
CRAWL_MAX_CONCURRENT: int = 2
CRAWL_SAME_HOST_DELAY_MS: int = 2000
CRAWL_MAX_DEPTH: int = 2
CRAWL_DEFAULT_PAGE_LIMIT: int = 25
DEMO_MODE: bool = True
REPORT_BRAND_NAME: str = "NPL PDP Audit Copilot"
```

- [ ] **Step 3: Add the SMTP runtime dependency.**

From `backend/`, use uv to add the pinned runtime dependency and refresh the lockfile:

```powershell
uv add "aiosmtplib>=3.0.2"
uv sync --python 3.12 --extra dev
```

- [ ] **Step 4: Add safe env examples.**

Document fixture and live values without secrets:

```dotenv
AUDIT_EXECUTION_MODE=fixture
DEMO_MODE=true
SCHEDULER_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_FROM=
```

- [ ] **Step 5: Add the smoke command.**

Implement `python -m app.smoke_demo` to call `/health`, create a three-target fixture audit, poll status, fetch issues/report, and print a concise pass/fail summary. It must return exit code 0 only when health, audit completion, findings, and report retrieval succeed.

- [ ] **Step 6: Update Docker and README.**

Document:

```powershell
docker compose up --build -d
cd backend
uv run python -m app.smoke_demo
```

Include MongoDB cleanup only as an explicit opt-in command; never delete volumes in the default demo flow.

- [ ] **Step 7: Run focused verification.**

```powershell
cd backend
uv run pytest tests/unit/test_config.py -q
ruff check .
```

Expected: configuration tests pass and Ruff is clean.

---

### Task 2: Extend domain and persistence contracts

**Files:**
- Modify: `backend/app/domain/models.py`
- Modify: `backend/app/api/schemas.py`
- Modify: `backend/app/persistence/repositories.py`
- Create: `backend/tests/unit/test_persistence_models.py`

- [ ] **Step 1: Add scope and coverage models.**

Add typed models:

```python
class CrawlScope(BaseModel):
    include_paths: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)
    page_limit: int = Field(default=25, ge=1, le=500)
    max_depth: int = Field(default=2, ge=0, le=10)


class CrawlPage(BaseModel):
    url: str
    canonical_url: str
    depth: int
    status: str
    reason: str | None = None
    discovered_from: str | None = None


class PageCoverage(BaseModel):
    scanned: int = 0
    skipped: int = 0
    inaccessible: int = 0
    duplicate: int = 0
    timeout: int = 0
```

- [ ] **Step 2: Extend audit definitions and runs.**

Add `scope: CrawlScope` to `AuditDefinition`. Add `coverage: PageCoverage`, `coverage_pages: list[CrawlPage]`, and `previous_comparable_run_id: str | None` to `AuditRun`.

- [ ] **Step 3: Add schedule and delivery models.**

```python
class Schedule(BaseModel):
    id: str
    audit_definition_id: str
    enabled: bool = True
    frequency: str
    local_time: str
    timezone: str
    recipients: list[str]
    next_run_at_utc: datetime
    lease_until_utc: datetime | None = None
    last_run_id: str | None = None


class DeliveryAttempt(BaseModel):
    id: str
    schedule_id: str
    run_id: str
    recipients: list[str]
    status: str
    provider_message_id: str | None = None
    error_code: str | None = None
    attempted_at: datetime | None = None
    completed_at: datetime | None = None
```

- [ ] **Step 4: Add repository methods.**

Implement typed methods:

```python
async def claim_due_schedule(
    self, now_utc: datetime, lease_until_utc: datetime
) -> Schedule | None:
    """Atomically claim one due schedule."""
```

Use Mongo `find_one_and_update` with `enabled=True`, `next_run_at_utc <= now`, and either no lease or expired lease. Add repositories for schedules and delivery attempts.

- [ ] **Step 5: Add API schemas.**

Add typed request/response models for scope, schedules, delivery attempts, coverage, and comparison statuses. Reject invalid timezone names, empty recipients, invalid frequency, and page limits outside configured bounds.

- [ ] **Step 6: Run tests.**

```powershell
uv run pytest tests/unit/test_persistence_models.py tests/unit/test_models.py -q
```

---

### Task 3: Implement deterministic facts for core checks

**Files:**
- Create: `backend/app/facts/models.py`
- Create: `backend/app/facts/collector.py`
- Create: `backend/app/facts/deterministic_runner.py`
- Modify: `backend/app/acquisition/playwright_fetcher.py`
- Modify: `backend/app/tools/units.py`
- Create: `backend/tests/unit/test_facts.py`

- [ ] **Step 1: Define facts.**

```python
class LinkFact(BaseModel):
    href: str
    locator: str
    status_code: int | None
    reachable: bool | None

class ImageFact(BaseModel):
    src: str
    locator: str
    loaded: bool
    alt: str | None

class DimensionFact(BaseModel):
    text: str
    value: float | None
    unit: str | None
    locator: str

class PageFacts(BaseModel):
    links: list[LinkFact] = Field(default_factory=list)
    images: list[ImageFact] = Field(default_factory=list)
    dimensions: list[DimensionFact] = Field(default_factory=list)
    network_warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 2: Collect DOM and network facts while the page is open.**

`FactCollector.collect(page, zones)` must inspect anchors and images, record locators, reuse navigation response statuses, parse dimension text with `UnitParser`, and never issue requests to URLs outside the approved URL policy.

- [ ] **Step 3: Implement deterministic rule dispatch.**

```python
async def evaluate_code_rule(
    rule: RulePassage,
    facts: PageFacts,
    zone: Zone,
    context: EvaluationContext,
) -> CheckResult:
    """Evaluate one code rule from typed facts."""
```

Dispatch by normalized rule topics:

- link → missing/broken link issue
- image/accessibility → missing/failed image or alt issue
- dimensions/units → locale/unit issue using `UnitConsistencyChecker`
- unknown code rule → `ERROR` with `unsupported_deterministic_rule`, never `PASS`

- [ ] **Step 4: Pass facts to hybrid DSX calls.**

Add compact `PageFacts.model_dump()` output to `DSXEvaluationRequest.deterministic_facts` for hybrid rules. Keep code-only rules out of DSX.

- [ ] **Step 5: Add controlled fact tests.**

Test broken links, failed images, missing alt, metric/imperial mismatches, valid units, and unsupported rule behavior. Assert exact evidence and locators.

- [ ] **Step 6: Run focused tests.**

```powershell
uv run pytest tests/unit/test_facts.py tests/unit/test_units.py -q
```

---

### Task 4: Add verification and issue reconciliation

**Files:**
- Create: `backend/app/agent/verifier.py`
- Create: `backend/app/issues/reconciler.py`
- Modify: `backend/app/comparison/engine.py`
- Create: `backend/tests/unit/test_verifier.py`
- Create: `backend/tests/unit/test_reconciler.py`

- [ ] **Step 1: Implement exact evidence verification.**

```python
class EvidenceVerifier:
    def verify(
        self,
        result: CheckResult,
        rule: RulePassage,
        zone: Zone,
        facts: PageFacts,
    ) -> VerificationResult:
        """Validate rule quote, evidence quote, and locator."""
```

Require rule quotes to occur in `rule.original_text`, evidence quotes to occur in zone text or normalized facts, and supplied locators to match known zone locators.

- [ ] **Step 2: Reject unverified issues.**

Verified issue remains `ISSUE`. Missing evidence becomes `ERROR` with `evidence_verification_failed`; it must not reach reportable issue output.

- [ ] **Step 3: Implement stable issue fingerprints.**

Normalize URL, locale, rule ID/version, zone, locator, and evidence subject using SHA-256. Persist `IssueIdentity` and `IssueObservation` through repositories.

- [ ] **Step 4: Implement transitions.**

Compare only equivalent scope/mode/rule-version runs. Mark failed or partial checks `NOT_RECHECKED`. Mark absent issues resolved only after successful comparable checks.

- [ ] **Step 5: Add transition tests.**

Cover new, unresolved, resolved, not-rechecked, changed-page, and scope-mismatch cases.

- [ ] **Step 6: Run focused tests.**

```powershell
uv run pytest tests/unit/test_verifier.py tests/unit/test_reconciler.py tests/unit/test_comparison.py -q
```

---

### Task 5: Implement multi-page crawling, concurrency, and caching

**Files:**
- Create: `backend/app/acquisition/crawler.py`
- Create: `backend/app/agent/cache.py`
- Modify: `backend/app/audits/orchestrator.py`
- Modify: `backend/app/audits/live_page_service.py`
- Modify: `backend/app/config.py`
- Create: `backend/tests/unit/test_crawler.py`
- Create: `backend/tests/unit/test_cache.py`
- Create: `backend/tests/integration/test_multi_page_audit.py`

- [ ] **Step 1: Implement URL normalization and scope.**

Normalize fragments/tracking parameters, accept only HTTPS approved hosts, enforce include/exclude paths, depth, and page limit, and record every skipped/duplicate URL as coverage data.

- [ ] **Step 2: Implement bounded crawl workers.**

Use `asyncio.Semaphore(settings.CRAWL_MAX_CONCURRENT)` and per-host delay. `Crawler.crawl(start_targets, scope)` returns ordered `CrawlPage` records and fetched pages.

- [ ] **Step 3: Add result cache.**

Cache key:

```text
rule version + rule ID + zone hash + facts hash + prompt version + model
```

Cache only validated results. Never cache errors, unverified issues, or results from partial facts.

- [ ] **Step 4: Integrate all targets.**

Replace one-page limit in `AuditOrchestrator` with crawler output, update progress after each page, persist coverage, and retain fixture mode behavior.

- [ ] **Step 5: Add multi-page tests.**

Test page limits, path exclusions, duplicate URLs, failed pages, concurrency bounds, cache hits, and partial status.

- [ ] **Step 6: Run integration tests.**

```powershell
uv run pytest tests/unit/test_crawler.py tests/unit/test_cache.py tests/integration/test_multi_page_audit.py -q
```

---

### Task 6: Complete reporting and API contracts

**Files:**
- Create: `backend/app/reporting/generator.py`
- Modify: `backend/app/api/schemas.py`
- Modify: `backend/app/api/mappers.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/unit/test_reporting.py`

- [ ] **Step 1: Generate report models.**

Include run time/timezone, sites, framework version, scanned/skipped/inaccessible counts, severity totals, status totals, partial-scan warnings, and all issue fields.

- [ ] **Step 2: Complete API endpoints.**

Ensure audit creation accepts scope; status exposes coverage; issues supports website/locale/category/severity/status/rule filters; comparison exposes all transition groups.

- [ ] **Step 3: Add report tests.**

Assert stable totals and partial-scan disclosure for fixture and live-like data.

- [ ] **Step 4: Run API tests.**

```powershell
uv run pytest tests/integration/test_audit_api.py tests/unit/test_reporting.py -q
```

---

### Task 7: Implement typed chat workflow

**Files:**
- Create: `backend/app/conversation/models.py`
- Create: `backend/app/conversation/parser.py`
- Create: `backend/app/conversation/service.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/unit/test_conversation.py`
- Create: `backend/tests/integration/test_chat_api.py`

- [ ] **Step 1: Define typed intents and state.**

Support audit creation, start audit, findings query, comparison query, schedule mutation, and delivery retry. Every mutation carries a confirmation-required state.

- [ ] **Step 2: Parse structured values.**

Extract HTTPS URLs, BCP-47 locales, mode, include/exclude paths, page limit, local time, IANA timezone, and validated recipients. Ambiguous or missing values return clarification prompts.

- [ ] **Step 3: Implement chat service.**

Use deterministic parsing first; use DSX only for ambiguous intent extraction with Pydantic validation. Never allow model output to directly execute mutations.

- [ ] **Step 4: Add API tests.**

Cover multi-URL clarification, confirmation, audit start, filters, comparison, invalid recipients, invalid timezone, and duplicate schedule mutation prevention.

- [ ] **Step 5: Run tests.**

```powershell
uv run pytest tests/unit/test_conversation.py tests/integration/test_chat_api.py -q
```

---

### Task 8: Implement schedules, reports, and Dell SMTP delivery

**Files:**
- Create: `backend/app/schedules/service.py`
- Create: `backend/app/delivery/smtp.py`
- Create: `backend/app/delivery/service.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/config.py`
- Create: `backend/tests/unit/test_schedules.py`
- Create: `backend/tests/unit/test_delivery.py`
- Create: `backend/tests/integration/test_schedule_delivery.py`

- [ ] **Step 1: Implement timezone-aware recurrence.**

Use `zoneinfo.ZoneInfo`, convert local schedule time to UTC, and calculate next daily/weekly occurrence without naive datetimes.

- [ ] **Step 2: Implement Mongo lease claiming.**

The scheduler claims due records atomically, creates one run per occurrence, advances `next_run_at_utc`, and releases/records lease state on failure.

- [ ] **Step 3: Implement SMTP transport.**

Use `aiosmtplib` with configured host/port/TLS/auth. Redact credentials, validate recipients, and persist sent/failed attempts.

- [ ] **Step 4: Implement retry.**

Retry creates a new delivery attempt for the same report/run and never creates a duplicate audit run.

- [ ] **Step 5: Add tests.**

Mock SMTP and clock behavior. Test DST/timezone conversion, lease idempotency, delivery success/failure, and retry.

- [ ] **Step 6: Run integration tests.**

```powershell
uv run pytest tests/unit/test_schedules.py tests/unit/test_delivery.py tests/integration/test_schedule_delivery.py -q
```

---

### Task 9: Complete frontend chat, audit, comparison, scheduling, and delivery UX

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/hooks/useChat.ts`
- Create: `frontend/src/hooks/useSchedules.ts`
- Create: `frontend/src/components/chat/ChatPanel.tsx`
- Create: `frontend/src/components/audit/ScopeEditor.tsx`
- Create: `frontend/src/components/schedules/SchedulePanel.tsx`
- Create: `frontend/src/components/delivery/DeliveryStatus.tsx`
- Create: `frontend/src/components/results/CoverageBanner.tsx`
- Create: `frontend/src/components/results/ComparisonFilters.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/results/ResultsStage.tsx`
- Modify: `frontend/src/types/audit.ts`
- Create: `frontend/src/e2e/demo-flow.spec.ts`

- [ ] **Step 1: Record DDS component mappings before implementation.**

Use DDS MCP React v3.2.0 component documentation and foundation tokens to record the selected component for each new workflow. Query `get_component_info_tool` for buttons, text inputs, text areas, selects, date/time pickers, checkboxes, switches, radio buttons, menus, modal, drawer, tabs, cards, table/list, progress bar, badges/tags, message bar, loading indicator, helper text, and tooltip. Query `get_ux_pattern_tool` for the empty-state pattern and `get_foundation_tokens_tool` for typography and spacing. Reject any design that introduces a raw action/form control.

- [ ] **Step 2: Add the frontend E2E runner.**

From `frontend/`, add the Playwright test dependency and browser:

```powershell
npm install --save-dev @playwright/test
npx playwright install chromium
```

Add scripts:

```json
{
  "test:e2e": "playwright test"
}
```

- [ ] **Step 3: Add typed API models and client methods.**

Add methods for chat, scope-aware audits, coverage/status, comparison, schedules, delivery status, and retry. Every response has typed success/error handling.

- [ ] **Step 4: Add chat state hook.**

Represent `clarification`, `confirmation`, `running`, `result_query`, and `schedule_saved` states. Disable mutation controls while requests are pending.

- [ ] **Step 5: Add DDS scope and schedule controls.**

Use DDS components for path fields, page limit, timezone, local time, frequency, recipients, confirmation, pause/resume/delete, and retry.

- [ ] **Step 6: Add results/coverage states.**

Render loading, empty, failed, partial, inaccessible, not-evaluated, verified, and comparison statuses. Do not show unverified issues as confirmed findings.

- [ ] **Step 7: Add frontend E2E flow.**

Exercise chat/configuration → audit → progress → findings → comparison → schedule → delivery state against a fixture API.

- [ ] **Step 8: Run frontend verification.**

```powershell
npm run lint
npm run build
npm audit --audit-level=high
```

---

### Task 10: Make demo readiness executable

**Files:**
- Create: `backend/tests/e2e/test_demo_flow.py`
- Modify: `frontend/src/e2e/demo-flow.spec.ts`
- Modify: `backend/app/smoke_demo.py`
- Modify: `README.md`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add backend demo E2E.**

Run fixture mode against three controlled targets, verify expected seeded findings, partial coverage, comparison transitions, schedule creation, and delivery status.

- [ ] **Step 2: Add frontend demo E2E.**

Verify dashboard startup, audit flow, findings, filters, comparison, schedule panel, and delivery state.

- [ ] **Step 3: Complete README runbook.**

Document prerequisites, `.env` setup, Docker startup, smoke test, fixture flow, live DSX/SMTP configuration, expected findings, troubleshooting, and safe cleanup.

- [ ] **Step 4: Run complete verification.**

```powershell
cd backend
uv run pytest
ruff check .
basedpyright app
cd ../frontend
npm run lint
npm run build
npm audit --audit-level=high
```

Expected: tests pass, Ruff clean, BasedPyright reports 0 errors, frontend build passes, and npm audit reports no high-severity vulnerabilities.

- [ ] **Step 5: Review the final staged diff.**

```powershell
git status --short
git diff --check
git diff --stat
```

Confirm no secret files, credentials, generated build output, or unreviewed files are staged.

- [ ] **Step 6: Commit the completed E2E implementation.**

```powershell
git add backend frontend docs README.md docker-compose.yml
 git commit -m "feat: complete end-to-end PDP audit workflow"
```

---

## Final acceptance checklist

- [ ] Bundled NPL R2/R3 guide loads and reports its version.
- [ ] Multiple URLs/locales/scopes/page limits validate and persist.
- [ ] Multi-page live crawl respects scope and reports coverage.
- [ ] Links/images/units/dimensions/footnotes/trademarks/accessibility facts evaluate deterministically.
- [ ] Subjective rules evaluate through DSX with token usage.
- [ ] Rule/evidence/locator verification rejects unsupported findings.
- [ ] Issue identity and all comparison statuses work across comparable runs.
- [ ] Chat creates audits, filters results, compares runs, and manages schedules.
- [ ] Scheduler claims due jobs without duplicates and handles timezone conversion.
- [ ] Dell SMTP delivery records success/failure and supports retry.
- [ ] Frontend renders all loading/error/partial/empty/comparison/schedule/delivery states using DDS controls.
- [ ] Fixture mode works without DSX credentials.
- [ ] Smoke test runs from documented commands without manual database edits.
- [ ] Backend and frontend verification commands pass.
