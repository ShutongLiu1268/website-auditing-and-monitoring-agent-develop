# NPL Agentic PDP Audit — Hackathon Design

**Date:** 2026-10-05

**Status:** Approved for implementation


## Objective

Build a focused hackathon MVP where an LLM dynamically retrieves and applies bundled Sprint/Launch, R2, or R3 PDP checkpoints to extracted page evidence. The system audits up to five public Dell PDP URLs, compares content across locales and runs, and presents evidence-backed findings in an interactive dashboard.


## Use Case


### Users

Product Launch Managers, R2/R3 auditors, localization reviewers, and PDP developers.


### Problem

Reviewers manually inspect multiple localized PDPs, interpret changing checkpoint guidance, compare specs/translations, collect evidence, and repeat reviews. Generic scanners lack Dell PDP/locale context; giant LLM prompts lose evidence and exceed context limits.


### Solution

A conversational web application where users submit URLs and review mode. The system renders pages, extracts structured content, retrieves relevant checkpoint passages, and uses Dell DSX to dynamically apply one checkpoint at a time. Every finding cites exact checkpoint text and exact page evidence. Cross-page and run-over-run comparisons track changes.


## Confirmed Hackathon Scope


### Included

- Bundled/versioned checkpoint guide auto-loaded on startup.
- Up to five submitted public Dell PDP URLs; demo uses three.
- Playwright rendering and zone-aware extraction.
- Runtime checkpoint retrieval and one-rule-per-call DSX evaluation.
- Deterministic link/image/unit/spec/DOM fact tools.
- Evidence-backed interactive report table/dashboard.
- Shared API and error contracts.
- MongoDB audit history.
- Cross-page locale/spec comparison.
- Second-run new/unresolved/resolved/not-rechecked comparison.
- Chat queries that filter persisted findings.
- Browser HTML report.


### Deferred

- Redis worker and distributed queue.
- SSE; use 3-second polling.
- Recursive crawl.
- Authenticated WIP pages.
- Runtime rule uploads/editor.
- Arbitrary cron expressions.
- Scheduling and recurring runs.
- Email delivery and SMTP.
- SMTP retry workflow.
- 30-day deletion job.
- Full coverage-event taxonomy.
- Broad idempotency system.
- Full WCAG/EAA certification.
- Automatic PDP correction/publishing.


## Agentic Checkpoint Application


### Bundled rule source

Store supplied guide as immutable Markdown source with version/hash. On startup, parse into passages while preserving exact original text and hierarchy. Each passage stores stable ID, version, heading path, source range, modes, locale/country tags, topic tags, applicable page zones, and original text.


### Retrieval

For each page zone, retrieve passages by audit mode, URL/document locale, zone, and detected topics. Use metadata plus lexical matching. Always include applicable global rules and mandatory reminders.


### One-checkpoint-per-call workflow

1. Planner builds page × zone × checkpoint matrix.
2. For each applicable checkpoint, gather bounded visible text, structured DOM facts, nearby context, and deterministic fact-tool output.
3. DSX applies that exact checkpoint to that evidence.
4. Pydantic validates response.
5. One retry follows malformed JSON.
6. If needed, fallback extracts first JSON object and validates it.
7. Repeated malformed output becomes `error`; insufficient evidence becomes `not_evaluated`.
8. Evidence verifier rejects issue lacking exact checkpoint quote, exact page quote, and locator.
9. Reconciler deduplicates findings and preserves top-to-bottom PDP order.


### LLM input

Send extracted text/DOM facts, never full raw HTML. Target 2–5 KB section chunks within 6K-token model budget. Input includes URL, locale, zone, exact checkpoint, deterministic facts, and JSON schema. Page/rule content is untrusted data and cannot issue instructions or trigger tools.


### Required response

```json
{
  "outcome": "pass | issue | not_evaluated",
  "problem": "...",
  "suggested_correction": "...",
  "proof_text": "...",
  "severity": "critical | high | medium | low",
  "rule_quote": "exact checkpoint text",
  "evidence_quote": "exact page text",
  "dom_locator": "...",
  "confidence": 0.0,
  "review_required": false
}
```

No exact rule/page citation means no confirmed issue.


## DSX Configuration

- Dell GenAI gateway via `csoutils[ai]` DSXClient (OpenAI-compatible)
- Client-credentials OAuth: `DSX_CLIENT_ID`, `DSX_CLIENT_SECRET`, `DSX_AUTH_METHOD` (default: `client`)
- Secondary `DSX_API_KEY` for compatibility
- Environment variables: `DSX_BASE_URL`, `DSX_MODEL` (default: `gpt-oss-120b`), `DSX_VERIFY_TLS` (default: `true`), `DSX_JSON_MODE` (default: `true`), `DSX_TIMEOUT_SECONDS` (default: `60.0`)
- TLS verification uses OS trust store (carries Dell corporate CAs); optional `DSX_CA_BUNDLE` for custom PEM
- 6K-token context limit
- No end-user authentication; backend authenticates via client credentials
- Temperature 0 for repeatable audit results
- One checkpoint per call (batching deferred to post-hackathon optimization)
- JSON-object response mode enabled (gateway supports it)
- Token usage recorded per check result
- Bounded concurrency from measured rate limits


## Deterministic Fact Tools

Tools provide facts; LLM applies retrieved checkpoint:
- Link/image/media status.
- Unit parser/converter and tolerance.
- Top/configuration/full-spec normalization and diff.
- Footnote reference graph.
- DOM accessibility facts: names, labels, alt, headings, landmarks, duplicate IDs, tabindex.
- Language heuristic.
- Trademark occurrence/adjacency.
- Date/number/currency parser.
- Cross-page field diff.

Broken links/images and numeric calculations become direct deterministic findings when rule mapping is unambiguous.


## PDP Extraction


### Zones

`global_header`, `breadcrumbs`, `pdp_hero`, `media_gallery`, `configuration_selector`, `configuration_cards`, `tech_specs`, `features`, `dimensions_weight`, `ports_slots`, `reviews`, `support`, `footnotes_disclaimers`, `global_footer`, `legal_trademarks`.


### Extracted evidence

Product name/model/SKU/offer ID/locale/currency, ordered visible fragments with heading/list context, configuration and detailed specs, dimensions/weight raw and parsed values, ports/slots, footnote references/definitions, links/assets/media and status/attributes, accessibility facts and semantic relationships, trademark mentions with adjacent characters, stable DOM locator and text fingerprint, render/fetch state, final URL, capture time, extraction warnings.


### Browser limits

Maximum five submitted URLs, maximum two concurrent browser pages, minimum two-second same-host start delay, 30-second render timeout, 60-second total per-page budget, bounded response size and redirect count, public HTTPS Dell hosts only, revalidate redirects and reject private/reserved targets, expand Tech Specs/known accordions but never buy, add to cart, submit forms, or authenticate.


### Content hash

Compute hash over normalized extracted PDP content only: include ordered PDP zones, visible text, normalized specs, dimensions, links, and asset identities; exclude global header/footer, legal boilerplate, price/promotions/ratings by default, scripts, session tokens, timestamps, recommendations, and known dynamic blocks; normalize whitespace and Unicode; store extraction-policy version with hash. Also retain per-zone hashes.


## Comparison Semantics

- **New:** issue identity now present, absent in previous comparable run.
- **Unresolved:** same issue remains.
- **Resolved:** previous issue absent only after relevant page/check completed successfully.
- **Not rechecked:** page/check failed or was not evaluated; never resolved.
- **Changed page:** normalized PDP/per-zone hash changed; tracked separately.

Cross-page comparison distinguishes invariants (model, dimensions, chassis/port facts, core feature claims) from market-sensitive information (price, currency, offer ID, promotions, keyboard/service, configuration availability, ratings). Localized prose aligns by zone/heading; do not expect string equality.

Issue identity: URL/locale + rule passage ID + zone + stable locator/normalized subject. Observation remains separate from identity.


## Conversation Flow

For sample request:
1. Parse mode and URLs.
2. Validate URL count, public Dell origin, duplicates, and locale paths.
3. Preview mode, URL/locales, and rule version.
4. Persist Audit Definition.
5. Queue run.
6. Frontend polls run status every three seconds.
7. Render report.


## Architecture


### Modules

Conversation: typed intent and clarification state. Audit Definition: mode, URLs/locales, rule version, comparison key. Acquisition: URL policy and Playwright behind `PageFetcher`. Extraction: DOM/templates to normalized `PageSnapshot`. Rule Knowledge: bundled-document parser/index/retrieval. Agent Audit: planner, evaluator, verifier, reconciler behind `AuditAgent`. Fact Tools: deterministic evidence utilities. Comparison: intra-page, cross-page, previous-run. Jobs: in-process `asyncio.Queue`/background runner and status persistence. Reporting: shared dashboard model. Persistence: Mongo repositories.


### Runtime

React/Vite/TypeScript, FastAPI/Pydantic, MongoDB, Playwright Chromium, Dell GenAI gateway via `csoutils[ai]` DSXClient (OpenAI-compatible, 6K context), Docker Compose. No Redis in hackathon runtime.


## API Contract

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/chat` | Parse message; return clarification, query answer, or accepted action |
| GET | `/api/framework` | Bundled rule version and ingestion status |
| POST | `/api/audits` | Create Audit Definition from structured input |
| POST | `/api/audits/{id}/runs` | Queue Run Now |
| GET | `/api/runs/{id}/status` | Poll aggregate/per-page progress |
| GET | `/api/runs/{id}/issues` | Filter by URL/locale/category/severity/status/rule |
| GET | `/api/runs/{id}/report` | Shared report model |
| GET | `/api/runs/{id}/comparison` | Page/run comparison |


### Shared error envelope

```json
{
  "error": {
    "code": "RULE_DOCUMENT_INVALID",
    "message": "Checkpoint section could not be indexed.",
    "details": [{"path": "section_9", "reason": "missing heading"}],
    "request_id": "...",
    "retryable": false
  }
}
```

Use stable codes for validation, URL policy, acquisition, extraction, DSX, and persistence failures.


## Persistence

Collections: `rule_versions`, `rule_passages`, `conversations`, `audit_definitions`, `audit_runs`, `page_snapshots`, `agent_audit_batches`, `check_results`, `issue_identities`, `issue_observations`.

Persist retrieved passages, prompt template/model, response hash, tool facts, validation/retry outcome, and extraction version. No retention deletion job in hackathon MVP.

Run statuses: `queued`, `running`, `partial`, `completed`, `failed`, `cancelled`.
Check outcomes: `pass`, `issue`, `not_applicable`, `not_evaluated`, `error`.
Coverage states: `scanned`, `failed(reason)`, `skipped(reason)`.


## Dashboard and Report

Summary by severity/category/page/locale/status. URL tabs and side-by-side comparison. Polling progress with per-page stages. Clickable issue cards in PDP source order. Reconstructed page content and exact highlights. Yellow: format/spelling/grammar/trademark/footnotes/dimensions. Red: translation/language/meaning/tone/naturalness. Orange: spec/cross-page inconsistency. Every card: original text, problem, correction, proof, severity, confidence, exact checkpoint citation, locator/evidence, evaluator. Filters by page, locale, category, rule, severity, transition, review-required. Rule-retrieval trace for demo transparency. Browser report always available.

### DDS UI Foundation

Use DDS React components as the primary UI library and DDS design tokens for color, spacing, typography, grid, focus treatment, and elevation. Use DDS components for buttons, text areas, selects, tabs, badges, cards, progress, message bars, and labels. Use DDS AI variants only on the agent-specific prompt and audit action surface. Treat `DDSTable` as optional because DDS marks it alpha; findings may use DDS cards and a semantic table fallback. Custom CSS is limited to dashboard composition, evidence highlights, and comparison visualization. Pin the compatible `@dds/react` version and import bundled DDS styles from the package. Provide a persistent `Light` / `Dark` / `System` selector; apply DDS `dds--light-mode` or `dds--dark-mode` at application scope, listen for system preference changes in System mode, and use semantic DDS tokens for all custom surfaces so no light/dark mismatch remains.


## Hackathon Demo

1. Paste three-URL R3 request.
2. Confirm and Run Now.
3. Polling screen shows three pages rendering/extracting/auditing.
4. Rule trace shows exact checkpoint retrieved for each zone.
5. Demonstrate locale spelling applicability, FR-CA residual English, dimensions/weight, one DOM accessibility issue, and spec difference.
6. Open finding to exact page evidence and exact checkpoint; copy proof edit.
7. Show cross-page expected vs actionable differences.
8. Run second fixture version to show new/unresolved/resolved/not-rechecked.

Controlled Dell-like fixtures and recorded DSX responses are deterministic demo path. Live sample URLs remain optional smoke demo; defect counts are not guaranteed.


## Files to Change


### Existing

- `README.md` — replace placeholder with MVP setup/demo/architecture.
- `docs/superpowers/specs/2026-10-02-website-auditing-monitoring-agent-design.md` — mark production roadmap/superseded for hackathon.


### New docs

- `GLOSSARY.md`
- `docs/adr/0001-agentic-rule-application.md`
- `docs/adr/0002-hackathon-runtime.md`


### Backend

- `backend/pyproject.toml`
- `backend/app/main.py`, `config.py`, `errors.py`
- `backend/app/domain/models.py`
- `backend/app/rules/npl-pdp-audit-guide.md`
- `backend/app/rule_knowledge/{ingestion,index,retriever}.py`
- `backend/app/agent/{orchestrator,evaluator,verifier,reconciler,schemas}.py`
- `backend/app/tools/{units,links,footnotes,accessibility,language,trademarks,localization,specs}.py`
- `backend/app/acquisition/{interface,url_policy,playwright_fetcher}.py`
- `backend/app/extraction/{page_extractor,zones,locators,hashing}.py`
- `backend/app/conversation/*`, `audits/*`, `comparison/*`, `jobs/*`, `reporting/*`, `persistence/*`, `api/*`
- `backend/tests/{unit,integration,e2e}/...`


### Frontend/runtime

- React features for chat, polling progress, rule trace, report, and comparison.
- `.env.example`, `docker-compose.yml`, fixture pages, and recorded DSX fixtures.


## Implementation Sequence

1. Write focused approved spec, glossary, ADRs; mark broad spec roadmap.
2. Execute DSX spike and record model/rate/JSON/context decisions.
3. Normalize bundled guide and build retrieval tests.
4. Scaffold backend/frontend/MongoDB/Playwright.
5. Define domain, API, errors, and agent schemas.
6. Build URL policy and zone-aware extractor against fixtures/live-page structures.
7. Build deterministic fact tools test-first.
8. Build one-checkpoint DSX evaluator, fallback parsing, verifier, reconciler.
9. Build comparisons and normalized hashing.
10. Build repositories, in-process jobs, and polling status.
11. Build chat/progress/rule-trace/report/comparison UI.
12. Build three-locale and second-run demo fixtures.
13. Update README and rehearse controlled/live-safe demo.
14. Run verification and security scan.


## Verification


### Rule/agent

Every guide section indexed with exact text/source. Retrieval includes required mode/locale/zone passages and reminders. One checkpoint per call respects token budget. JSON mode and fallback parser paths tested. Missing/mismatched citations reject candidate. Conflicting rules become review-required/not-evaluated. Prompt injection cannot alter schema or trigger side effects.


### Extraction/tools

Zones exclude shell/legal noise appropriately. Stable locators and normalized hashes ignore configured dynamic blocks. Unit/spec/footnote/link/image/accessibility facts correct. Two-page concurrency, delay, and timeout limits enforced. Redirect/SSRF policy enforced.


### End-to-end

Sample prompt confirms and runs three URLs. Polling reaches terminal state after partial success/failure. Findings link checkpoint and page evidence. Chat filters persisted results. Second run shows valid transitions; failed recheck never resolves. Browser report always works.

Commands: backend `pytest`, `ruff check .`, `basedpyright`; frontend tests/lint/typecheck/build; Docker health; controlled E2E; Snyk code scan, fix, and rescan.


## Risks and Mitigations

- LLM inconsistency: one-rule calls, temperature 0, strict schema, retry, exact citations, verifier, deterministic tools.
- Context limits: extracted zone text only; measured token budget.
- Rate limits: day-one spike and bounded concurrency.
- Rule retrieval miss: metadata+lexical retrieval, mandatory rules, coverage tests, visible trace.
- False positives from shell/legal: zone applicability.
- Locale/config differences: invariant vs market-sensitive comparison classes.
- Live instability: controlled fixtures and optional live smoke.
- In-process job loss on restart: persisted statuses detect interrupted runs; accepted hackathon limitation documented.


## Success Criteria

1. LLM dynamically reads retrieved bundled checkpoints; checkpoint behavior is not hardcoded into evaluator code.
2. Every confirmed LLM finding has exact rule and exact page evidence.
3. Three sample URLs audit under correct R3 locale profiles.
4. Progress works through polling without Redis/SSE.
5. Cross-page and run-over-run comparisons avoid false resolutions and obvious market-difference false positives.
6. Browser report is complete.
7. MongoDB preserves extraction, rules, model/prompt, facts, and findings provenance.
8. Controlled E2E demo passes; live smoke remains bounded.
9. Tests, lint, types, builds, Docker checks, and Snyk scan pass.
