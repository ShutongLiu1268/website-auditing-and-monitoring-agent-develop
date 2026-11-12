# Checkpoints by profile

Source: `7.13 Global PDP Content R2 & R3 Audit Bot Database.docx`. Text reviewed; wording stays close to the source. The repo guide (`backend/app/rule_knowledge/npl-pdp-audit-guide.md`) is similar but not identical. For example, the "digitilization" row exists only in the docx.

Scope column:
- **Global**: applies to every locale.
- **Market: X**: the checkpoint text names these markets.
- **Open**: the source does not define the markets. See Open items.

## Profile map

| Profile | Checkpoints | Count |
|---|---|---|
| Sprint/Launch | SPR-01 to SPR-23 | 23 |
| R2 | R2G-01 to R2G-16, plus D1 to D15 | 16 + 15 |
| R3 | R3R-01 to R3R-11, plus D1 to D15 | 11 + 15 |

D1 to D15 are the source's "R2 & R3 PDP Audit: Detailed Sections 1-15". The source says to run them for R2 and R3 audits. Sprint/Launch uses only its own list.

## Sprint/Launch (SPR)

| ID | Checkpoint | Scope |
|---|---|---|
| SPR-01 | Dimensions order: Height (front and rear height if applicable), Width, Depth, Weight, Starting weight (if applicable), Max weight (if applicable) | Global |
| SPR-02 | Dimensions and weight bullets in sentence case | Global |
| SPR-03 | Ports and slots bullets follow sentence case (product names excepted) | Global |
| SPR-04 | Repetitive headers: inline banner matches the product offering (source example: Intel processors PDP with an Intel inline banner) | Global |
| SPR-05 | Superlatives, e.g. most, the most, world's best, thinnest, fastest (flagging rule in D6) | Global |
| SPR-06 | Spelling and grammar errors (English variants in D1) | Global |
| SPR-07 | Words with more than 3 syllables | Open (R2G-04 limits it to US English) |
| SPR-08 | Differences between tech specs and PDP dimensions and weight (see D4) | Global |
| SPR-09 | Configuration callouts not offered globally | Global |
| SPR-10 | Missing imagery | Global |
| SPR-11 | Accessibility issues (WCAG or EAA, per the role section) | Global |
| SPR-12 | Broken links | Global |
| SPR-13 | Broken videos or animations | Global |
| SPR-14 | Inch notation: spell out "inch" in measurements; avoid "in." except in dimensions and weight; no " for inch | Global |
| SPR-15 | Tech specs values as a list, not a paragraph | Global |
| SPR-16 | Space between each value and its unit | Global |
| SPR-17 | Round to two decimal places where decimals appear; leading zero when the value is under 1.00 | Global |
| SPR-18 | Claims that would need testing (example: "dropped from 48 inches over 3000 times") | Global |
| SPR-19 | Every footnote reference (¹, ², ...) has a matching explanation (see D7) | Global |
| SPR-20 | Orphan notes (see D7) | Global |
| SPR-21 | Broken or mismatched references (see D7) | Global |
| SPR-22 | Trademark accuracy: brand or product name missing ™ or ® (keyword list in D9) | Global |
| SPR-23 | Imperial units within body text are localized | Open (markets not named) |

## R2 Global English Review (R2G)

| ID | Checkpoint | Scope |
|---|---|---|
| R2G-01 | Repetitive headers | Global |
| R2G-02 | Superlatives (most, the most, world's best, thinnest, fastest) | Global |
| R2G-03 | Spelling and grammar with variants: UK, IE, AU, NZ, MY, SG, IN, HK use UK English (e.g. customisation); PH, PK, TH, VN, ID use US English (e.g. customization) | Market: UK/IE/AU/NZ/MY/SG/IN/HK = UK; PH/PK/TH/VN/ID = US (en-CA: see Open 6) |
| R2G-04 | Words with more than 3 syllables (readability and accessibility) | Market: US English content only; not regions |
| R2G-05 | Differences between tech specs and PDP dimensions and weight (see D4) | Global |
| R2G-06 | Imperial units within text are localized | Open |
| R2G-07 | EMEA and APJC: metric first, imperial in brackets (example: mm or cm first, inches in brackets) | Market: EMEA and APJC (membership open) |
| R2G-08 | JP: metric only, kg and mm; no inch or lbs | Market: JP |
| R2G-09 | Claims that would need testing | Global |
| R2G-10 | Every footnote reference has an explanation (see D7) | Global |
| R2G-11 | Orphan notes (see D7) | Global |
| R2G-12 | Broken or mismatched references (see D7) | Global |
| R2G-13 | China content has no Copilot references (see D8) | Market: CN |
| R2G-14 | Trademark symbol check (see D9) | Global |
| R2G-15 | Unit value accuracy: convert inches to mm (1 inch = 25.4 mm) and compare each value pair on the PDP | Global |
| R2G-16 | Weight and dimension format: EMEA and APJC metric first, imperial in brackets; JP metric only (see D3) | Market: EMEA, APJC, JP |

## R3 Regional Review (R3R)

| ID | Checkpoint | Scope |
|---|---|---|
| R3R-01 | Spelling and grammar errors (variants as R2G-03) | Global |
| R3R-02 | Improper units of measure for the region (unit rules in D3) | Global |
| R3R-03 | Metric for metric regions | Open (no region list) |
| R3R-04 | Imperial for imperial regions | Open (no region list) |
| R3R-05 | JP: metric only, kg and mm; no inch or lbs | Market: JP |
| R3R-06 | English words on non-English pages | Market: non-English locales |
| R3R-07 | Callout any points from the R3 Checklist | Open ("R3 Checklist" is not defined) |
| R3R-08 | Callout any URLs with missing content | Global |
| R3R-09 | EN-US links on non-English pages | Market: non-English locales |
| R3R-10 | Monitors: EMEA profiles must have energy labels | Market: EMEA; product: monitors |
| R3R-11 | Identify countries that use UK English and make sure it is implemented | Market: UK-English markets (see D1) |

## R2 & R3 Detailed Sections (D1-D15)

Run for R2 and R3. Each group keeps the source rules.

### D1 Spelling check (English variants)
- Scope: UK/IE/AU/NZ/MY/SG/IN/HK use UK English; PH/PK/TH/VN/ID use US English.
- Suggest corrections from the source's US-UK word table (reference data, not copied here).
- Flag the wrong English variant for the specified country.
- The variant rules are for APJC English pages. They do not apply to German PDPs (source note).

### D2 Spelling errors and language mismatch (Global)
- Detect English spelling mistakes.
- Find English words on non-English pages (e.g. English inside a FR or DE page).
- Find other-language words on English pages (e.g. non-English inside a UK or IE page).
- Find wrong-language words on country pages (e.g. German words on FR pages).
- List all mismatches and language fragments. Flag mistranslation or missing information.

### D3 Weight and dimension format (Market-specific; reminder: rule not finalized)
- Metric-first group (UK, IE, CH, BE, AT, NL, ES, IT, NO, DK, SE, AU, NZ, MY, SG, PK, PH, ID, VN, TH, EN-HK): dimensions in mm only, not cm; mm first with inches in brackets; inch written "in." with the period; weight in kg first, pounds in brackets, "lb" with no period. Dimension order: Height (front and rear if applicable), Width, Depth, Weight or Starting Weight (lowest and maximum).
- IN (India): cm first, then inches in brackets. Example: 40.64 cm (16-inch).
- KR, CN, TW, ZH-HK: mm only, no inch values; kg only, no pounds.
- JP: kg and mm only.
- Source examples (French, German) show the target format.
- General: tech specs as a list; space between value and unit; two decimals with a leading zero; outside dimensions and weight, APJC uses kg when weight is called out; SEO keyword lists need no final period, so do not flag a missing period.
- Tasks: wrong units, wrong unit order, missing brackets, hybrid formats; improper inch or weight notation; mm-to-inch calculation errors (up to two decimals, with an example).

### D4 Top specs vs full tech specs (Global)
- Compare the top "Tech Specs" dimensions and weight with the detailed "Dimensions and weight" section. Flag mismatches.

### D5 Inch format consistency (Global; reminder: rule not finalized)
- Use "-inch" in descriptions (e.g. "14-inch display").
- No "in" and no prime symbol inside content descriptions.
- Flag non-compliant inch notation.

### D6 Unsupported superlatives (Global, with a country list)
- Detect "most", "the most", "thinnest", "lightest", "fastest". Flag unless a disclaimer or substantiation is present.
- Avoid "World's x" claims in: UK, IE, FR, CH, BE, DE, AT, NL, ES, IT, NO, DK, SE, AU, NZ, MY, SG, PH, VN, TH, KR, CN, HK, TW.

### D7 Footnotes (tech notes) (Global)
- Each footnote reference (¹, ², ...) has an explanation. Detect orphan notes. Flag broken or mismatched references.

### D8 CN: no Copilot (Market: CN)
- Flag "Copilot" in any case.

### D9 Trademark accuracy (Global)
- Flag a brand or product name without its symbol directly after it: Intel (®), vPro (®), NVIDIA (®), Qualcomm (®), Core (™), GeForce RTX (™), Ryzen (™), Adreno (™). Scan all content, including free text. Give the corrected version.
- Keyword reminder: Intel® (R), vPro® (R), NVIDIA® (R), Qualcomm® (R), Core™ (TM), Arc™ (TM), GeForce RTX™ (TM), Ryzen™ (TM), Adreno™ (TM).

### D10 Peace of Mind module (Market: APJC)
- Remove the module for APJC.

### D11 Meaning accuracy (Global; native-speaker reminder)
- Flag text that does not clearly cover the intended message.

### D12 Tone and register (Global; native-speaker reminder)
- Use formal address where the language needs it (vous in FR, Sie in DE). Keep tone consistent and suited to the audience. Flag informal or inconsistent tone.

### D13 Naturalness (Global; native-speaker reminder)
- Flag unnatural or word-for-word translations from English. Example: "Boîtiers" should be "Sacoche"; "Manchons" should be "Housse".

### D14 Accents and diacritics (Market: French; general rule for target-language conventions; native-speaker reminder)
- French accents are mandatory (é, è, ê, à, ç, ô). Missing accents are grammatical errors. Flag missing, incorrect, or inconsistent accents.

### D15 Localization (Market: non-English markets only; native-speaker reminder)
- Dates, decimal separators, and currency follow local conventions. Examples: French "22 avril 2026"; German "22 April 2026" (see Open 10).
- Europe uses a comma decimal separator (1,5, not 1.5).
- Currency symbol, placement, and spacing are correct.
- Do not flag English formatting for English markets.

## Process notes (not checkpoints)
- Initial questions before any audit: audit type (Sprint/Launch, R2, R3), region, regional offering plan, tailoring English content, WIP vs live comparison, tech-spec comparison.
- Sprint/Launch flow: ask for the offering plan first, then the PDP content.
- R2 and R3 flow: ask for the region, then the content.
- Tailoring flow: ask for the region and content, then output against the regional checkpoints.
- Output: group by category. For each issue give the problem (quote the original text), a short suggested correction, the proof text (only the desired edit), and severity (Critical, High, Medium, Low for R2 and R3).
- HTML dashboard: Yellow = format, spelling, grammar, trademark, footnotes, dimensions; Red = translation, language, meaning, tone, naturalness (needs QA); Orange = tech-spec mismatch with top dimensions. Order top to bottom; side-by-side compare.
- Turnaround: R2 is 4 business days; R3 is 5 business days.

## Shared checkpoints across profiles
- Spelling and grammar: SPR-06, R2G-03, R3R-01, D1, D2
- Superlatives: SPR-05, R2G-02, D6
- Tech specs vs PDP dimensions: SPR-08, R2G-05, D4
- Metric and imperial units: SPR-23, R2G-06, R2G-07, R2G-16, R3R-02, D3
- Claims needing testing: SPR-18, R2G-09
- Footnotes: SPR-19 to SPR-21, R2G-10 to R2G-12, D7
- Trademarks: SPR-22, R2G-14, D9
- JP metric only: R2G-08, R3R-05, D3
- China and Copilot: R2G-13, D8
- Repetitive headers: SPR-04, R2G-01

## Open items (decide before implementation)
1. **cm in EMEA/APJC**: D3 says mm only, not cm, for the metric-first group. R2G-07 says mm or cm first. Which is right?
2. **Syllable rule scope** (SPR-07): all markets, or US English only as in R2G-04?
3. **"R3 Checklist"** (R3R-07): not defined. Assume D1 to D15?
4. **Region lists**: no imperial list (R3R-04), no metric list (R3R-03), and no EMEA or APJC membership (R2G-07, R2G-16).
5. **Imperial localization markets** (SPR-23, R2G-06).
6. **en-CA spelling standard**: no variant rule covers Canada. The UK list and the PH/PK/TH/VN/ID list do not include it. US English is implied only for US content.
7. **"World's best"** (SPR-05, R2G-02): flag in every market, or only in the D6 country list?
8. **Arc™**: in the keyword reminder, missing from the D9 detect list.
9. **Likely typo**: "digitilization" in the D1 table (digitalization or digitalisation). Check the table.
10. **German date example** "22 April 2026" (D15): German usually writes "22. April 2026". Confirm.
11. **"Not finalized" reminders** (D3, D5): keep them in every output?
