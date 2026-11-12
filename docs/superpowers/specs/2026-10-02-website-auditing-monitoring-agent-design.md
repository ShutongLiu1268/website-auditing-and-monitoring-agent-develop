# Spec: Website Auditing and Monitoring Agent

**Date:** 2026-10-02

**Status:** Superseded by hackathon-focused design

**Repository state:** Initial scaffold; implementation files do not yet exist.

**Note:** This broad production-oriented spec is superseded by the focused hackathon design in `docs/superpowers/specs/2026-10-05-npl-agentic-pdp-audit-hackathon-design.md`. This document remains as a post-hackathon roadmap for production features including scheduling, email delivery, distributed workers, and full WCAG/EAA certification.

## Objective

Build a single-user web application that audits multiple country and locale scopes on `www.dell.com` against a versioned guideline framework, stores evidence and issue history, answers questions about completed audits through chat, and turns an audit into a recurring monitoring job with HTML email delivery.

The product is valuable because it combines website quality checks with conversational workflow control and longitudinal monitoring. A static scanner reports one point in time. This system explains what changed, distinguishes new, unresolved, resolved, and not-rechecked issues, and lets a web team manage the workflow from chat.

### Feasibility verdict

The use case is technically viable for a hackathon when constrained to:

- One allowed page origin: `www.dell.com`.
- Multiple logical country or locale scopes represented by path prefixes, not multiple hostnames.
- Up to five scopes and 25 pages per scope for the demo.
- Public live scans for the product demonstration.
- Controlled fixtures or mocked crawler responses for deterministic acceptance tests.
- One supplied JSON framework version instead of silently inventing R2, R3, or Audit Review definitions.
- Technical checks performed deterministically and language/context checks performed through the Dell DSX OpenAI-compatible client.

Live public pages cannot guarantee fixed grammar errors, broken assets, or controlled day-to-day changes. Therefore, public scans prove real crawling and coverage behavior; controlled fixtures prove seeded findings and comparison transitions.

## Users and primary outcomes

### Primary user

A web or localization reviewer responsible for several country or locale areas of the Dell public website.

### Primary outcomes

1. Configure multiple locale/path scopes and expected languages.
2. Run a bounded audit with visible progress and coverage limitations.
3. Inspect evidence-backed findings and filter them through chat.
4. Schedule recurring scans with explicit time, converted UTC time, scope, framework version, and recipients.
5. Receive a report that focuses attention on changed and actionable issues rather than repeating an undifferentiated static list.

## MVP scope

### Included

- Single demo workspace and single user; no authentication or role management.
- Multiple logical scopes on `https://www.dell.com`.
- Standard locale path mapping for `/en-us/`, `/fr-fr/`, and `/es-es/`, with configuration overrides.
- Seed URLs, include paths, exclude paths, expected locale, page limit, and approved Dell asset-host allowlist per scope.
- Playwright-based browser rendering.
- Same-origin page discovery restricted to `www.dell.com`.
- `robots.txt` compliance, bounded concurrency, per-host throttling, response limits, browser timeouts, and coverage reporting.
- PostgreSQL persistence with 30-day retention for snapshots and related evidence.
- Redis-backed background worker for crawl, audit, comparison, report, and delivery jobs.
- Immutable, versioned JSON guideline framework upload and framework selection.
- Deterministic checks for technical findings such as HTTP failures, broken links, and broken images.
- DSX evaluation for grammar, language, and contextual rules through an OpenAI-compatible adapter.
- `pass`, `issue`, `not_evaluated`, and `error` check outcomes.
- Evidence, confidence, and `review_required` fields for AI findings; no human approval workflow in MVP.
- Conversational filtering and comparison queries against stored results.
- Common recurring schedules: daily, weekdays, and weekly at a specified time.
- Named timezone input converted once to UTC at schedule creation; both source input and conversion are displayed. Future runs use the stored UTC time and do not adjust for future DST changes.
- Schedule create, update, pause, resume, delete, and run-now actions.
- Schedule mutations require explicit confirmation. Audit runs start after valid input without an additional confirmation. Run-now uses an existing schedule and does not mutate its recurrence, so it does not require schedule-mutation confirmation.
- Stable issue identities and comparable-run comparison.
- HTML email report through SMTP plus a browser report table.
- Delivery result persistence, bounded retry, and visible delivery failure.
- React/Vite/TypeScript web interface with chat, SSE progress, report table, and schedule views.
- Docker Compose runtime for frontend, API, worker, PostgreSQL, and Redis.

### Excluded from MVP

- Arbitrary user-supplied domains or subdomain crawling.
- Authenticated or private websites.
- Slack, Teams, or other notification channels.
- Multi-user workspaces, permissions, assignment, and approval workflows.
- Automatic website content changes.
- Screenshot evidence.
- Full SEO or accessibility conformance certification.
- An arbitrary cron editor.
- Hardcoded or assumed definitions for R2, R3, or Audit Review.
- Guaranteed defect counts on live Dell pages.

## User journeys and acceptance criteria

### Configure and start an audit

1. User submits two or more Dell locale/path seed URLs in chat.
2. System creates or updates logical scopes with name, locale, include paths, exclude paths, and page limit.
3. User uploads a JSON framework or selects an existing imported framework version.
4. System displays the effective scope: seeds, locale mappings, limits, exclusions, framework name/version, and known crawl restrictions.
5. User starts the audit.
6. System enqueues one idempotent run and streams progress through SSE.
7. System reports discovered, scanned, skipped, blocked, timed-out, and failed pages.
8. System labels incomplete coverage as a partial scan.

### Evaluate pages

For each successfully retrieved applicable page and framework rule, the system records:

- Page URL.
- Logical scope and locale.
- Guideline ID and framework version.
- Category.
- Issue description.
- Evidence.
- Severity.
- Recommended fix.
- Evaluation method.
- Confidence and review flag where applicable.
- Check outcome.

Technical rules use deterministic checks. Grammar, language, and contextual rules use DSX. Retrieval failures never become passes. A check that cannot be evaluated is `not_evaluated`.

### Review results conversationally

The chat must support filters and questions by:

- Logical scope or country.
- Locale.
- Guideline ID or category.
- Issue type.
- Severity.
- Current comparison status.
- Run or date.

Examples:

- “Show only high-priority problems.”
- “Show all broken links.”
- “Which country scope has the most localization issues?”
- “What changed compared with the previous completed scan?”

Answers are generated from database query results. The model must not invent findings that are absent from stored results.

### Create and operate monitoring schedule

A request such as “Run this every morning at 8 AM Eastern and email the report to webteam@example.com” must:

1. Resolve the referenced audit definition.
2. Parse recurrence, time, source timezone, and recipients.
3. Convert the requested time to UTC once.
4. Show the schedule, UTC conversion, scope, framework version, and recipients.
5. Require explicit confirmation.
6. Persist one schedule and one next-run value.
7. Avoid duplicate schedules when the same message is retried.

The user can update, pause, resume, delete, or run a schedule now through chat. A run-now action creates one occurrence for the selected schedule and does not alter its recurrence.

### Compare scans

A current run is comparable only when its scope definitions, path rules, page limits, and framework version match the previous run's comparison key. The report must disclose non-comparability instead of presenting an unqualified day-to-day comparison.

Status definitions:

- **New:** issue identity appears in current comparable run but not previous comparable run.
- **Unresolved:** same issue identity remains present.
- **Resolved:** previous issue is absent after the relevant page and rule completed successfully in the current run.
- **Not rechecked:** current run could not evaluate the relevant page or rule. It must not be marked resolved.
- **Changed page:** current page content hash differs from previous comparable run; tracked separately from issue status.

### Deliver email report

Each report contains:

- Run time and UTC display.
- Selected scopes and locale mappings.
- Framework name and version.
- Scanned page count.
- Inaccessible, blocked, skipped, timed-out, and failed page count.
- Partial-scan notice when applicable.
- Total issues by severity.
- Total issues by comparison status.
- New, unresolved, resolved, and not-rechecked totals.
- Detailed issue table with page URL, guideline ID, category, issue description, evidence, severity, recommended fix, and change status.

SMTP success and failure are stored. Failed deliveries can be retried without rerunning the audit.

## Architecture

### Runtime modules

- **Web module:** React/Vite/TypeScript chat, progress, report, and schedule interface.
- **HTTP module:** FastAPI endpoints for chat, frameworks, audit definitions, runs, reports, issues, schedules, SSE, and delivery retry.
- **Chat module:** Converts natural-language messages into typed intents through DSX, validates fields, manages clarification state, and controls schedule confirmation.
- **Crawl module:** Applies scope, robots, URL, throttling, and rendering policy through a Playwright adapter.
- **Framework module:** Validates, versions, stores, and selects JSON framework definitions.
- **Evaluation module:** Dispatches deterministic and DSX rule evaluators and normalizes check outcomes.
- **Comparison module:** Computes issue identity, compatible-run checks, status transitions, and page changes.
- **Persistence module:** Owns PostgreSQL schema, migrations, retention, and transaction boundaries.
- **Job module:** Owns Redis queue contracts, retries, progress events, and idempotency.
- **Report module:** Builds a report model and renders browser and HTML email representations.
- **Notification module:** Sends through an SMTP adapter and records delivery attempts.

### Interfaces and adapters

The following seams keep provider and infrastructure changes local:

- `Crawler` interface with Playwright and fixture adapters.
- `AiEvaluator` interface with DSX and deterministic test adapters.
- `MailSender` interface with SMTP and test-sink adapters.
- `JobQueue` interface with Redis and in-memory test adapters.
- `Clock` interface for recurrence and deterministic comparison tests.

Callers use domain-level request and result types. They do not depend on Playwright, DSX SDK objects, SMTP clients, or Redis primitives.

### Data flow

```text
Chat message
  -> typed intent and validated slots
  -> persisted audit definition or schedule command
  -> Redis job
  -> crawler
  -> page snapshots and coverage events
  -> deterministic and DSX checks
  -> issue observations and page changes
  -> compatible-run comparison
  -> report model
  -> SSE/web report and optional SMTP delivery
```

### Idempotency

- Audit runs have a unique run ID and a request idempotency key.
- Schedule occurrences have a unique `(schedule_id, occurrence_key)` constraint.
- Delivery attempts have a unique report/recipient/attempt key.
- Worker retries re-use existing IDs instead of creating replacement domain records.
- Schedule creation stores a command fingerprint so a retried chat request cannot create an unintended duplicate.

## Domain model

### SiteScope

Stores:

- Logical scope name.
- One or more seed URLs.
- Expected BCP 47 locale.
- Include path prefixes.
- Exclude path prefixes.
- Per-scope page limit.
- Approved asset hosts.
- Active/inactive state.

A scope is logical and can share the `www.dell.com` hostname with other country scopes. Page discovery never crosses to another page origin.

### FrameworkVersion

Stores:

- Framework ID and display name.
- Immutable semantic version string.
- Upload source and timestamp.
- Validated rule set.
- Content hash.

Each rule contains:

```json
{
  "id": "LINK-001",
  "category": "technical",
  "description": "All internal links return a successful response.",
  "applicability": {"content_types": ["html"]},
  "severity": "high",
  "evaluator": "deterministic",
  "criteria": "HTTP status is 200–399 after approved redirects.",
  "evidence_requirements": ["target_url", "http_status"],
  "recommended_fix": "Update or remove the link.",
  "identity_strategy": "page_rule_target_status"
}
```

Allowed evaluator types are `deterministic` and `dsx`. Allowed severities are `critical`, `high`, `medium`, `low`, and `info`. The exact 20–25 rule catalog and final category allocation are an input that must be supplied before production audit-engine acceptance. The importer and evaluator contract can be built before that catalog arrives.

### AuditDefinition and AuditRun

`AuditDefinition` snapshots selected scopes, scope configuration, and framework version. `AuditRun` references the snapshot and stores trigger type, status, timestamps, progress counters, comparison parent, and aggregate counts.

### PageSnapshot and CoverageEvent

`PageSnapshot` stores canonical URL, final URL, HTTP status, retrieval/render state, title and metadata, content hash, sanitized HTML, and capture timestamp. `CoverageEvent` stores every blocked, skipped, timeout, redirect rejection, robots denial, or retrieval failure with a machine-readable reason.

Sanitized HTML removes scripts, forms, embedded active content, and other unnecessary executable content before persistence. Snapshot and evidence records follow the 30-day retention policy.

### CheckResult and IssueObservation

A check result stores page, rule, evaluator method, outcome, evidence, confidence, review flag, and error details. An issue observation stores the report-facing fields for a finding in one run.

Issue identity is separated from observations. The base fingerprint is:

```text
hash(logical_scope_id + canonical_page_url + rule_id + normalized_issue_subject)
```

Identity strategies include:

- Broken link: page + rule + normalized target URL + failure class.
- Broken image: page + rule + normalized asset URL.
- Grammar/language: page + rule + stable DOM locator + normalized offending span.

### Schedule and delivery

`Schedule` stores recurrence, original time input, original timezone label, converted UTC time, selected audit definition, recipients, state, next run, and last run. `ScheduleOccurrence` and `DeliveryAttempt` provide retry and idempotency records.

## Chat contract

DSX produces a typed intent, never a direct side effect:

```json
{
  "intent": "schedule_create",
  "slots": {
    "audit_definition_id": "audit_123",
    "recurrence": "daily",
    "time": "08:00",
    "timezone_input": "Eastern Time",
    "recipients": ["webteam@example.com"]
  },
  "missing_fields": [],
  "confidence": 0.96
}
```

Supported intents:

- Configure, add, and remove a site scope.
- Upload and select a framework.
- Preview and start an audit.
- Filter and compare results.
- Create, update, pause, resume, and delete a schedule.
- Run a schedule now.
- Retry failed delivery.

The backend validates every intent, asks for missing fields, rejects unsupported operations, and confirms schedule mutations. Chat result responses use query output and report models as their source of truth.

## Crawler behavior

1. Validate seed URLs as HTTPS `www.dell.com` URLs.
2. Reject userinfo, non-standard unsafe ports, private or reserved IP targets, and non-HTTPS schemes.
3. Revalidate every redirect against the same page-origin policy.
4. Fetch and cache `robots.txt` for the allowed origin.
5. Apply include and exclude path rules before queueing a page.
6. Canonicalize URLs by removing fragments, normalizing host casing, and applying the configured query policy.
7. Deduplicate before retrieval.
8. Render pages with Playwright under bounded browser and response timeouts.
9. Extract page text, links, images, metadata, HTTP results, and sanitized HTML.
10. Check image URLs only on an explicit approved Dell asset-host allowlist; do not crawl those hosts as pages.
11. Evaluate link targets only on `www.dell.com`; external link targets are `not_evaluated` and never expand page scope.
12. Record every limit, denial, timeout, and failed retrieval as coverage data.

The default demo limit is five scopes, 25 pages per scope, and a five-minute target for a normal run. The report may be partial when public-site response time, robots rules, or rendering cost prevents full coverage.

## Evaluation behavior

- Deterministic checks run without DSX when the rule evaluator is `deterministic`.
- DSX receives bounded page content, rule criteria, locale, and required evidence shape as data.
- Page content is explicitly untrusted and cannot override system instructions or invoke tools.
- DSX output is schema-validated. One bounded retry handles malformed output; repeated malformed output becomes `error`, while provider timeout, provider unavailability, or a missing response becomes `not_evaluated`.
- AI confidence is stored and displayed. Low-confidence findings may be marked `review_required`; MVP does not require approval before showing or counting them.
- Rule applicability prevents irrelevant checks from being reported as failures.

## Reporting and notifications

The report module consumes a report model containing summary counts, coverage, comparison metadata, and issue observations. It renders:

- Web summary cards and sortable/filterable issue table.
- HTML email with executive summary followed by detailed issue table.
- Partial-scan and non-comparable-run warnings.

The SMTP adapter receives only validated recipient addresses and rendered report content. It records response code, error class, attempt number, and final delivery state. Retry is bounded and does not enqueue another audit.

## Frontend behavior

The web UI contains:

- Chat panel with conversation history and structured clarification prompts.
- Scope/framework setup view.
- Live run progress view backed by SSE with reconnect and final-state refresh.
- Report summary and issue table with filters for scope, locale, guideline, category, severity, status, and run.
- Schedule view showing recurrence, original input, converted UTC time, recipients, state, next run, and actions.
- Delivery status and retry action.

The UI displays partial coverage and non-comparability prominently. It does not claim that a page passed when its checks were not evaluated.

## Security and privacy

### Always enforce

- HTTPS `www.dell.com` page-origin allowlist.
- Redirect revalidation.
- Private-network and unsafe-port rejection.
- Robots compliance.
- Bounded page, response, browser, concurrency, and rate limits.
- Sanitized snapshot storage and escaped report rendering.
- DSX, SMTP, PostgreSQL, and Redis secrets only through environment or approved secret stores.
- No secret, full page body, or credential in logs.
- Untrusted page content isolated from DSX control instructions.
- 30-day snapshot/evidence retention and deletion job.

### Threats addressed

- SSRF through submitted or redirected URLs.
- Prompt injection through page content.
- Duplicate schedules or emails after worker retry.
- HTML/script injection through issue evidence.
- Accidental crawling outside approved origin or robots policy.
- Credential exposure in logs or source control.

## Testing strategy

### Unit tests

Cover URL policy, robots decisions, canonicalization, scope limits, framework validation, rule dispatch, issue fingerprinting, comparison truth tables, partial-scan resolution gates, recurrence conversion, typed intent validation, report totals, HTML escaping, and retry state.

### Integration tests

Use PostgreSQL migrations, Redis job adapters, SSE event streams, mocked DSX responses, Playwright against controlled fixture pages, and fake SMTP delivery. Inject malformed DSX output, timeout, blocked page, 404 link, failed image, partial scan, and SMTP failure.

### End-to-end acceptance

Controlled fixtures must demonstrate:

- Grammar error.
- Broken link.
- Broken image.
- Wrong-language content.
- New issue.
- Existing unresolved issue.
- Resolved issue after successful recheck.
- Not-rechecked issue after failed or skipped recheck.
- Changed page with unchanged issue status.
- Chat filters and comparisons.
- Schedule confirmation and idempotent mutation.
- Run-now execution.
- Email delivery and retry.

A public Dell smoke test verifies real browser retrieval, scope enforcement, robots handling, coverage reporting, and report generation. It must not assert a particular live defect.

## Tech stack and commands

### Proposed stack

- Python 3.12 backend.
- FastAPI and Pydantic for HTTP and typed contracts.
- SQLAlchemy and Alembic for PostgreSQL persistence and migrations.
- Redis-backed worker queue.
- Playwright for browser rendering.
- DSX OpenAI-compatible client behind `AiEvaluator`.
- SMTP behind `MailSender`.
- React, Vite, and TypeScript frontend.
- Docker Compose for all local services.
- Pytest, Ruff, and BasedPyright for verification.

The DSX integration follows the documented `DSXClient` provider patterns and environment-based client authentication. Documentation reference: `https://documentation.cqa-r2-np.kob.dell.com/csoutils/ai/`.

### Commands

```text
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api pytest
docker compose exec api ruff check .
docker compose exec api basedpyright
docker compose exec web npm run build
```

CI runs the same checks plus integration and end-to-end suites with fixture adapters. Live public-site smoke tests remain opt-in and bounded.

## Proposed project structure

```text
docker-compose.yml
.env.example
backend/
  pyproject.toml
  app/
    main.py
    api/
    chat/
    crawl/
    evaluation/
    framework/
    comparison/
    jobs/
    persistence/
    reporting/
    notifications/
    domain/
  migrations/
  tests/
    unit/
    integration/
    e2e/
frontend/
  package.json
  src/
    components/
    features/chat/
    features/audits/
    features/reports/
    features/schedules/
    lib/
docs/
  superpowers/specs/
  superpowers/plans/
```

Each module owns one concept and exposes typed interfaces at its seam. Provider-specific implementation stays in adapters. Test fixtures and fakes implement those same interfaces.

## Code style

Python uses typed snake_case names, Pydantic models for external data, small functions with one responsibility, explicit result states, and async I/O at network seams. React components use PascalCase, hooks use `useX` names, and shared API types are generated or manually kept in sync with backend contracts.

Example:

```python
class AuditScope(BaseModel):
    name: str
    seed_urls: list[AnyHttpUrl]
    locale: str
    page_limit: PositiveInt = 25


def is_comparable(previous: AuditRun, current: AuditRun) -> bool:
    return previous.comparison_key == current.comparison_key
```

Do not log secrets or raw page content. Keep browser, DSX, Redis, and SMTP client details out of domain modules.

## Boundaries

### Always do

- Validate every external input at the seam.
- Preserve partial coverage and not-evaluated states.
- Use immutable framework versions in audit definitions.
- Keep issue observations and issue identity separate.
- Use idempotency keys for runs, schedule occurrences, and delivery attempts.
- Run unit, integration, and relevant end-to-end tests before commit.
- Keep secrets in environment configuration and run secret/security scans before push.

### Ask first

- Changing the allowed page origin or approved asset-host policy.
- Adding a framework rule category or changing rule severity semantics.
- Changing PostgreSQL schema or retention behavior.
- Adding a provider, dependency, notification channel, or authentication system.
- Changing schedule timezone semantics or comparison status definitions.
- Changing Docker, CI, or deployment configuration.

### Never do

- Commit DSX, SMTP, database, or Redis credentials.
- Crawl arbitrary domains, private addresses, or disallowed robots paths.
- Treat failed retrieval or incomplete evaluation as a pass or resolution.
- Use live public content as the only regression oracle.
- Let DSX output execute tools or bypass URL and schedule validation.
- Send duplicate emails because of a worker retry.
- Remove failing tests to make the pipeline pass.

## Success criteria

The MVP is complete when all conditions hold:

1. A user can configure multiple `www.dell.com` locale/path scopes.
2. A valid JSON framework can be uploaded, versioned, selected, and referenced by an audit run.
3. Invalid framework files receive actionable validation errors.
4. A run stays within configured scope and reports successful and failed coverage.
5. Controlled fixtures produce evidence-backed grammar, broken-link, broken-image, and wrong-language findings.
6. Reports contain every required summary and detailed issue field.
7. Chat answers filters and comparisons from stored data.
8. Schedule requests show recurrence, recipients, scope, framework, and UTC conversion before confirmation.
9. Schedule mutations are idempotent and support pause, resume, delete, update, and run-now.
10. A second comparable fixture run distinguishes new, unresolved, resolved, not-rechecked, and changed-page states correctly.
11. Scheduled or run-now reports are sent through SMTP and delivery failures are visible and retryable.
12. Container restart preserves PostgreSQL audit history and schedule state.
13. Public Dell smoke scans remain within origin, robots, rate, and page limits.
14. Verification commands pass for backend tests, lint, type checking, frontend build, and integration/e2e fixtures.

## Open inputs and decision gates

These inputs are intentionally external to the architecture and must be supplied before their dependent implementation tasks can close:

1. **Guideline catalog:** exact rule IDs, count, descriptions, applicability, severities, criteria, evidence examples, recommended fixes, and identity strategies. The framework importer and test contract can be implemented first; production audit acceptance requires the supplied catalog.
2. **DSX runtime details:** model ID, approved base URL, authentication mode, and structured-output capability. Credentials must be provided through local secret configuration, never in the repository.
3. **SMTP details:** relay host/port/security mode, sender identity, recipient allowlist, and retry policy limits.
4. **Demo scope list:** initial Dell seed URLs, exact path exclusions, and approved Dell asset hosts. Standard locale paths are the default starting point.
5. **Judging environment:** whether live Dell smoke access, DSX access, SMTP access, and Docker are available during the demo.

## Review gate

This document is the source of truth for planning. User review must resolve changes to scope, domain policy, framework contract, schedule semantics, and acceptance criteria before an implementation plan is created.
