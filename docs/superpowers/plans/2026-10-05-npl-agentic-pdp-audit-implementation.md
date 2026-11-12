# NPL Agentic PDP Audit — Implementation Plan

This plan guides an SWE coding agent through end-to-end delivery of the hackathon MVP defined by the NPL multi-URL agentic PDP audit design.

## Product Target

Build a conversational web application that accepts up to five public Dell PDP URLs, dynamically retrieves and applies bundled Sprint/Launch, R2, or R3 checkpoints through Dell DSX/GPT-OSS, compares page and specification content, tracks findings between runs, schedules daily reruns, and optionally emails the resulting report.

Every LLM finding must include:

- Exact quoted checkpoint text.
- Exact page evidence.
- Stable DOM locator.
- Problem description.
- Suggested correction.
- Proof-ready replacement text.
- Severity, confidence, and review requirement.

The LLM interprets checkpoint text dynamically. Application code must not hardcode expected checkpoint outcomes. Deterministic tools provide network, arithmetic, parsing, accessibility, and comparison facts.

## Hackathon Boundaries

### Included

- Bundled, versioned checkpoint guide.
- Up to five submitted public Dell PDP URLs.
- Playwright-rendered extraction.
- Page-zone classification.
- Runtime checkpoint retrieval.
- One checkpoint per DSX call.
- Deterministic fact tools.
- MongoDB persistence.
- In-process asynchronous jobs.
- Three-second frontend polling.
- Cross-page and run-over-run comparison.
- Daily schedule with named timezone.
- Explicit schedule and recipient confirmation.
- Browser report and optional SMTP delivery.
- Controlled EN-CA, EN-US, and FR-CA fixtures.

### Deferred

- Redis and distributed workers.
- SSE.
- Recursive crawling.
- Authenticated WIP pages.
- Runtime checkpoint upload/editor.
- Vector database.
- Arbitrary cron syntax.
- Scheduling and recurring runs.
- Email delivery and SMTP.
- SMTP retry workflow.
- Retention deletion job.
- Multi-user authentication.
- Automatic PDP modification.
- Full WCAG/EAA certification.

## Runtime Architecture

- React, Vite, and TypeScript frontend.
- FastAPI and Pydantic v2 backend.
- MongoDB persistence.
- Playwright Chromium acquisition.
- Dell GenAI gateway via `csoutils[ai]` DSXClient (OpenAI-compatible) and recorded evaluator adapter.
- In-process `asyncio.Queue` worker.
- Docker Compose local runtime.

## API Contract

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/chat` | Parse message and return clarification, confirmation, query answer, or accepted action |
| POST | `/api/commands/{id}/confirm` | Confirm schedule or recipient mutation |
| GET | `/api/framework` | Return bundled rule version and ingestion state |
| POST | `/api/audits` | Create validated Audit Definition |
| POST | `/api/audits/{id}/runs` | Queue Run Now |
| GET | `/api/runs/{id}/status` | Poll aggregate and per-page progress |
| GET | `/api/runs/{id}/issues` | Filter findings |
| GET | `/api/runs/{id}/report` | Return shared report model |
| GET | `/api/runs/{id}/comparison` | Return page/run comparison |
| POST | `/api/schedules` | Create confirmed daily schedule |
| PATCH | `/api/schedules/{id}` | Update, pause, or resume schedule |
| POST | `/api/schedules/{id}/run-now` | Queue occurrence without changing recurrence |
| GET | `/api/schedules` | List schedules and next runs |

All errors use:

```json
{
  "error": {
    "code": "RULE_DOCUMENT_INVALID",
    "message": "Checkpoint section could not be indexed.",
    "details": [{"path": "section_9", "reason": "missing heading"}],
    "request_id": "request-id",
    "retryable": false
  }
}
```

## Phase 0 — Design Baseline

Goal:

Make approved decisions repository-owned before implementation.

Changes:

- Create focused design specification.
- Add `GLOSSARY.md` defining Audit Definition, Audit Run, Page Snapshot, Rule Passage, Check Result, Finding Identity, Observation, Coverage, and Comparison Status.
- Add ADR for dynamic agentic checkpoint application.
- Add ADR for in-process hackathon runtime.
- Mark broad 2026-10-02 design as production roadmap superseded for hackathon delivery.

Gate:

- No TBD placeholders.
- No contradictions between focused design, ADRs, and this plan.
- Markdown lint passes.

## Phase 1 — DSX Capability Spike

Goal:

Resolve DSX assumptions before provider implementation.

Changes:

- Add opt-in `backend/scripts/probe_dsx.py`.
- Probe exact model ID.
- Probe JSON object and JSON schema response modes.
- Measure representative 2–5 KB request latency.
- Confirm context-window/input limit: 6K tokens.
- Identify sustained and burst rate limits.
- Record authentication/configuration variable names without secrets.
- Use `csoutils[ai]` DSXClient as Dell GenAI gateway adapter (OpenAI-compatible).
- Define provider-neutral `AiEvaluator` interface.

### Decision Rules

- Use native JSON mode if confirmed (gateway supports it).
- Otherwise use prompt JSON, tolerant parsing, Pydantic validation, one retry, then conservative first-object extraction.
- If DSX is unavailable, use recorded adapter for demo and mark live language checks `not_evaluated`.
- Configure concurrency from measured limits.
- No end-user authentication; backend authenticates via client credentials (`DSX_CLIENT_ID`, `DSX_CLIENT_SECRET`, `DSX_AUTH_METHOD`).
- TLS verification uses OS trust store (carries Dell corporate CAs); optional `DSX_CA_BUNDLE` for custom PEM.

Gate:

Provider strategy and non-secret findings recorded in ADR and environment example.

## Phase 2 — Workspace Scaffold

### Backend

Create:

- `backend/pyproject.toml`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/errors.py`
- Package initializers.
- Backend smoke test.

Use Python 3.12, FastAPI, Pydantic v2, async MongoDB adapter, Playwright, `csoutils[ai]` DSXClient, pytest, Ruff, and BasedPyright.

### Frontend

Create React/Vite/TypeScript app with:

- Strict TypeScript.
- App shell.
- Typed API client.
- Test setup.
- Health screen.

### Runtime

Create Docker Compose services for API, web, MongoDB, and Mailpit. Do not add Redis. Use `csoutils[ai]` DSXClient as Dell GenAI gateway adapter with DSX_BASE_URL, DSX_CLIENT_ID, DSX_CLIENT_SECRET, DSX_AUTH_METHOD, DSX_MODEL, DSX_VERIFY_TLS, DSX_JSON_MODE, and DSX_TIMEOUT_SECONDS environment variables. No end-user authentication.

Gate:

- Backend health test passes.
- Frontend tests and production build pass.
- Docker services report healthy.

## Phase 3 — Domain and API Contracts

Goal:

Freeze shared contracts before adapters and UI.

### Domain Models

Implement:

- `AuditDefinition`
- `PageTarget`
- `AuditRun`
- `PageSnapshot`
- `RulePassage`
- `CheckResult`
- `IssueIdentity`
- `IssueObservation`
- `Schedule`
- `ScheduleOccurrence`
- `DeliveryAttempt`
- Report DTOs

Statuses:

- Runs: `queued`, `running`, `partial`, `completed`, `failed`, `cancelled`.
- Checks: `pass`, `issue`, `not_applicable`, `not_evaluated`, `error`.
- Coverage: `scanned`, `failed`, `skipped` with reason.
- Comparison: `new`, `unresolved`, `resolved`, `not_rechecked`.

Tests first:

- Invalid audit mode.
- Sixth URL rejected.
- Duplicate URL rejected.
- Invalid locale.
- Invalid severity.
- Illegal run state transition.
- Shared error serialization.

Gate:

OpenAPI generates, frontend types match, and domain tests pass without MongoDB or browser.

## Phase 4 — Bundled Checkpoint Knowledge

Goal:

Use supplied checkpoint guide as runtime source of truth.

Changes:

- Store normalized source at `backend/app/rules/npl-pdp-audit-guide.md`.
- Preserve exact meaning and wording.
- Split by heading/checkpoint while preserving source range and hierarchy.
- Add curated metadata manifest for mode, locale, topic, and page-zone tags.
- Calculate framework version from normalized document hash.
- Build metadata and lexical retrieval.
- Auto-load/reindex when source hash changes.

### Required Coverage

- Global responsibilities and questions.
- Sprint/Launch rules.
- R2 rules.
- R3 rules.
- Detailed Sections 1–15.
- Regional spelling and measurement tables.
- Trademark list.
- Under-discussion reminders.
- Native-speaker reminders.

Tests first:

- Every expected section parses.
- Exact source quotation round-trips.
- R3 FR-CA query retrieves localization rules.
- R2 EN-US query excludes irrelevant non-English rules.
- Global reminders always appear when applicable.

Gate:

`GET /api/framework` returns source hash, version, passage count, and ingestion warnings.

## Phase 5 — Controlled Fixtures and URL Policy

### Fixtures

Create Dell-like EN-CA, EN-US, and FR-CA fixture pages containing:

- Hero and product identity.
- Configuration cards.
- Detailed Tech Specs.
- Dimensions and weight.
- Ports and slots.
- Media gallery.
- Footnotes.
- Legal trademark footer.
- Accessibility attributes.

Create second-run variants with one new, unresolved, resolved, not-rechecked, and content-only change.

### URL Policy

Implement before Playwright:

- HTTPS only.
- Approved Dell hosts.
- No userinfo.
- Approved ports only.
- Reject IP literals and private/reserved DNS results.
- Revalidate redirects.
- Limit redirects.
- Fixture-host allowance only in test/development.

Tests first:

Allowed Dell URL, deceptive subdomain, private IP, private DNS response, unsafe port, redirect escape, duplicate canonical URL, and locale extraction.

Gate:

Security tests pass before browser fetcher accepts URLs.

## Phase 6 — Playwright Acquisition and Extraction

### Acquisition Limits

- Maximum five URLs.
- Maximum two concurrent browser pages.
- Minimum two-second same-host start delay.
- 30-second render timeout.
- 60-second total page budget.
- Bounded response size and redirects.

### Page Zones

Extract:

- `global_header`
- `breadcrumbs`
- `pdp_hero`
- `media_gallery`
- `configuration_selector`
- `configuration_cards`
- `tech_specs`
- `features`
- `dimensions_weight`
- `ports_slots`
- `reviews`
- `support`
- `footnotes_disclaimers`
- `global_footer`
- `legal_trademarks`

### Evidence

Extract product identity, ordered fragments, headings, lists, specs, dimensions, ports, footnotes, links, images, media, trademarks, accessibility facts, stable locators, final URL, and warnings.

Expand known Tech Specs/accordions. Never buy, add to cart, submit forms, or authenticate.

### Hashing

Hash normalized PDP zones, visible text, specs, dimensions, links, and asset identities. Exclude global shell, legal boilerplate, prices, promotions, ratings, scripts, tokens, timestamps, recommendations, and known dynamic blocks. Store extraction-policy version and per-zone hashes.

Tests first:

Zone boundaries, repeated-text deduplication, legal/footer isolation, locator fallback, hidden section warning, timeout, malformed page, and dynamic-noise hash stability.

Gate:

Three fixtures produce approved snapshot golden files.

## Phase 7 — Deterministic Fact Tools

Implement independently:

- Localized unit parser and converter.
- Spec normalizer and diff.
- Footnote reference graph.
- Trademark occurrence and adjacent-symbol scanner.
- Bounded link/image/media checker.
- Accessibility fact extractor.
- Date/number/currency parser.
- Language heuristic.
- Cross-page normalized field diff.

Deterministic tools return facts. LLM applies checkpoint meaning. Broken resources and calculations can produce direct findings only when mapping is unambiguous.

Gate:

Pure tests cover supplied examples and researched EN-CA, EN-US, and FR-CA excerpts. Network tests use fixture server only.

## Phase 8 — Agent Evaluator

### Workflow

1. Build page × zone × checkpoint matrix.
2. Retrieve applicable exact checkpoint passage.
3. Gather bounded visible text, DOM facts, nearby context, and deterministic facts.
4. Call DSX once for that checkpoint.
5. Validate structured response.
6. Retry malformed response once.
7. Apply conservative JSON fallback when needed.
8. Reject unsupported citations.
9. Deduplicate and order findings.

### Required Response

- Outcome.
- Problem.
- Suggested correction.
- Proof text.
- Severity.
- Exact rule quote.
- Exact evidence quote.
- DOM locator.
- Confidence.
- Review-required flag.

### Grounding Rules

- Rule quote must exist in retrieved passage.
- Evidence quote must exist in extracted fragment.
- Locator must resolve.
- Subjective localization findings require native-speaker reminder.
- Repeated malformed output becomes `error`.
- Insufficient evidence becomes `not_evaluated`.

Tests first:

Valid pass/issue/not-evaluated, malformed recovery, repeated malformed output, fabricated rule citation, fabricated evidence, prompt injection, duplicate candidates, low-confidence native review, timeout, and recorded-adapter determinism.

Gate:

No ungrounded candidate reaches issue observations.

## Phase 9 — Audit Orchestration and MongoDB

Changes:

- Implement repository interfaces and MongoDB adapters.
- Add indexes for run queries and unique schedule occurrences.
- Implement in-process `asyncio.Queue` worker under FastAPI lifespan.
- Persist progress after each stage.
- Process up to five page jobs with two-browser concurrency.
- Mark interrupted running jobs failed/recoverable on startup.
- Implement polling status DTO.

Tests first:

State transitions, partial page failure, evaluator failure, restart recovery, duplicate occurrence, and Mongo repository contracts.

Gate:

Run endpoint returns immediately and polling reaches a terminal state while preserving partial failures.

## Phase 10 — Comparison Engine

Changes:

- Compare configuration/top specs to full Tech Specs.
- Compare invariant fields across locale pages.
- Treat price, currency, promotions, ratings, keyboards, services, and configuration availability as market-sensitive unless rules say otherwise.
- Align localized prose by zone/heading rather than string equality.
- Build comparable-run key from URLs, locales, mode, rule version, extraction version, and prompt version.
- Separate issue identity from observation.

### Transition Rules

- New: current issue absent previously.
- Unresolved: same identity persists.
- Resolved: prior issue absent only after successful current recheck.
- Not rechecked: current page/check failed or was not evaluated.
- Changed page: normalized page/zone hash changed independently.

Gate:

Second fixture run matches approved transition truth table exactly.

## Phase 11 — Conversation and Result Queries

Changes:

- Parse audit, run, query, and schedule intents into typed commands.
- Backend validates all URLs, modes, timezones, recipients, and IDs.
- Missing timezone always creates clarification.
- Schedule/recipient mutation creates pending confirmation.
- Confirmation performs action exactly once.
- Query intents map to repository filters.
- Answers use only returned records.
- Deterministic parser handles sample prompt; DSX can enrich but never bypass validation.

Tests first:

Exact sample prompt, missing timezone, invalid mode, five/six URLs, duplicate confirmation, high-severity France query, and empty-result hallucination prevention.

Gate:

Sample prompt confirms and runs three URLs with correct mode and locales.

## Phase 12 — React Experience

Build in this order:

1. App shell and typed API client.
2. Chat composer and parsed-request card.
3. Timezone clarification and confirmation.
4. Polling progress with per-page stages.
5. Report summary, filters, issue cards, rule/evidence trace, and proof-copy action.
6. URL tabs and side-by-side comparison.
7. Schedule list, actions, and SMTP state.

Use `@dds/react` 3.2.0 components and bundled DDS styles/tokens for controls, cards, tabs, badges, progress, messages, typography, spacing, grid, focus, and elevation. Add persistent `Light` / `Dark` / `System` theme control, apply DDS `dds--light-mode` or `dds--dark-mode` at application scope, persist the selection, and subscribe to system preference changes for System mode. Use semantic DDS tokens for every custom surface and text color. Use DDS AI variants only for the agent prompt and audit action. Treat `DDSTable` as optional because it is alpha; provide a DDS-card/semantic-table fallback. Keep custom CSS limited to dashboard composition, evidence highlights, and comparison visualization. Use semantic controls, visible focus, keyboard navigation, status announcements, and responsive laptop layout. Never render unsanitized HTML.

### Tests

Clarification, confirmation, progress, partial/error, report filtering, evidence navigation, proof-copy payload, polling termination, and schedule actions.

Gate:

User completes sample flow without developer tools. Frontend tests, lint, type check, and build pass.

## Phase 14 — End-to-End Demo

### Seeded Findings

- Locale spelling difference.
- FR-CA English fragment.
- Dimension/unit problem.
- Top/full-spec mismatch.
- Missing trademark.
- Broken footnote.
- Broken link/image.
- Unsupported superlative.
- DOM accessibility problem.

### Demo Path

1. Paste three-URL R3 request.
2. Confirm and Run Now.
3. Poll three page stages.
4. Open rule retrieval trace.
5. Inspect exact checkpoint and page evidence.
6. Copy proof text.
7. Open side-by-side comparison.
8. Run second fixture version and show transitions.

Recorded evaluator mode must be visibly identified. Live DSX/pages remain optional smoke path.

Gate:

Automated E2E completes request through report and comparison.

## Phase 14 — Documentation, Security, and Final Verification

### README

Document prerequisites, setup, environment variables, architecture, fixture demo, optional DSX/live setup, commands, limits, and production roadmap.

### Security

Verify SSRF and redirects, HTML escaping, prompt injection resistance, log redaction, secret scanning, dependency scanning, and Snyk code scanning. Fix introduced findings and rescan.

### Final Commands

- Backend tests.
- Ruff.
- BasedPyright.
- Frontend tests.
- Frontend lint.
- TypeScript type check.
- Frontend production build.
- Docker health checks.
- Fixture E2E.
- Optional bounded live smoke.
- Secret scan.
- Snyk scan.

Do not claim success when a required command fails. Unavailable external checks must be reported as unavailable, not passed.

## Coding-Agent Guardrails

- Follow phase order.
- Build contracts and fixtures before UI.
- Keep provider types inside adapters.
- Do not hardcode checkpoint outcomes.
- Do not send full raw HTML to DSX.
- Do not treat failures as passes.
- Do not resolve findings after failed checks.
- Do not crawl recursively or leave approved hosts.
- Do not execute purchase, form, or authentication actions.
- Do not send real email in tests.
- Do not add deferred infrastructure without reopening scope.
- Run narrow tests and inspect diff at every phase gate.

## Completion Criteria

1. LLM dynamically reads bundled checkpoint passages.
2. Every confirmed finding contains exact rule and page evidence.
3. Three locale fixtures audit under correct R3 profiles.
4. Polling works without Redis/SSE.
5. Comparisons avoid false resolutions and market-difference false positives.
6. Browser report is complete.
7. MongoDB preserves rule, extraction, model, prompt, facts, and findings provenance.
8. Controlled E2E passes.
9. Tests, lint, types, builds, Docker checks, and security scans pass.
