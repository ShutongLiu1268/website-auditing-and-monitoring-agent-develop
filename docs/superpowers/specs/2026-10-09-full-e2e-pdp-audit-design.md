# Full End-to-End PDP Audit Completion Design

## Status

Proposed for review.

## Objective

Complete the NPL PDP Audit Copilot from audit submission through multi-page crawling, deterministic and DSX evaluation, evidence-backed issue history, conversational filtering, recurring schedules, Dell SMTP report delivery, and frontend user flows.

The implementation must leave no feature from the agreed product scope unfinished, except custom checklist upload, which is explicitly excluded from this release.

## Product scope

### Included

- Bundled NPL R2 and R3 guide as the only framework source.
- Sprint/Launch, R2, and R3 audit modes supported by the bundled guide.
- Multiple PDP targets with locale and country information.
- Crawl scope: included paths, excluded paths, and page limit.
- Public HTTPS website crawling with duplicate avoidance and coverage reporting.
- Playwright-rendered page acquisition.
- Deterministic checks for links, images, units, dimensions, footnotes, trademarks, and accessibility facts.
- DSX checks for grammar, language mismatch, meaning, tone, naturalness, accents, localization, and other subjective rules.
- Exact evidence and DOM locator capture.
- Rule/evidence quote verification before an issue is accepted.
- Stable issue identity and run comparison:
  - new
  - unresolved
  - resolved
  - not rechecked
  - changed page
- Multi-page progress, partial scans, inaccessible pages, timeouts, and skipped pages.
- Conversational audit setup, clarification, confirmation, filtering, and comparison questions.
- Recurring timezone-aware schedules.
- Dell SMTP relay delivery through environment configuration.
- Delivery attempts, failures, and retry action.
- Frontend loading, error, empty, partial, progress, findings, comparison, scheduling, and delivery states.
- Fixture mode for deterministic demos and automated tests.
- Live mode for real public pages and configured DSX/SMTP services.

### Explicitly excluded

- Custom checklist upload.
- User authentication and multi-user permissions.
- Authenticated/private website crawling.
- Automatic website modification.
- Vector database, embeddings, and RAG.
- Slack or Teams delivery.

## Completion definition

The project is complete when this controlled flow passes end to end:

```text
Chat request with multiple PDP URLs/locales
  → clarification and confirmation
  → audit definition with scope and framework
  → run started
  → multi-page crawl progress
  → deterministic + DSX checks
  → evidence verification
  → persisted findings
  → report and filters
  → schedule created
  → scheduled run executes
  → report delivered through configured SMTP
  → page changes
  → second run classified as new/unresolved/resolved/not-rechecked
```

## Architecture

```text
React DDS dashboard
  ↕ typed REST API
FastAPI application
  ├── Conversation service
  ├── Audit definition service
  ├── Crawl/orchestration service
  ├── Fact collector and deterministic runner
  ├── DSX evaluator
  ├── Evidence verifier
  ├── Issue reconciler
  ├── Report generator
  ├── Schedule service
  └── SMTP delivery service
        ↕
MongoDB + Playwright + Dell DSX + Dell SMTP relay
```

MongoDB remains the system of record. The runtime remains Python 3.12, uv, FastAPI, Pydantic v2, Motor, Playwright, React/Vite/TypeScript, and DDS components.

## Domain model additions

### Audit definition

Extend the existing audit definition with per-target crawl configuration:

```text
targets:
  url
  locale
  country
  include_paths[]
  exclude_paths[]
  page_limit
framework mode: sprint_launch | r2 | r3
rule_version
comparison_key
```

The comparison key includes normalized target scope, locale, mode, and rule version. Runs with different scope or rule versions disclose that comparison is not equivalent.

### Crawl and page models

Add:

- `CrawlPage`: discovered URL, canonical URL, depth, discovery source, status.
- `PageCoverage`: scanned, skipped, inaccessible, timeout, blocked, duplicate.
- `PageFacts`: links, images, dimensions, units, footnotes, trademarks, accessibility facts, and network responses.
- `PageSnapshot`: retains normalized content hash, zones, facts, and warnings.

### Schedule models

Add:

```text
Schedule
  id
  audit_definition_id
  enabled
  frequency: daily | weekly
  local_time
  timezone
  recipients[]
  next_run_at_utc
  last_run_id
  created_at
  updated_at
```

Add delivery records:

```text
DeliveryAttempt
  id
  schedule_id
  run_id
  recipients[]
  status: queued | sent | failed
  provider_message_id
  error_code
  attempted_at
  completed_at
```

## Rule execution design

### Applicability

Rule retrieval remains deterministic:

```text
mode + locale + country + zone + topic + evaluator type
```

No LLM decides whether a rule applies.

### Deterministic runner

The runner evaluates code rules using reusable facts:

- links: missing href, failed status, external/EN-US mismatch
- images: missing source, failed load, missing alt
- units/dimensions: locale order, allowed units, spacing, decimal format, dimension order
- footnotes: missing definitions, orphan notes, mismatched references
- trademarks: required symbol presence and adjacency
- accessibility: alt, labels, heading order, landmarks, duplicate IDs, tabindex, empty links

Each rule produces a typed `CheckResult` with outcome, problem, evidence quote, correction, severity, and DOM locator.

### Hybrid runner

Hybrid rules run deterministic checks first. Their facts are passed to DSX through `deterministic_facts`. DSX provides subjective interpretation only. Duplicate findings are merged by rule ID, zone, locator, and normalized evidence.

### DSX runner

DSX remains responsible for subjective language/context decisions. Each request contains one rule, one zone, bounded facts, and bounded page evidence. Calls are async, temperature 0, JSON validated, retried on malformed output, and token usage is recorded.

## Evidence verification

Before an issue becomes reportable:

1. `rule_quote` must exist in the exact ingested rule passage.
2. `evidence_quote` must exist in the zone text or normalized page facts.
3. `dom_locator` must identify a known extracted element when supplied.
4. A deterministic issue must carry evidence generated from the fact source.
5. Missing or altered evidence changes the result to `error` or `not_evaluated`; it never becomes a pass.

## Crawl design

The crawler:

1. Validates the starting URL with the existing HTTPS/host policy.
2. Loads the start page through Playwright.
3. Extracts same-scope links.
4. Normalizes canonical URLs and removes fragments/tracking parameters.
5. Applies include/exclude path rules.
6. Stops at the configured page limit.
7. Tracks duplicates, redirects, blocked URLs, timeouts, and retrieval errors.
8. Uses bounded concurrency and per-host delay.
9. Persists coverage status for every discovered URL.

The audit run is `completed` only when all requested crawl work completes without failures. Any inaccessible, skipped, or capped pages produce `partial` status and explicit warnings.

## Issue reconciliation

Stable issue identity uses:

```text
normalized URL
locale
rule passage ID/version
zone
DOM locator
normalized evidence subject
```

Comparison rules:

- `new`: current issue has no matching previous identity.
- `unresolved`: matching identity exists in current and previous comparable runs.
- `resolved`: previous issue absent from a successful current comparable check.
- `not_rechecked`: previous issue could not be evaluated because page/check failed or scan was partial.
- `changed_page`: comparable page identity changed due to URL/scope/page mapping.

If scope, locale, mode, or rule version changes, the report includes a comparison mismatch warning and does not present unqualified resolved statuses.

## Conversation design

The chat service uses a typed state machine:

```text
received
  → clarification_required
  → configuration_preview
  → confirmation_required
  → audit_created
  → run_started
  → result_query
  → schedule_confirmation
  → schedule_saved
```

Supported commands:

- Submit multiple URLs and locales.
- Select Sprint/Launch, R2, or R3.
- Set include paths, exclude paths, and page limit.
- Start an audit.
- Ask for filtered issues by page, locale, category, severity, or status.
- Compare countries/pages/runs.
- Create, list, pause, resume, update, and delete schedules.
- Retry failed report delivery.

Natural-language parsing uses typed validation. DSX may assist with ambiguous intent extraction, but all URLs, modes, times, timezones, recipients, and mutations are validated in code.

## Scheduling design

Use a Mongo-backed scheduler loop in the FastAPI lifespan:

- Poll enabled schedules at a configured interval.
- Claim due schedules with an atomic lease/idempotency update.
- Queue one run per occurrence.
- Calculate the next occurrence with `zoneinfo` and timezone-aware datetimes.
- Avoid duplicate runs after restarts.
- Persist schedule state before triggering delivery.
- Allow pause/resume/delete without creating unintended jobs.

The scheduler is not exposed as an unbounded background task; it is canceled and drained during application shutdown.

## Dell SMTP delivery

Use a provider-neutral SMTP delivery service configured only through environment variables:

```text
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_USE_TLS
SMTP_FROM
SMTP_TIMEOUT_SECONDS
```

No SMTP secret is committed or logged. The service:

1. Validates recipient addresses.
2. Generates text and HTML reports from stored run results.
3. Sends through the configured Dell relay.
4. Persists delivery attempt status.
5. Redacts credentials and message content from logs.
6. Exposes retry for failed attempts.

Tests mock SMTP transport. No real email is sent in automated tests.

## API completion

Add or complete typed endpoints:

```text
POST   /api/chat
GET    /api/framework
POST   /api/audits
POST   /api/audits/{id}/runs
GET    /api/runs/{id}/status
GET    /api/runs/{id}/issues
GET    /api/runs/{id}/report
GET    /api/runs/{id}/comparison
POST   /api/schedules
GET    /api/schedules
PATCH  /api/schedules/{id}
DELETE /api/schedules/{id}
POST   /api/deliveries/{id}/retry
```

All endpoints use existing structured error envelopes. No stack traces or credentials appear in responses.

## Frontend completion

Use existing DDS components and typed API modules. Add:

- Chat message history and clarification cards.
- Audit configuration preview and confirmation.
- Scope editor.
- Multi-page progress and coverage warnings.
- Deterministic/DSX evaluator labels.
- Evidence verification state.
- New/unresolved/resolved/not-rechecked filters.
- Comparison view across pages and runs.
- Schedule editor with timezone and recipients.
- Schedule list with pause/resume/delete.
- Delivery status and retry.
- Empty, loading, partial, failed, and offline states.

No raw action/form controls are introduced; DDS components remain the control layer.

### DDS MCP implementation contract

Frontend work must use DDS React v3.2.0 documentation and tokens retrieved through DDS MCP before implementation. No alternate UI component library is permitted.

Required mappings:

- Actions: `DDSButton`, compact `size="sm"` or `size="xs"`.
- Text and URL fields: `DDSTextInput`.
- Chat/prompt content: `DDSTextArea`; AI variant only for the agent prompt surface.
- Selectors: `DDSSelect size="sm"`.
- Scope and recipient toggles: `DDSCheckbox`, `DDSSwitch`, and `DDSRadioButton`.
- Time configuration: `DDSDatePicker` and `DDSTimePicker`.
- Menus: `DDSDropdown` and `DDSActionMenu`.
- Confirmation/details: `DDSModal` and `DDSDrawer`.
- Results: `DDSTabs`, `DDSCard`, `DDSClickableCard`, `DDSList`, and documented `DDSTable` when supported.
- Status: `DDSProgressBar`, `DDSProgressTracker`, `DDSBadge`, `DDSTag`, `DDSMessageBar`, and `DDSLoadingIndicator`.
- Help: `DDSHelperText` and `DDSTooltip`.
- Empty state: DDS empty-state pattern.

Before each UI implementation task, query DDS MCP component docs and foundation tokens for the selected component. Use DDS Roboto typography (`var(--dds-font-family-base)`) and DDS spacing helpers/tokens. Standard semantic layout elements and custom CSS are allowed only for layout composition, evidence highlighting, and audit-specific visualizations. Raw HTML action/form controls and custom modals/dropdowns/tabs/progress/toasts are prohibited.

## Testing and acceptance

### Backend

- Unit tests for every fact tool and parser.
- Unit tests for verifier and reconciliation transitions.
- Unit tests for schedule timezone/lease behavior.
- SMTP mocked delivery success/failure/retry tests.
- Integration test for multi-page crawl and partial coverage.
- Integration test for second-run status transitions.
- Integration test for chat-to-audit configuration.
- Integration test for schedule-to-run-to-delivery.
- Full pytest, Ruff, and BasedPyright verification.

### Frontend

- Typed API client tests.
- Component tests for chat, progress, findings, schedule, and delivery states.
- E2E test for the complete demo journey.
- Lint, typecheck, production build, and npm audit.

### End-to-end demo acceptance

1. Submit three controlled PDP URLs with locales.
2. Select R3 and configure scope.
3. Start audit.
4. Observe multi-page progress and coverage warnings.
5. Inspect deterministic and DSX findings with evidence.
6. Filter issues through chat and dashboard controls.
7. Compare against a previous run.
8. Create a daily schedule with timezone and recipients.
9. Trigger an accelerated scheduled run.
10. Verify SMTP delivery record.
11. Force a delivery failure and retry it.
12. Modify a controlled page and verify new/unresolved/resolved/not-rechecked results.

## Demo readiness

The completed application must be demoable by a technical teammate without code changes or manual database editing.

### Demo profile

Provide a documented demo profile with:

```text
AUDIT_EXECUTION_MODE=fixture
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=npl_pdp_audit
```

Fixture mode must demonstrate the complete product flow with deterministic controlled results for multiple URLs, including:

- grammar issue
- broken link
- broken image
- locale/language issue
- dimension/unit issue
- new, unresolved, resolved, and not-rechecked run states
- partial scan and inaccessible-page warning

Live mode remains available when DSX and Dell SMTP environment values are supplied. Demo mode must not require a DSX credential merely to start the application or inspect the dashboard.

### Startup and smoke test

Provide:

- `backend/.env.example` with safe values and clear live/fixture comments.
- `frontend/.env.example` with API base URL.
- Docker Compose startup for MongoDB, API, and frontend.
- A backend health check that reports API, database, rule-guide, and DSX configuration state without exposing secrets.
- A single smoke-test command or script that:
  1. verifies health;
  2. creates a multi-target fixture audit;
  3. starts a run;
  4. polls until completion;
  5. retrieves findings and report;
  6. creates or exercises a schedule in demo mode;
  7. verifies delivery status or a clear configured-relay failure state.

### Demo documentation

README instructions must include:

- prerequisites;
- exact startup commands;
- fixture-mode demo flow;
- live-mode configuration;
- SMTP configuration without secrets;
- expected findings;
- expected schedule and delivery behavior;
- troubleshooting for MongoDB, Playwright, DSX, and SMTP;
- cleanup commands that do not delete persistent data without explicit user action.

### Demo acceptance

A fresh developer environment can start the stack, open the frontend, run the fixture flow, inspect evidence, filter findings, compare runs, manage a schedule, and see delivery success/failure state using only documented commands.

## Non-goals and explicit remaining boundaries

After this design is implemented, only the following remain outside scope:

- Custom checklist upload.
- Authenticated website support.
- User authentication/authorization.
- Slack/Teams integrations.
- Automatic content modification.
- Vector RAG infrastructure.
