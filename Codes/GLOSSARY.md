# Glossary

## Audit Definition

A reusable configuration that stores the review mode (Sprint/Launch, R2, or R3), the set of URLs to audit, their inferred locales, the selected rule-catalog version, and the comparison key used to determine whether two runs are comparable.

## Audit Run

A single execution of an Audit Definition. Each run has a unique ID, trigger type, status, timestamps, progress counters, and a reference to the previous comparable run for comparison.

## Page Snapshot

A normalized representation of a rendered PDP page containing ordered visible fragments, structured configuration and tech specs, dimensions/weight, ports/slots, footnotes, links, media, accessibility facts, trademarks, stable DOM locators, content hash, and extraction warnings. The snapshot excludes global navigation, legal boilerplate, and known dynamic blocks to enable stable comparison.

## Rule Passage

A single checkpoint from the bundled NPL PDP audit guide. Each checkpoint has a declared header: a stable ID, the profiles that run it (Sprint/Launch, R2, R3), the markets it applies to, the page zones it reads, its evaluator (`code`, `hybrid`, or `llm`), the named check that code and hybrid checkpoints run, a review rule, and an optional reminder. A `page` zone declares a checkpoint that runs once per audit page. Market groups (for example EMEA, APJC, IMPERIAL) are declared once at the top of the guide. Nothing is inferred from heading text.

## Check Result

The outcome of applying a single rule passage to a single page snapshot. Includes the rule ID, page URL, zone, outcome, evidence, confidence, review requirement, and any error details.

## Finding Identity

A stable fingerprint that identifies an issue across runs. Computed from the URL, locale, rule passage ID, zone, stable DOM locator, and normalized subject. Separated from the observation to support comparison.

## Issue Observation

A single instance of a finding in a specific run. Stores the rule citation, page evidence, DOM locator, problem, suggested correction, proof text, severity, confidence, review requirement, and the finding identity.

## Coverage

The status of page acquisition and evaluation: `scanned` (success), `failed(reason)` (retrieval or evaluation error), or `skipped(reason)` (policy or resource limit). Partial scans are explicitly reported rather than treated as passes.

## Comparison Status

The transition state of an issue identity between comparable runs:

- `new`: present in current run, absent in previous comparable run.
- `unresolved`: same identity persists in both runs.
- `resolved`: absent in current run but present in previous run, only after successful recheck.
- `not_rechecked`: the relevant page or check failed or was not evaluated in the current run; cannot be resolved.
- `changed page`: the normalized page or zone hash changed between runs, tracked separately from issue status.

## Comparable Run

Two Audit Runs are comparable when their URL sets, locale mappings, mode, rule-catalog version, extraction-policy version, and prompt-template version match. Non-comparable runs cannot produce meaningful issue transitions.
