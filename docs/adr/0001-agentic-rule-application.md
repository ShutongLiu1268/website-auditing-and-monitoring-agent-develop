# ADR-0001: Agentic Rule Application

## Status

Accepted

## Context

The NPL PDP audit guide contains 15 detailed sections covering spelling, language, dimensions, trademarks, footnotes, accessibility, and more. Hardcoding each rule as a separate evaluator would make the system inflexible to guideline updates and would not demonstrate agentic reasoning.

## Decision

The system uses a bundled, versioned Markdown document as the source of truth for all Sprint/Launch, R2, and R3 checkpoints. At startup, the document is parsed into passages with preserved exact text, source ranges, and heading hierarchy. Each passage is tagged with mode, locale, country, topic, and page-zone applicability.

For each page zone, the system retrieves relevant passages by mode, locale, zone, and detected topics. The LLM receives one checkpoint at a time along with bounded page evidence and deterministic fact-tool results. The LLM must cite both the exact checkpoint text and the exact page evidence in its response. Findings without exact citations are rejected.

## Consequences

- Guideline updates only require updating the bundled document and reindexing; no code changes.
- The LLM interprets checkpoint meaning dynamically; application code must not hardcode expected outcomes.
- Deterministic tools provide network, arithmetic, parsing, and accessibility facts; the LLM applies checkpoint judgment.
- One checkpoint per call improves traceability, retry behavior, and demo debugging but increases DSX request count.
- Subjective localization findings require native-speaker review and carry a mandatory reminder.

## Alternatives Considered

- Hardcoded evaluators: rejected for inflexibility and lack of agentic demonstration.
- Batching multiple checkpoints per call: rejected for increased hallucination risk and reduced traceability.
- Vector database: not required for MVP; metadata and lexical retrieval are sufficient.

## Amendment (2026-10-10): Code Checkpoints and Gates

Accepted. Amends the Consequences bullet that says application code must not hardcode expected outcomes, for the checkpoints listed here only.

- `evaluator: code` checkpoints take their verdict from a named Python check (`check:` header key) over zone text or page facts. They make no LLM call. Use this only for deterministic predicates: regex, arithmetic, keyword, HTTP status, or DOM property. Every issue cites exact evidence and a locator.
- `evaluator: hybrid` checkpoints name a gate check. The gate returns candidate spans. No candidates means not applicable and no LLM call. Candidates are passed to the LLM as facts. A gate must be a necessary condition for an issue, so its absence proves compliance.
- `evaluator: llm` checkpoints run the LLM on every applicable zone with no code screen. Judgement-only rules stay here.
- Facts reach the LLM only through the checkpoint's `topics`. Links are never sent to the LLM.
- `zones: page` runs a code check once per audit page. It does not run per zone.
- Guide headers stay the source of truth. Startup fails if a code or hybrid checkpoint names an unregistered check, or if an llm checkpoint names one.

Reason: LLM cost was one call per checkpoint per zone, each carrying the full page facts. A pure predicate gains nothing from a model call and loses reproducibility.
