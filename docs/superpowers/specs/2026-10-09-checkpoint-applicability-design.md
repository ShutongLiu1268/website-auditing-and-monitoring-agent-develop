# Checkpoint applicability declared in the guide

- **Status:** Design approved 2026-10-09. Spec review pending.
- **Builds on:** ADR-0001 (the Markdown guide is the source of truth; passages are tagged at parse time).
- **Reference:** `docs/checkpoints-by-profile.md` (65 checkpoints, their source items, and open items).

## Problem

Measured on the real guide with the current code:

- Applicability is inferred by keyword and substring matching in `RuleIngestor`. `"de"` matches "description" and tags the checkpoint as German. Result: en-US and en-CA match 0 checkpoints in every profile.
- Headings starting "R2 reviews..." or "R3 reviews..." become section headers. The real "R2 REVIEW: Global English Reviews" heading is dropped.
- A checkpoint with no zone tag runs in every extracted zone (up to 14), including footer and legal zones.
- Ingestion tests use small synthetic guides. No test runs the real guide through retrieval, so none of this failed the suite.

## Goals

1. Each checkpoint's profiles, markets, zones, evaluator, and review rules are declared once, in the guide.
2. One selection function: `select(profile, locale, zone)`.
3. The real guide is tested for every profile.

## Non-goals

- Demo fixture findings stay hardcoded.
- Output format, HTML dashboard, chat flow, and DSX prompt wording are unchanged.

## Design

### 1. Checkpoint header

Each checkpoint gets one hidden HTML comment directly under its heading. Keys are plain `key: value` lines, so no YAML dependency is needed.

```
<!-- checkpoint
id: SPR-07
profiles: sprint_launch
markets: en-US
zones: all
evaluator: llm
review: never
-->
```

| Key | Values | Meaning |
|---|---|---|
| `id` | SPR-01..SPR-23, R2G-01..R2G-16, R3R-01..R3R-11, D1..D15 | Stable ID. Replaces heading-derived IDs. |
| `profiles` | `sprint_launch`, `r2`, `r3` (comma list) | Profiles that run this checkpoint. |
| `markets` | `global`, a locale tag (`en-US`), a group name (`EMEA`), or a comma list of these | Locales it runs on. `global` means all. |
| `zones` | `all`, or a comma list of zone names from `zone_extractor.py` | Zones it reads. `all` means every extracted zone. |
| `evaluator` | `llm`, `hybrid`, `code` | `hybrid` means it needs fact-tool results. `code` is the existing name for deterministic checks. |
| `review` | `never`, `always`, or a locale tag (`en-CA`) | When findings need native-speaker review. |
| `reminder` | optional text | Shown with findings from this checkpoint. |

Missing keys, unknown values, unknown zone names, unknown group names, and duplicate IDs fail at startup.

### 2. Market groups

One block at the top of the guide, parsed together with the checkpoints. Explicit lists, no nested groups:

```
<!-- market-groups
EMEA: en-GB, en-IE, fr-CH, de-CH, it-CH, fr-BE, nl-BE, de-AT, nl-NL, es-ES, it-IT, nb-NO, da-DK, sv-SE, fr-FR, de-DE
APJC: en-AU, en-NZ, en-MY, en-SG, en-IN, en-HK, en-PH, en-PK, th-TH, vi-VN, id-ID
METRIC_MM: en-GB, en-IE, fr-CH, de-CH, it-CH, fr-BE, nl-BE, de-AT, nl-NL, es-ES, it-IT, nb-NO, da-DK, sv-SE, fr-FR, de-DE, en-AU, en-NZ, en-MY, en-SG, en-HK, en-PH, en-PK, th-TH, vi-VN, id-ID
IN: en-IN
EAST_ASIA_METRIC: ja-JP, ko-KR, zh-CN, zh-TW, zh-HK
IMPERIAL: en-US, en-CA, fr-CA
UK_ENGLISH: en-GB, en-IE, en-AU, en-NZ, en-MY, en-SG, en-IN, en-HK
FRENCH: fr-FR, fr-CA, fr-BE, fr-CH
NON_IMPERIAL: every locale not in IMPERIAL
NON_ENGLISH: every locale whose language is not en
-->
```

- `METRIC_MM` is the D3 mm-only rule: EMEA and APJC, minus en-IN, which has its own cm-first rule.
- Market matching is case-insensitive. Group names expand at selection time.

### 3. Ingestion

- Parse the market-groups block and each checkpoint block. Checkpoint text stays verbatim, from one header to the next, so citations match the source.
- Passage `id` = header `id`. `heading_path` keeps the guide section and checkpoint headings for display.
- Remove keyword inference for locale, zone, mode, topic, evaluator, and severity; remove heading-prefix detection and the R3 default.
- Any validation error fails application startup.

### 4. Selection

`select(profile, locale, zone)` returns the passages where all three hold:

1. `profile` is in the passage's `profiles`.
2. Market: `global` matches any locale. Otherwise the locale equals a tag, or belongs to a group.
3. Zone: `all` matches any zone. Otherwise the zone is in the passage's zone list.

Removed: language fallback, `_ZONE_ALIASES`, and the topic filter. The live path never passes a topic. Guide zone names must match the extractor names exactly, so no alias map is needed.

### 5. Evaluator and review

- One checkpoint per DSX call, unchanged (ADR-0001).
- `hybrid` checkpoints receive fact-tool results (dimensions, units, links, footnotes, accessibility, trademarks).
- When a result is built, `review_required` is set if the checkpoint's `review` is `always`, or matches the page locale. The checkpoint's `reminder` is copied onto the finding as a new `reminder` field on `CheckResult` and `IssueResponse`.
- en-CA spelling (SPR-06, R2G-03, R3R-01, D1) uses `review: en-CA`. The model judges Canadian English with no hand-written list, and those findings require review.

### 6. Comparison identity

Finding identity includes the rule passage ID. IDs change at migration, so runs made before the migration cannot be compared with runs made after it. GLOSSARY already requires the same rule-catalog version for comparable runs, so this is expected.

### 7. Data model

`RulePassage` changes:

- `modes` holds profiles, using the existing `AuditMode` values.
- `locales` is replaced by `markets`, the declared tokens. Groups expand at selection time.
- `zones` holds exact zone names. Empty means all.
- `evaluator_type`, `review`, and `reminder` come from the header. `review` replaces `review_required` as the declared rule. The per-finding `review_required` is computed when the result is built, from `review` and the page locale.
- `topics` is kept. The optional `topics` header key feeds the deterministic fact runner. Selection never filters on topics.
- `countries` is removed. Nothing reads it.
- `severity` stays as it is today: not declared.

### 8. Tests

- Real-guide ingestion: 65 checkpoints, all headers valid, IDs unique.
- Real-guide selection, checked against `docs/checkpoints-by-profile.md`, for sprint_launch/en-US, r2/en-US, r3/en-CA, r3/fr-CA, r2/fr-FR, r3/de-DE, r3/ja-JP, and r2/zh-CN. The current zero-match case becomes a failing test before the fix.
- Group expansion: EMEA, APJC, METRIC_MM excludes en-IN, IMPERIAL is exactly en-US, en-CA, fr-CA, NON_IMPERIAL is the complement, NON_ENGLISH.
- Validation: a missing key, unknown zone, unknown group, and duplicate ID each fail startup.
- Replace the heading-based assertions in `test_ingestion.py` with header-based ones. Update `test_retriever.py` and `test_live_page_service.py` to the selection interface.

### 9. Content work (reviewed as a diff)

- Sync the guide text to the 7.13 docx.
- Add one header per checkpoint. Items not listed below use `markets: global` and `review: never`.
- Draft the `zones` and `evaluator` values for each checkpoint. Review them in the diff.
- Fix "digitilization" to "digitalization" in the D1 table.
- Change the German date example in D15 to "22. April 2026".
- Add Arc™ to the D9 detect list.

Items with a non-default header:

| ID | markets | review | reminder |
|---|---|---|---|
| SPR-06 | global | en-CA | |
| SPR-07 | en-US | never | |
| SPR-23 | NON_IMPERIAL | never | |
| R2G-03 | global | en-CA | |
| R2G-04 | en-US | never | |
| R2G-06 | NON_IMPERIAL | never | |
| R2G-07 | EMEA, APJC | never | |
| R2G-08 | ja-JP | never | |
| R2G-13 | zh-CN | never | |
| R2G-16 | EMEA, APJC, ja-JP | never | |
| R3R-01 | global | en-CA | |
| R3R-03 | NON_IMPERIAL | never | |
| R3R-04 | IMPERIAL | never | |
| R3R-05 | ja-JP | never | |
| R3R-06 | NON_ENGLISH | never | |
| R3R-09 | NON_ENGLISH | never | |
| R3R-10 | EMEA | never | |
| R3R-11 | UK_ENGLISH | never | |
| D1 | global | en-CA | |
| D3 | global | never | Rule not finalized and in discussion. |
| D5 | global | never | Rule not finalized and in discussion. |
| D8 | zh-CN | never | |
| D9 | global | never | Check that the keywords carry the correct trademark symbol. |
| D10 | APJC | never | |
| D11 | global | always | Only native speakers should recommend alternative copy; otherwise seek the translations team. |
| D12 | global | always | Same as D11. |
| D13 | global | always | Same as D11. |
| D14 | FRENCH | always | Same as D11. |
| D15 | NON_ENGLISH | always | Same as D11. |

### 10. Migration and rollout

- Ingestion writes passages keyed by `(id, version)`. Re-ingesting the same version must not create duplicates. Verify the current `create_many` behavior during planning.
- The ID and version change at migration, so comparisons restart there.
- Merge only after the guide diff is reviewed.

### 11. Decisions from the design conversation

| Topic | Decision |
|---|---|
| Source of applicability | Markdown in repo; ADR-0001 kept |
| Unit of a checkpoint | One per numbered item: 65 total (Sprint/Launch 23, R2 31, R3 26) |
| Market scope | Global by default; markets only where the item names them |
| Zone scope | Declared list per checkpoint; default all |
| en-CA spelling | Model judges Canadian English; findings flagged for review |
| cm rule | mm only (D3); R2G-07's cm option dropped |
| EMEA and APJC | From the source: APJC from the D1 note; EMEA from the D3 European markets, plus fr-FR and de-DE from the French and German examples |
| Imperial | en-US, en-CA, fr-CA only |
| 3-syllable rule | US English only (SPR-07, R2G-04) |
| R3 checklist (R3R-07) | Detailed sections D1 to D15 |
| "World's best" | Flagged in every market |
| IN | Its own group (cm first, inch in brackets) |
| Locale tags | Draft table in section 2, approved |
