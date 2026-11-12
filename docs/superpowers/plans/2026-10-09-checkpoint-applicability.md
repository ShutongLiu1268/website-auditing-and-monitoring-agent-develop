# Checkpoint Applicability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task by task, inline in this session. Use superpowers:subagent-driven-development only if the user asks for subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Declare each checkpoint's profiles, markets, zones, evaluator, and review rule in the bundled guide, and replace keyword inference with one selection function, `select(profile, locale, zone)`.

**Architecture:** The Markdown guide stays the source of truth (ADR-0001). Each checkpoint gets a hidden header comment. A small parser validates headers and market groups at startup. A pure `RuleSelector` returns the checkpoints for one profile, locale, and zone. The live audit service uses the selector and sets the review flag and reminder on each finding.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, Motor (MongoDB), pytest, pytest-asyncio, ruff, basedpyright.

---

## Deviations from the approved spec

These came up while reading the code. Task 0 updates the spec to match.

1. **`topics` is kept.** `DeterministicFactRunner` reads `rule.topics` to pick its fact checks (`link`, `image`/`accessibility`, `dimensions`/`units`/`weight`). Selection still never filters on topics. A new optional header key `topics` feeds the runner.
2. **Evaluator value `code`, not `deterministic`.** `RuleEvaluatorType` already has `code`, `llm`, and `hybrid`. Production checkpoints use only `llm` and `hybrid`. No new deterministic checks are added.
3. **`countries` is removed.** Nothing reads it.
4. **Missing guide fails startup.** The old lifespan silently skipped ingestion when the guide was missing. The new lifespan raises.
5. **Reminders reach comparison items.** `IssueObservation` also gets `reminder`, so comparison findings carry it. The spec only named `CheckResult` and `IssueResponse`.

## Repository state

The working tree has uncommitted edits from the user in many files, including `frontend/src/App.tsx`, `frontend/src/App.css`, `backend/app/audits/demo_fixtures.py`, and several tests. **Stage only the files each task lists. Never run `git add -A` or `git add .`.** Confirm with the user before switching branches, because uncommitted edits are present.

## File map

Create:
- `backend/app/rule_knowledge/markets.py`: market groups and matching.
- `backend/app/rule_knowledge/checkpoint_header.py`: header and group parsing and validation.
- `backend/app/rule_knowledge/selection.py`: `RuleSelector`.
- `backend/tests/unit/test_markets.py`
- `backend/tests/unit/test_checkpoint_header.py`
- `backend/tests/unit/test_selection.py`
- `backend/tests/unit/test_rule_passage_repository.py`
- `backend/tests/unit/test_guide_checkpoints.py`

Modify:
- `backend/app/rule_knowledge/ingestion.py`: rewritten.
- `backend/tests/unit/test_ingestion.py`: rewritten.
- `backend/app/domain/models.py`: `RulePassage`, `CheckResult`, `IssueObservation`.
- `backend/app/facts/deterministic_runner.py:137`
- `backend/tests/unit/test_models.py:64,69`
- `backend/app/persistence/repositories.py`: `RulePassageRepository`.
- `backend/app/audits/live_page_service.py`
- `backend/tests/unit/test_live_page_service.py`
- `backend/app/issues/reconciler.py`
- `backend/tests/unit/test_reconciler.py`
- `backend/app/api/schemas.py`: `IssueResponse`.
- `backend/app/api/mappers.py`
- `backend/app/main.py`: imports and lifespan.
- `backend/app/rule_knowledge/npl-pdp-audit-guide.md`: rewritten with headers.
- `GLOSSARY.md`: Rule Passage entry.
- `docs/superpowers/specs/2026-10-09-checkpoint-applicability-design.md`: Task 0 only.

Delete (Task 9 only, after nothing references them):
- `backend/app/rule_knowledge/retriever.py`
- `backend/tests/unit/test_retriever.py`

---

## Execution order

Run the tasks in this order: 0, 2, 4, 1, 3, 5, 6, 7, 8, 9, 10, 11, 12.

Task 2 and Task 4 come first because Task 1 imports `COMPLEMENT_GROUPS` from `markets.py`, and Task 3 needs `RulePassage.markets` from Task 4. Task 6 keeps `create_many` until Task 9 removes its only caller, so the app never calls a removed method.

---

### Task 0: Correct the spec

**Files:**
- Modify: `docs/superpowers/specs/2026-10-09-checkpoint-applicability-design.md`

- [ ] **Step 1: Read the spec.** Use the read tool on the whole file.

- [ ] **Step 2: Change the evaluator row.** Replace the line that starts with `| \`evaluator\`` with:

```
| `evaluator` | `llm`, `hybrid`, `code` | `hybrid` means it needs fact-tool results. `code` is the existing name for deterministic checks. |
```

- [ ] **Step 3: Replace the topics bullet in section 7.** Replace `- \`topics\` is removed.` with:

```
- `topics` is kept. The optional `topics` header key feeds the deterministic fact runner. Selection never filters on topics.
- `countries` is removed. Nothing reads it.
```

- [ ] **Step 4: Commit only the spec.**

```bash
git add -- "docs/superpowers/specs/2026-10-09-checkpoint-applicability-design.md"
git commit -m "docs: correct checkpoint applicability spec for topics and evaluator values"
```

---

### Task 1: Header and market-group parsing

**Files:**
- Create: `backend/app/rule_knowledge/checkpoint_header.py`
- Create: `backend/tests/unit/test_checkpoint_header.py`
- Depends on Task 2 (`COMPLEMENT_GROUPS` lives in `markets.py`). Do Task 2 first if you want the imports to resolve when the tests run.

- [ ] **Step 1: Write the failing test.** Create `backend/tests/unit/test_checkpoint_header.py`:

```python
import pytest

from app.domain.models import AuditMode, RuleEvaluatorType
from app.rule_knowledge.checkpoint_header import (
    CheckpointHeaderError,
    build_header,
    parse_market_groups,
)

GROUP_NAMES = frozenset({"EMEA", "APJC", "IMPERIAL", "NON_IMPERIAL", "NON_ENGLISH"})

VALID = """
id: SPR-20
profiles: sprint_launch
markets: global
zones: footnotes_disclaimers
evaluator: hybrid
review: never
reminder: Check that: the notes match
topics: footnote, link
"""


def test_build_header_reads_every_key():
    header = build_header(VALID, GROUP_NAMES)

    assert header.id == "SPR-20"
    assert header.profiles == (AuditMode.SPRINT_LAUNCH,)
    assert header.markets == ("global",)
    assert header.zones == ("footnotes_disclaimers",)
    assert header.evaluator == RuleEvaluatorType.HYBRID
    assert header.review == "never"
    assert header.reminder == "Check that: the notes match"
    assert header.topics == ("footnote", "link")


def test_zones_all_means_empty_tuple():
    header = build_header(VALID.replace("zones: footnotes_disclaimers", "zones: all"), GROUP_NAMES)
    assert header.zones == ()


def test_review_accepts_a_locale_tag():
    header = build_header(VALID.replace("review: never", "review: en-CA"), GROUP_NAMES)
    assert header.review == "en-CA"


def test_missing_key_is_rejected():
    with pytest.raises(CheckpointHeaderError, match="missing keys"):
        build_header(VALID.replace("evaluator: hybrid\n", ""), GROUP_NAMES)


def test_unknown_zone_is_rejected():
    with pytest.raises(CheckpointHeaderError, match="unknown zones"):
        build_header(VALID.replace("footnotes_disclaimers", "footer_nav"), GROUP_NAMES)


def test_unknown_market_is_rejected():
    with pytest.raises(CheckpointHeaderError, match="unknown market"):
        build_header(VALID.replace("markets: global", "markets: MOON"), GROUP_NAMES)


def test_unknown_evaluator_is_rejected():
    with pytest.raises(CheckpointHeaderError):
        build_header(VALID.replace("evaluator: hybrid", "evaluator: guess"), GROUP_NAMES)


def test_market_groups_parse_explicit_and_complement_groups():
    groups = parse_market_groups(
        "EMEA: en-GB, fr-FR\n"
        "NON_IMPERIAL: every locale not in IMPERIAL\n"
        "IMPERIAL: en-US, en-CA"
    )

    assert groups == {
        "EMEA": ("en-GB", "fr-FR"),
        "NON_IMPERIAL": (),
        "IMPERIAL": ("en-US", "en-CA"),
    }


def test_market_group_with_non_locale_entry_is_rejected():
    with pytest.raises(CheckpointHeaderError, match="non-locale"):
        parse_market_groups("EMEA: en-GB, United Kingdom")
```

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_checkpoint_header.py -q`
Expected: collection error, because `app.rule_knowledge.checkpoint_header` does not exist yet.

- [ ] **Step 3: Write the minimal implementation.** Create `backend/app/rule_knowledge/checkpoint_header.py`:

```python
"""Declared checkpoint headers and market groups for the bundled guide."""

import re
from dataclasses import dataclass

from app.acquisition.zone_extractor import ZoneExtractor
from app.domain.models import AuditMode, RuleEvaluatorType
from app.rule_knowledge.markets import COMPLEMENT_GROUPS

KNOWN_ZONES = frozenset(ZoneExtractor.ZONE_SELECTORS)
REQUIRED_KEYS = ("id", "profiles", "markets", "zones", "evaluator", "review")
REVIEW_VALUES = frozenset({"never", "always"})
LOCALE_TAG = re.compile(r"^[a-z]{2,3}-[a-z]{2}$", re.IGNORECASE)


class CheckpointHeaderError(ValueError):
    """Raised when a checkpoint header or market group is invalid."""


@dataclass(frozen=True)
class CheckpointHeader:
    id: str
    profiles: tuple[AuditMode, ...]
    markets: tuple[str, ...]
    zones: tuple[str, ...]
    evaluator: RuleEvaluatorType
    review: str
    reminder: str | None
    topics: tuple[str, ...]


def build_header(block: str, group_names: frozenset[str]) -> CheckpointHeader:
    values = _parse_key_values(block)
    missing = [key for key in REQUIRED_KEYS if key not in values]
    if missing:
        raise CheckpointHeaderError(f"{values.get('id', '?')}: missing keys {missing}")
    checkpoint_id = values["id"]
    try:
        profiles = tuple(AuditMode(item) for item in _split(values["profiles"]))
        evaluator = RuleEvaluatorType(values["evaluator"])
    except ValueError as exc:
        raise CheckpointHeaderError(f"{checkpoint_id}: {exc}") from exc
    markets = tuple(_split(values["markets"]))
    if not profiles or not markets:
        raise CheckpointHeaderError(f"{checkpoint_id}: profiles and markets must not be empty")
    for token in markets:
        if token != "global" and token not in group_names and not LOCALE_TAG.match(token):
            raise CheckpointHeaderError(f"{checkpoint_id}: unknown market {token}")
    zones = () if values["zones"] == "all" else tuple(_split(values["zones"]))
    unknown_zones = sorted(set(zones) - KNOWN_ZONES)
    if unknown_zones:
        raise CheckpointHeaderError(f"{checkpoint_id}: unknown zones {unknown_zones}")
    review = values["review"]
    if review not in REVIEW_VALUES and not LOCALE_TAG.match(review):
        raise CheckpointHeaderError(f"{checkpoint_id}: invalid review {review}")
    return CheckpointHeader(
        id=checkpoint_id,
        profiles=profiles,
        markets=markets,
        zones=zones,
        evaluator=evaluator,
        review=review,
        reminder=values.get("reminder") or None,
        topics=tuple(_split(values.get("topics", ""))),
    )


def parse_market_groups(block: str) -> dict[str, tuple[str, ...]]:
    groups: dict[str, tuple[str, ...]] = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        name, separator, value = line.partition(":")
        name = name.strip()
        if not separator or name in groups:
            raise CheckpointHeaderError(f"invalid or duplicate market group: {line!r}")
        if name in COMPLEMENT_GROUPS:
            groups[name] = ()
            continue
        tags = tuple(_split(value))
        bad = [tag for tag in tags if not LOCALE_TAG.match(tag)]
        if bad:
            raise CheckpointHeaderError(f"group {name} has non-locale entries {bad}")
        groups[name] = tags
    return groups


def _parse_key_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise CheckpointHeaderError(f"header line has no key: {line!r}")
        values[key.strip()] = value.strip()
    return values


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
```

- [ ] **Step 4: Run the test and see it pass.**

Run: `cd backend && uv run pytest tests/unit/test_checkpoint_header.py -q`
Expected: `9 passed`.

- [ ] **Step 5: Commit.** Do this after Task 2 exists, because this module imports it.

```bash
git add -- backend/app/rule_knowledge/checkpoint_header.py backend/tests/unit/test_checkpoint_header.py
git commit -m "feat: parse declared checkpoint headers and market groups"
```

---

### Task 2: Market matching

**Files:**
- Create: `backend/app/rule_knowledge/markets.py`
- Create: `backend/tests/unit/test_markets.py`

- [ ] **Step 1: Write the failing test.** Create `backend/tests/unit/test_markets.py`:

```python
from app.rule_knowledge.markets import MarketGroups

GROUPS = MarketGroups(
    {
        "EMEA": ("en-GB", "fr-FR", "de-DE"),
        "IMPERIAL": ("en-US", "en-CA", "fr-CA"),
        "NON_IMPERIAL": (),
        "NON_ENGLISH": (),
    }
)


def test_global_matches_every_locale():
    assert GROUPS.matches(("global",), "ja-JP")


def test_empty_markets_matches_every_locale():
    assert GROUPS.matches((), "ja-JP")


def test_locale_tag_matches_case_insensitively():
    assert GROUPS.matches(("en-US",), "EN-us")
    assert not GROUPS.matches(("en-US",), "en-CA")


def test_group_name_expands_to_its_locales():
    assert GROUPS.matches(("EMEA",), "fr-FR")
    assert not GROUPS.matches(("EMEA",), "en-US")


def test_imperial_group_is_exact():
    assert GROUPS.matches(("IMPERIAL",), "fr-CA")
    assert not GROUPS.matches(("IMPERIAL",), "fr-FR")


def test_non_imperial_is_the_complement_of_imperial():
    assert GROUPS.matches(("NON_IMPERIAL",), "fr-FR")
    assert not GROUPS.matches(("NON_IMPERIAL",), "en-US")


def test_non_english_excludes_every_english_locale():
    assert GROUPS.matches(("NON_ENGLISH",), "de-DE")
    assert not GROUPS.matches(("NON_ENGLISH",), "en-GB")


def test_names_include_groups_and_complement_groups():
    assert {"EMEA", "NON_IMPERIAL", "NON_ENGLISH"} <= GROUPS.names
```

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_markets.py -q`
Expected: collection error, because `markets.py` does not exist yet.

- [ ] **Step 3: Write the minimal implementation.** Create `backend/app/rule_knowledge/markets.py`:

```python
"""Market matching for declared checkpoint headers."""

from collections.abc import Mapping

COMPLEMENT_GROUPS = frozenset({"NON_IMPERIAL", "NON_ENGLISH"})


class MarketGroups:
    """Named locale groups from the guide, plus the two complement groups."""

    def __init__(self, groups: Mapping[str, tuple[str, ...]]) -> None:
        self._groups = {
            name: frozenset(tag.lower() for tag in tags) for name, tags in groups.items()
        }

    @property
    def names(self) -> frozenset[str]:
        return frozenset(self._groups) | COMPLEMENT_GROUPS

    def matches(self, markets: tuple[str, ...], locale: str) -> bool:
        if not markets or "global" in markets:
            return True
        tag = locale.lower()
        return any(self._token_matches(token, tag) for token in markets)

    def _token_matches(self, token: str, tag: str) -> bool:
        if token == "NON_IMPERIAL":
            return tag not in self._groups.get("IMPERIAL", frozenset())
        if token == "NON_ENGLISH":
            return tag.split("-", 1)[0] != "en"
        if token in self._groups:
            return tag in self._groups[token]
        return token.lower() == tag
```

- [ ] **Step 4: Run the test and see it pass.**

Run: `cd backend && uv run pytest tests/unit/test_markets.py tests/unit/test_checkpoint_header.py -q`
Expected: `17 passed`.

- [ ] **Step 5: Commit.**

```bash
git add -- backend/app/rule_knowledge/markets.py backend/tests/unit/test_markets.py backend/app/rule_knowledge/checkpoint_header.py backend/tests/unit/test_checkpoint_header.py
git commit -m "feat: match checkpoint markets against declared groups"
```

---

### Task 3: Selection

**Files:**
- Create: `backend/app/rule_knowledge/selection.py`
- Create: `backend/tests/unit/test_selection.py`

- [ ] **Step 1: Write the failing test.** Create `backend/tests/unit/test_selection.py`:

```python
from app.domain.models import AuditMode, RulePassage
from app.rule_knowledge.markets import MarketGroups
from app.rule_knowledge.selection import RuleSelector

GROUPS = MarketGroups({"IMPERIAL": ("en-US", "en-CA", "fr-CA")})


def _passage(
    rule_id: str,
    profiles: list[AuditMode],
    markets: list[str],
    zones: list[str],
) -> RulePassage:
    return RulePassage(
        id=rule_id,
        version="v1",
        heading_path=["Section", rule_id],
        source_range=(1, 2),
        original_text=f"Text for {rule_id}.",
        modes=profiles,
        markets=markets,
        zones=zones,
    )


PASSAGES = [
    _passage("global-all", [AuditMode.R2], ["global"], []),
    _passage("en-us-only", [AuditMode.R2], ["en-US"], []),
    _passage("r3-only", [AuditMode.R3], ["global"], []),
    _passage("footer-only", [AuditMode.R2], ["global"], ["global_footer"]),
    _passage("imperial", [AuditMode.R2], ["IMPERIAL"], ["dimensions_weight"]),
]


def _ids(rules):
    return [rule.id for rule in rules]


def test_profile_must_match():
    assert "r3-only" not in _ids(RuleSelector(PASSAGES, GROUPS).select(AuditMode.R2, "en-GB", "hero"))


def test_global_passage_applies_to_every_locale_in_profile():
    selected = RuleSelector(PASSAGES, GROUPS).select(AuditMode.R2, "ja-JP", "hero")
    assert "global-all" in _ids(selected)


def test_locale_tag_passage_applies_only_to_that_locale():
    selector = RuleSelector(PASSAGES, GROUPS)
    assert "en-us-only" in _ids(selector.select(AuditMode.R2, "en-US", "hero"))
    assert "en-us-only" not in _ids(selector.select(AuditMode.R2, "en-CA", "hero"))


def test_empty_zone_list_applies_to_every_zone():
    selector = RuleSelector(PASSAGES, GROUPS)
    assert "global-all" in _ids(selector.select(AuditMode.R2, "en-US", "footer_anything"))


def test_zone_list_restricts_to_listed_zones():
    selector = RuleSelector(PASSAGES, GROUPS)
    assert "footer-only" in _ids(selector.select(AuditMode.R2, "en-US", "global_footer"))
    assert "footer-only" not in _ids(selector.select(AuditMode.R2, "en-US", "hero"))


def test_group_passage_uses_group_membership():
    selector = RuleSelector(PASSAGES, GROUPS)
    assert "imperial" in _ids(selector.select(AuditMode.R2, "en-US", "dimensions_weight"))
    assert "imperial" not in _ids(selector.select(AuditMode.R2, "fr-FR", "dimensions_weight"))
```

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_selection.py -q`
Expected: collection error, because `selection.py` does not exist yet.

- [ ] **Step 3: Write the minimal implementation.** Create `backend/app/rule_knowledge/selection.py`:

```python
"""Select checkpoints for one profile, locale, and page zone."""

from collections.abc import Sequence

from app.domain.models import AuditMode, RulePassage
from app.rule_knowledge.markets import MarketGroups


class RuleSelector:
    """Return the checkpoints that apply to one audit context."""

    def __init__(self, passages: Sequence[RulePassage], groups: MarketGroups) -> None:
        self._passages = tuple(passages)
        self._groups = groups

    def select(self, profile: AuditMode, locale: str, zone: str) -> list[RulePassage]:
        return [
            passage
            for passage in self._passages
            if profile in passage.modes
            and self._groups.matches(tuple(passage.markets), locale)
            and (not passage.zones or zone in passage.zones)
        ]
```

- [ ] **Step 4: Run the test and see it pass.**

Run: `cd backend && uv run pytest tests/unit/test_selection.py -q`
Expected: `6 passed`.

- [ ] **Step 5: Commit.** Task 4 must land before this test file imports `RulePassage.markets`, so run Task 4 Step 3 first if the test errors on `markets`. Then:

```bash
git add -- backend/app/rule_knowledge/selection.py backend/tests/unit/test_selection.py
git commit -m "feat: select checkpoints by profile, market, and zone"
```

---

### Task 4: Domain model fields

**Files:**
- Modify: `backend/app/domain/models.py:130-144` (`RulePassage`), `:162-181` (`CheckResult`), `:194-210` (`IssueObservation`)
- Modify: `backend/app/facts/deterministic_runner.py:137`
- Modify: `backend/tests/unit/test_models.py:64,69`

- [ ] **Step 1: Write the failing test.** Append to `backend/tests/unit/test_models.py`:

```python
def test_rule_passage_declares_markets_and_review():
    passage = RulePassage(
        id="SPR-06",
        version="v1",
        heading_path=["Sprint/Launch audit", "SPR-06"],
        source_range=(1, 2),
        original_text="Spelling.",
        modes=[AuditMode.SPRINT_LAUNCH],
        markets=["global"],
        review="en-CA",
    )

    assert passage.markets == ["global"]
    assert passage.review == "en-CA"
    assert not hasattr(passage, "locales")
    assert not hasattr(passage, "review_required")


def test_check_result_carries_reminder():
    result = CheckResult(
        id="r1",
        run_id="run-1",
        page_snapshot_id="snap-1",
        rule_passage_id="D3",
        zone="tech_specs",
        outcome=CheckOutcome.ISSUE,
        reminder="Rule not finalized and in discussion.",
    )

    assert result.reminder == "Rule not finalized and in discussion."
```

Also replace the existing `locales=["en-US", "en-CA"]` in `test_models.py:64` with `markets=["en-US", "en-CA"]` and `assert "en-US" in passage.locales` at line 69 with `assert "en-US" in passage.markets`. Add any missing imports (`RulePassage`, `CheckResult`, `CheckOutcome`, `AuditMode`) at the top of the file if they are not there.

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_models.py -q`
Expected: failures on `markets`, `review`, and `reminder`.

- [ ] **Step 3: Write the minimal implementation.** In `backend/app/domain/models.py`, replace the `RulePassage` class body with:

```python
class RulePassage(BaseModel):
    id: str
    version: str
    heading_path: list[str]
    source_range: tuple[int, int]
    original_text: str
    modes: list[AuditMode]
    markets: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    zones: list[str] = Field(default_factory=list)
    severity: Severity | None = None
    evaluator_type: RuleEvaluatorType = RuleEvaluatorType.LLM
    review: str = "never"
    reminder: str | None = None
```

In `CheckResult`, after `review_required: bool = False` add:

```python
    reminder: str | None = None
```

In `IssueObservation`, after `reasoning: str | None = None` add:

```python
    reminder: str | None = None
```

In `backend/app/facts/deterministic_runner.py` line 137, replace `review_required=rule.review_required,` with:

```python
            review_required=False,
```

- [ ] **Step 4: Run the test and see it pass.**

Run: `cd backend && uv run pytest tests/unit/test_models.py tests/unit/test_facts.py tests/unit/test_verifier.py -q`
Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add -- backend/app/domain/models.py backend/app/facts/deterministic_runner.py backend/tests/unit/test_models.py
git commit -m "feat: declare checkpoint markets, review rule, and reminder on models"
```

---

### Task 5: Ingestion rewrite

**Files:**
- Modify (full rewrite): `backend/app/rule_knowledge/ingestion.py`
- Modify (full rewrite): `backend/tests/unit/test_ingestion.py`

- [ ] **Step 1: Write the failing test.** Replace the contents of `backend/tests/unit/test_ingestion.py` with:

```python
from pathlib import Path

import pytest

from app.domain.models import AuditMode
from app.rule_knowledge.checkpoint_header import CheckpointHeaderError
from app.rule_knowledge.ingestion import RuleIngestor

GROUPS = """<!-- market-groups
EMEA: en-GB, fr-FR
IMPERIAL: en-US, en-CA, fr-CA
NON_IMPERIAL: every locale not in IMPERIAL
NON_ENGLISH: every locale whose language is not en
-->
"""

SAMPLE = """
## Sprint/Launch audit
### SPR-07 Syllables
<!-- checkpoint
id: SPR-07
profiles: sprint_launch
markets: en-US
zones: all
evaluator: llm
review: never
-->
Words with more than 3 syllables.

## Process notes
Plain text is not a checkpoint.
"""


def _guide(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "guide.md"
    path.write_text(GROUPS + body, encoding="utf-8")
    return path


def test_ingestor_reads_declared_headers(tmp_path):
    catalog = RuleIngestor(_guide(tmp_path, SAMPLE)).ingest()

    [passage] = catalog.passages
    assert passage.id == "SPR-07"
    assert passage.modes == [AuditMode.SPRINT_LAUNCH]
    assert passage.markets == ["en-US"]
    assert passage.zones == []
    assert passage.heading_path == ["Sprint/Launch audit", "SPR-07 Syllables"]
    assert passage.original_text == "Words with more than 3 syllables."
    assert catalog.groups.matches(("IMPERIAL",), "en-CA")


def test_version_changes_with_content(tmp_path):
    first = RuleIngestor(_guide(tmp_path, SAMPLE)).ingest().version
    second = RuleIngestor(_guide(tmp_path, SAMPLE + "\nMore text.\n")).ingest().version
    assert first != second


def test_heading_without_header_is_rejected(tmp_path):
    body = "\n## Sprint/Launch audit\n### SPR-01 No header\nText.\n"
    with pytest.raises(CheckpointHeaderError, match="no header"):
        RuleIngestor(_guide(tmp_path, body)).ingest()


def test_unknown_zone_is_rejected(tmp_path):
    body = SAMPLE.replace("zones: all", "zones: footer_nav")
    with pytest.raises(CheckpointHeaderError, match="unknown zones"):
        RuleIngestor(_guide(tmp_path, body)).ingest()


def test_unknown_market_is_rejected(tmp_path):
    body = SAMPLE.replace("markets: en-US", "markets: MOON")
    with pytest.raises(CheckpointHeaderError, match="unknown market"):
        RuleIngestor(_guide(tmp_path, body)).ingest()


def test_duplicate_ids_are_rejected(tmp_path):
    body = SAMPLE + SAMPLE.split("## Process notes")[0]
    with pytest.raises(CheckpointHeaderError, match="duplicate"):
        RuleIngestor(_guide(tmp_path, body)).ingest()


def test_guide_without_market_groups_is_rejected(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text(SAMPLE, encoding="utf-8")
    with pytest.raises(CheckpointHeaderError, match="market-groups"):
        RuleIngestor(path).ingest()
```

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_ingestion.py -q`
Expected: failures, because the current ingestor has no `ingest()` returning a catalog.

- [ ] **Step 3: Write the minimal implementation.** Replace the contents of `backend/app/rule_knowledge/ingestion.py` with:

```python
"""Parse the bundled guide into checkpoints from declared headers."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from app.domain.models import RulePassage
from app.rule_knowledge.checkpoint_header import (
    CheckpointHeaderError,
    build_header,
    parse_market_groups,
)
from app.rule_knowledge.markets import MarketGroups

_GROUPS_RE = re.compile(r"<!--\s*market-groups\n(.*?)\n-->", re.DOTALL)
_CHECKPOINT_RE = re.compile(r"<!--\s*checkpoint\n(.*?)\n-->", re.DOTALL)


@dataclass(frozen=True)
class RuleCatalog:
    version: str
    groups: MarketGroups
    passages: list[RulePassage]


class RuleIngestor:
    """Parse the bundled guide into checkpoint passages."""

    def __init__(self, source_path: Path):
        self.source_path = source_path
        self.content = source_path.read_text(encoding="utf-8")
        self.version = hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def ingest(self) -> RuleCatalog:
        groups_match = _GROUPS_RE.search(self.content)
        if groups_match is None:
            raise CheckpointHeaderError("guide has no market-groups block")
        groups = MarketGroups(parse_market_groups(groups_match.group(1)))
        passages: list[RulePassage] = []
        seen: set[str] = set()
        for section, title, start, end, body in _checkpoint_blocks(self.content):
            text = "\n".join(body)
            match = _CHECKPOINT_RE.search(text)
            if match is None:
                raise CheckpointHeaderError(f"checkpoint heading has no header: {title}")
            header = build_header(match.group(1), groups.names)
            if header.id in seen:
                raise CheckpointHeaderError(f"duplicate checkpoint id: {header.id}")
            seen.add(header.id)
            passages.append(
                RulePassage(
                    id=header.id,
                    version=self.version,
                    heading_path=[section, title],
                    source_range=(start, end),
                    original_text=_CHECKPOINT_RE.sub("", text).strip(),
                    modes=list(header.profiles),
                    markets=list(header.markets),
                    zones=list(header.zones),
                    topics=list(header.topics),
                    evaluator_type=header.evaluator,
                    review=header.review,
                    reminder=header.reminder,
                )
            )
        return RuleCatalog(version=self.version, groups=groups, passages=passages)


def _checkpoint_blocks(content: str) -> list[tuple[str, str, int, int, list[str]]]:
    """Split the guide at ## sections and ### checkpoint headings."""
    blocks: list[tuple[str, str, int, int, list[str]]] = []
    section = "Introduction"
    current: tuple[str, int, list[str]] | None = None
    lines = content.splitlines()
    for number, line in enumerate(lines, start=1):
        if line.startswith("## ") or line.startswith("### "):
            if current is not None:
                blocks.append((section, current[0], current[1], number - 1, current[2]))
                current = None
            if line.startswith("## "):
                section = line[3:].strip()
            else:
                current = (line[4:].strip(), number, [])
        elif current is not None:
            current[2].append(line)
    if current is not None:
        blocks.append((section, current[0], current[1], len(lines), current[2]))
    return blocks
```

- [ ] **Step 4: Run the test and see it pass.**

Run: `cd backend && uv run pytest tests/unit/test_ingestion.py tests/unit/test_markets.py tests/unit/test_checkpoint_header.py tests/unit/test_selection.py -q`
Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add -- backend/app/rule_knowledge/ingestion.py backend/tests/unit/test_ingestion.py
git commit -m "feat: ingest checkpoints from declared headers instead of inference"
```

---

### Task 6: Idempotent passage storage

**Files:**
- Modify: `backend/app/persistence/repositories.py:167-171` (`create_many` becomes `replace_version`)
- Create: `backend/tests/unit/test_rule_passage_repository.py`

- [ ] **Step 1: Write the failing test.** Create `backend/tests/unit/test_rule_passage_repository.py`:

```python
import pytest

from app.domain.models import AuditMode, RulePassage
from app.persistence.repositories import RulePassageRepository


class FakeCollection:
    def __init__(self):
        self.docs: list[dict] = []

    async def delete_many(self, query):
        self.docs = [doc for doc in self.docs if doc.get("version") != query.get("version")]

    async def insert_many(self, docs):
        self.docs.extend(docs)

        class Result:
            inserted_ids = list(range(len(docs)))

        return Result()


class FakeDb:
    def __init__(self):
        self.rule_passages = FakeCollection()


def _passage(rule_id: str) -> RulePassage:
    return RulePassage(
        id=rule_id,
        version="v1",
        heading_path=["Section", rule_id],
        source_range=(1, 2),
        original_text="Text.",
        modes=[AuditMode.R3],
    )


@pytest.mark.asyncio
async def test_replace_version_does_not_duplicate_on_restart():
    db = FakeDb()
    repo = RulePassageRepository(db)
    passages = [_passage("A"), _passage("B")]

    await repo.replace_version("v1", passages)
    await repo.replace_version("v1", passages)

    assert len(db.rule_passages.docs) == 2


@pytest.mark.asyncio
async def test_replace_version_keeps_other_versions():
    db = FakeDb()
    repo = RulePassageRepository(db)
    await repo.replace_version("v0", [_passage("OLD")])
    await repo.replace_version("v1", [_passage("NEW")])

    assert {doc["version"] for doc in db.rule_passages.docs} == {"v0", "v1"}
```

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_rule_passage_repository.py -q`
Expected: failures with `AttributeError: 'RulePassageRepository' object has no attribute 'replace_version'`.

- [ ] **Step 3: Write the minimal implementation.** In `backend/app/persistence/repositories.py`, add this method to `RulePassageRepository` directly after `create_many`. Keep `create_many` until Task 9 removes its only caller:

```python
    async def replace_version(self, version: str, passages: list[RulePassage]) -> int:
        """Replace the stored passages for one rule version, so restarts do not duplicate."""
        await self.collection.delete_many({"version": version})
        if not passages:
            return 0
        result = await self.collection.insert_many([p.model_dump() for p in passages])
        return len(result.inserted_ids)
```

- [ ] **Step 4: Run the test and see it pass.**

Run: `cd backend && uv run pytest tests/unit/test_rule_passage_repository.py -q`
Expected: `2 passed`.

- [ ] **Step 5: Commit.**

```bash
git add -- backend/app/persistence/repositories.py backend/tests/unit/test_rule_passage_repository.py
git commit -m "fix: replace rule passages per version so restarts do not duplicate them"
```

---

### Task 7: Live service uses the selector and sets review and reminder

**Files:**
- Modify: `backend/app/audits/live_page_service.py` (import at line 34, constructor at lines 49–52 and 65–66, loop at line 145, return at line 235)
- Modify: `backend/tests/unit/test_live_page_service.py`

- [ ] **Step 1: Write the failing test.** In `backend/tests/unit/test_live_page_service.py`, change the existing `retriever` mocks to a selector mock, and append this test:

```python
@pytest.mark.asyncio
async def test_en_ca_spelling_finding_is_flagged_for_review(mocker: MockerFixture):
    """Test findings from an en-CA review checkpoint require review."""
    zone = Zone(name="hero", text="Colour", dom_locator=".hero", metadata={})
    fetcher = mocker.MagicMock()
    fetcher.fetch_page = mocker.AsyncMock(
        return_value=FetchedPage(
            url="https://example.test/pdp",
            html="<html>content</html>",
            zones=[zone],
            content_hash="hash-1",
            warnings=[],
        )
    )
    fetcher.stop = mocker.AsyncMock()
    spelling = _rule("SPR-06", RuleEvaluatorType.LLM)
    spelling.review = "en-CA"
    selector = mocker.MagicMock()
    selector.select = mocker.MagicMock(return_value=[spelling])
    evaluator = mocker.MagicMock()
    evaluator.evaluate = mocker.AsyncMock(
        return_value=DSXEvaluation(
            model="gpt-oss-120b",
            attempts=1,
            response=DSXEvaluationResponse(
                outcome="issue",
                problem="Use the Canadian form.",
                rule_quote="Check the page content.",
                evidence_quote="Colour",
                dom_locator=".hero",
            ),
        )
    )
    snapshot_repo = mocker.MagicMock()
    snapshot_repo.create = mocker.AsyncMock()
    persisted: list[CheckResult] = []
    result_repo = mocker.MagicMock()
    result_repo.create = mocker.AsyncMock(side_effect=persisted.append)
    service = LivePageAuditService(fetcher, selector, evaluator, snapshot_repo, result_repo)
    en_ca = PageTarget(url="https://example.test/pdp", locale="en-CA")

    await service.audit_page(_run(), en_ca, AuditMode.R3)

    selector.select.assert_called_once_with(AuditMode.R3, "en-CA", "hero")
    assert persisted[0].review_required is True
    assert persisted[0].reminder is None
```

Also in the two existing tests, replace `retriever = mocker.MagicMock()` with `selector = mocker.MagicMock()`, replace `retriever.retrieve = mocker.AsyncMock(return_value=...)` with `selector.select = mocker.MagicMock(return_value=...)`, pass `selector` where `retriever` was passed to `LivePageAuditService`, and change the assertion `retriever.retrieve.assert_awaited_once_with(AuditMode.R3, "en-US", zone="hero")` to `selector.select.assert_called_once_with(AuditMode.R3, "en-US", "hero")`.

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_live_page_service.py -q`
Expected: failures, because the service still expects a retriever with an async `retrieve`.

- [ ] **Step 3: Write the minimal implementation.** In `backend/app/audits/live_page_service.py`:

1. Replace the import `from app.rule_knowledge.retriever import RuleRetriever` with:

```python
from app.rule_knowledge.selection import RuleSelector
```

2. In `__init__`, replace the parameter `retriever: RuleRetriever,` with `selector: RuleSelector,` and `self._retriever = retriever` with `self._selector = selector`.

3. In `audit_fetched_page`, replace the line `rules = await self._retriever.retrieve(mode, target.locale, zone=zone.name)` with:

```python
            rules = self._selector.select(mode, target.locale, zone.name)
```

4. In `_evaluate_rule`, replace the final line `return self._verifier.verify(result, rule, zone, facts).result` with:

```python
        checked = self._verifier.verify(result, rule, zone, facts).result
        return checked.model_copy(
            update={
                "review_required": checked.review_required or _needs_review(rule, target.locale),
                "reminder": rule.reminder,
            }
        )
```

5. Add this module-level function at the end of the file:

```python
def _needs_review(rule: RulePassage, locale: str) -> bool:
    return rule.review == "always" or rule.review.lower() == locale.lower()
```

- [ ] **Step 4: Run the test and see it pass.**

Run: `cd backend && uv run pytest tests/unit/test_live_page_service.py -q`
Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add -- backend/app/audits/live_page_service.py backend/tests/unit/test_live_page_service.py
git commit -m "feat: select checkpoints per zone and flag review on findings"
```

---

### Task 8: Reminder reaches the API

**Files:**
- Modify: `backend/app/issues/reconciler.py` (inside `build_observation`, after `reasoning=result.reasoning,`)
- Modify: `backend/app/api/schemas.py` (`IssueResponse`, after `reasoning: str | None = None` that precedes `capture_url`)
- Modify: `backend/app/api/mappers.py` (after `reasoning=result.reasoning,` in `to_issue_response`, and after `reasoning=observation.reasoning,` in `to_observation_response`)
- Modify: `backend/tests/unit/test_reconciler.py`

- [ ] **Step 1: Write the failing test.** Append to `backend/tests/unit/test_reconciler.py`:

```python
def test_observation_keeps_check_reminder():
    """Test observations carry the checkpoint reminder into comparisons."""
    result = _result("reminded", "same").model_copy(
        update={"reminder": "Rule not finalized and in discussion."}
    )

    observation = IssueReconciler().build_observation(result, _snapshot())

    assert observation is not None
    assert observation.reminder == "Rule not finalized and in discussion."
```

Also add a finding-level assertion to the existing `test_observation_response_carries_check_reasoning` only if you want more coverage. It is not required.

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_reconciler.py -q`
Expected: failure on `observation.reminder`, because `build_observation` does not copy it yet.

- [ ] **Step 3: Write the minimal implementation.**

1. In `backend/app/issues/reconciler.py`, inside `build_observation`, directly after the line `            reasoning=result.reasoning,`, add:

```python
            reminder=result.reminder,
```

2. In `backend/app/api/schemas.py`, inside `IssueResponse`, directly after `    reasoning: str | None = None` and before `    capture_url: str | None = None`, add:

```python
    reminder: str | None = None
```

3. In `backend/app/api/mappers.py`, inside `to_issue_response`, directly after `        reasoning=result.reasoning,`, add:

```python
        reminder=result.reminder,
```

Inside `to_observation_response`, directly after `        reasoning=observation.reasoning,`, add:

```python
        reminder=observation.reminder,
```

- [ ] **Step 4: Run the test and see it pass.**

Run: `cd backend && uv run pytest tests/unit/test_reconciler.py tests/unit/test_comparison.py -q`
Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add -- backend/app/issues/reconciler.py backend/app/api/schemas.py backend/app/api/mappers.py backend/tests/unit/test_reconciler.py
git commit -m "feat: return checkpoint reminders on findings and comparison items"
```

---

### Task 9: Startup wiring, and remove the retriever

**Files:**
- Modify: `backend/app/main.py` (imports, `lifespan`)
- Delete: `backend/app/rule_knowledge/retriever.py`
- Delete: `backend/tests/unit/test_retriever.py`

- [ ] **Step 1: Confirm nothing else uses the retriever.** Use the grep tool on `backend` for `RuleRetriever|rule_retriever|retriever.py`. Expected matches: only `backend/app/main.py`, `backend/app/rule_knowledge/retriever.py`, and `backend/tests/unit/test_retriever.py`. Stop if anything else appears, and fix it first.

- [ ] **Step 2: Write the failing test.** Append to `backend/tests/integration/test_audit_api.py` a test that the lifespan wires a selector. Because the integration fixture does not run the lifespan, add this unit test instead, in a new file `backend/tests/unit/test_startup_wiring.py`:

```python
from pathlib import Path

from app.domain.models import AuditMode
from app.rule_knowledge.ingestion import RuleIngestor
from app.rule_knowledge.selection import RuleSelector

GUIDE = Path(__file__).resolve().parents[2] / "app" / "rule_knowledge" / "npl-pdp-audit-guide.md"


def test_startup_catalog_builds_a_selector_that_finds_english_checkpoints():
    catalog = RuleIngestor(GUIDE).ingest()
    selector = RuleSelector(catalog.passages, catalog.groups)

    assert selector.select(AuditMode.R2, "en-US", "features")
    assert selector.select(AuditMode.R3, "en-CA", "dimensions_weight")
```

This test depends on Task 10 (the new guide). Run it after Task 10. For now, it is expected to fail with a validation error from the old guide.

- [ ] **Step 3: Write the minimal implementation.** In `backend/app/main.py`:

1. Replace `from app.rule_knowledge.retriever import RuleRetriever` with:

```python
from app.rule_knowledge.selection import RuleSelector
```

2. In `lifespan`, delete the line `    app.state.rule_retriever = RuleRetriever(app.state.rule_passage_repo)`.

3. In `lifespan`, directly after `    app.state.activity = RunActivityLog()` and before `    app.state.live_page_service = LivePageAuditService(`, insert:

```python
    rule_path = Path(__file__).parent / "rule_knowledge" / "npl-pdp-audit-guide.md"
    catalog = RuleIngestor(rule_path).ingest()
    await app.state.rule_passage_repo.replace_version(catalog.version, catalog.passages)
    app.state.rule_selector = RuleSelector(catalog.passages, catalog.groups)
    print(f"Ingested {len(catalog.passages)} checkpoints (version: {catalog.version})")
```

4. In the `LivePageAuditService(` call, replace `        app.state.rule_retriever,` with `        app.state.rule_selector,`.

5. Delete the old ingestion block near the bottom of `lifespan`, which starts with `    rule_path = Path(__file__).parent / "rule_knowledge" / "npl-pdp-audit-guide.md"` followed by `    if rule_path.exists():` and ends with the `print(f"Ingested {len(passages)} rule passages ...")` line.

6. Delete the two files:

```bash
git rm -- backend/app/rule_knowledge/retriever.py backend/tests/unit/test_retriever.py
```

- [ ] **Step 4: Run the checks.**

Run: `cd backend && uv run pytest tests/unit tests/integration -q`
Expected: all pass, except `test_startup_wiring.py` until Task 10 lands.

- [ ] **Step 5: Commit.**

```bash
git add -- backend/app/main.py backend/tests/unit/test_startup_wiring.py
git commit -m "feat: build the checkpoint selector at startup and remove the keyword retriever"
```

---

### Task 10: Rewrite the guide with declared headers

**Files:**
- Modify (full rewrite): `backend/app/rule_knowledge/npl-pdp-audit-guide.md`
- Create: `backend/tests/unit/test_guide_checkpoints.py`

**Source text:** `docs/checkpoints-by-profile.md` is a close restatement of the checklist, not the verbatim wording. For exact wording, extract the 7.13 docx with this command (PowerShell):

```powershell
$path = 'C:\Users\Avinash_Verma2\Downloads\7.13 Global PDP Content R2 & R3 Audit Bot Database.docx'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($path)
$entry = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
$reader = New-Object System.IO.StreamReader($entry.Open()); $xml = $reader.ReadToEnd(); $reader.Close(); $zip.Dispose()
$xml = $xml -replace '</w:tc>', ' | ' -replace '</w:tr>', "`n" -replace '</w:p>', "`n"
$text = [System.Text.RegularExpressions.Regex]::Replace($xml, '<[^>]+>', '')
[System.Net.WebUtility]::HtmlDecode($text)
```

- [ ] **Step 1: Write the failing test.** Create `backend/tests/unit/test_guide_checkpoints.py`:

```python
from pathlib import Path

import pytest

from app.domain.models import AuditMode
from app.rule_knowledge.ingestion import RuleIngestor
from app.rule_knowledge.selection import RuleSelector

GUIDE = Path(__file__).resolve().parents[2] / "app" / "rule_knowledge" / "npl-pdp-audit-guide.md"


@pytest.fixture(scope="module")
def catalog():
    return RuleIngestor(GUIDE).ingest()


@pytest.fixture(scope="module")
def selector(catalog):
    return RuleSelector(catalog.passages, catalog.groups)


def _ids(rules):
    return {rule.id for rule in rules}


def test_guide_declares_65_checkpoints_per_profile(catalog):
    assert len(catalog.passages) == 65
    counts = {mode: sum(mode in p.modes for p in catalog.passages) for mode in AuditMode}
    assert counts == {AuditMode.SPRINT_LAUNCH: 23, AuditMode.R2: 31, AuditMode.R3: 26}


def test_english_pages_get_checkpoints(selector):
    assert "R2G-02" in _ids(selector.select(AuditMode.R2, "en-US", "hero"))
    assert "R3R-01" in _ids(selector.select(AuditMode.R3, "en-US", "hero"))
    assert "SPR-05" in _ids(selector.select(AuditMode.SPRINT_LAUNCH, "en-CA", "hero"))


def test_en_us_only_checkpoints_stay_on_en_us(selector):
    assert "R2G-04" in _ids(selector.select(AuditMode.R2, "en-US", "features"))
    assert "R2G-04" not in _ids(selector.select(AuditMode.R2, "en-CA", "features"))


def test_imperial_and_metric_checks_split_by_market(selector):
    en_ca = _ids(selector.select(AuditMode.R3, "en-CA", "dimensions_weight"))
    fr_fr = _ids(selector.select(AuditMode.R3, "fr-FR", "dimensions_weight"))
    assert "R3R-04" in en_ca and "R3R-03" not in en_ca
    assert "R3R-03" in fr_fr and "R3R-04" not in fr_fr


def test_china_copilot_check_only_on_zh_cn(selector):
    assert "D8" in _ids(selector.select(AuditMode.R2, "zh-CN", "features"))
    assert "D8" not in _ids(selector.select(AuditMode.R2, "en-US", "features"))


def test_footnote_zone_checks_only_run_in_their_zone(selector):
    assert "SPR-20" in _ids(selector.select(AuditMode.SPRINT_LAUNCH, "en-US", "footnotes_disclaimers"))
    assert "SPR-20" not in _ids(selector.select(AuditMode.SPRINT_LAUNCH, "en-US", "global_footer"))
```

- [ ] **Step 2: Run the test and see it fail.**

Run: `cd backend && uv run pytest tests/unit/test_guide_checkpoints.py -q`
Expected: fail, because the guide has no market-groups block and no headers yet.

- [ ] **Step 3: Write the guide.** Replace the entire contents of `backend/app/rule_knowledge/npl-pdp-audit-guide.md` with this structure. Fill each checkpoint body with the verbatim text from the docx, and use the header values from the table below.

Structure, in order:

1. A title line: `# NPL PDP Audit Guide`.
2. The market-groups block, exactly:

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

3. Section headings use `## `. There are four sections: `## Sprint/Launch audit`, `## R2 Global English review`, `## R3 Regional review`, `## R2 and R3 detailed sections`. Then `## Process notes`.
4. Each checkpoint is a `### ` heading (for example `### SPR-07 Words with more than three syllables`), then the header comment, then the verbatim body text. Use the header format shown below.
5. `## Process notes` contains plain bold-text paragraphs only. It must contain no `### ` headings.

Header format (one per checkpoint):

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

Add a `reminder: <text>` line only where the table says so.

**Header table.** Profiles: `sprint_launch` for SPR items, `r2` for R2G items, `r3` for R3R items, `r2, r3` for D items. Zones are comma lists from the extractor names, or `all`.

| ID | markets | zones | evaluator | review | reminder |
|---|---|---|---|---|---|
| SPR-01 | global | dimensions_weight | hybrid | never | |
| SPR-02 | global | dimensions_weight, tech_specs | llm | never | |
| SPR-03 | global | ports_slots | llm | never | |
| SPR-04 | global | hero, features, configuration_selector | llm | never | |
| SPR-05 | global | all | llm | never | |
| SPR-06 | global | all | llm | en-CA | |
| SPR-07 | en-US | all | llm | never | |
| SPR-08 | global | tech_specs, dimensions_weight | hybrid | never | |
| SPR-09 | global | configuration_selector, configuration_cards | llm | never | |
| SPR-10 | global | media_gallery | hybrid | never | |
| SPR-11 | global | all | hybrid | never | |
| SPR-12 | global | all | hybrid | never | |
| SPR-13 | global | media_gallery | hybrid | never | |
| SPR-14 | global | all | llm | never | |
| SPR-15 | global | tech_specs | llm | never | |
| SPR-16 | global | all | llm | never | |
| SPR-17 | global | all | llm | never | |
| SPR-18 | global | all | llm | never | |
| SPR-19 | global | all | hybrid | never | |
| SPR-20 | global | footnotes_disclaimers | hybrid | never | |
| SPR-21 | global | all | hybrid | never | |
| SPR-22 | global | all | hybrid | never | |
| SPR-23 | NON_IMPERIAL | all | llm | never | |
| R2G-01 | global | hero, features, configuration_selector | llm | never | |
| R2G-02 | global | all | llm | never | |
| R2G-03 | global | all | llm | en-CA | |
| R2G-04 | en-US | all | llm | never | |
| R2G-05 | global | tech_specs, dimensions_weight | hybrid | never | |
| R2G-06 | NON_IMPERIAL | all | llm | never | |
| R2G-07 | EMEA, APJC | dimensions_weight, tech_specs | hybrid | never | |
| R2G-08 | ja-JP | dimensions_weight, tech_specs | hybrid | never | |
| R2G-09 | global | all | llm | never | |
| R2G-10 | global | all | hybrid | never | |
| R2G-11 | global | footnotes_disclaimers | hybrid | never | |
| R2G-12 | global | all | hybrid | never | |
| R2G-13 | zh-CN | all | llm | never | |
| R2G-14 | global | all | hybrid | never | |
| R2G-15 | global | dimensions_weight, tech_specs | hybrid | never | |
| R2G-16 | EMEA, APJC, ja-JP | dimensions_weight, tech_specs | hybrid | never | |
| R3R-01 | global | all | llm | en-CA | |
| R3R-02 | global | dimensions_weight, tech_specs | hybrid | never | |
| R3R-03 | NON_IMPERIAL | dimensions_weight, tech_specs | hybrid | never | |
| R3R-04 | IMPERIAL | dimensions_weight, tech_specs | hybrid | never | |
| R3R-05 | ja-JP | dimensions_weight, tech_specs | hybrid | never | |
| R3R-06 | NON_ENGLISH | all | llm | never | |
| R3R-07 | global | all | llm | never | |
| R3R-08 | global | all | hybrid | never | |
| R3R-09 | NON_ENGLISH | all | hybrid | never | |
| R3R-10 | EMEA | media_gallery, features | llm | never | |
| R3R-11 | UK_ENGLISH | all | llm | never | |
| D1 | global | all | llm | en-CA | |
| D2 | global | all | llm | never | |
| D3 | global | dimensions_weight, tech_specs | hybrid | never | Rule not finalized and in discussion. |
| D4 | global | tech_specs, dimensions_weight | hybrid | never | |
| D5 | global | all | llm | never | Rule not finalized and in discussion. |
| D6 | global | all | llm | never | |
| D7 | global | all | hybrid | never | |
| D8 | zh-CN | all | llm | never | |
| D9 | global | all | hybrid | never | Check that the keywords carry the correct trademark symbol. |
| D10 | APJC | features, support | llm | never | |
| D11 | global | all | llm | always | Only native speakers should recommend alternative copy; otherwise seek the translations team. |
| D12 | global | all | llm | always | Only native speakers should recommend alternative copy; otherwise seek the translations team. |
| D13 | global | all | llm | always | Only native speakers should recommend alternative copy; otherwise seek the translations team. |
| D14 | FRENCH | all | llm | always | Only native speakers should recommend alternative copy; otherwise seek the translations team. |
| D15 | NON_ENGLISH | all | llm | always | Only native speakers should recommend alternative copy; otherwise seek the translations team. |

**Content fixes applied while rewriting** (they are part of this task, and the diff is reviewed):
- In the D1 table, change `digitilization` to `digitalization`.
- In the D15 German date example, change `22 April 2026` to `22. April 2026`.
- In the D9 detect list, add `Every "Arc" not followed by ™`, matching the keyword reminder.

- [ ] **Step 4: Run the tests and see them pass.**

Run: `cd backend && uv run pytest tests/unit/test_guide_checkpoints.py tests/unit/test_startup_wiring.py -q`
Expected: all pass. If a test fails, the header table or the body text is the likely cause. Fix the guide, not the test.

- [ ] **Step 5: Commit.**

```bash
git add -- backend/app/rule_knowledge/npl-pdp-audit-guide.md backend/tests/unit/test_guide_checkpoints.py
git commit -m "docs: declare checkpoint headers in the audit guide"
```

---

### Task 11: Glossary

**Files:**
- Modify: `GLOSSARY.md` (the `## Rule Passage` section)

- [ ] **Step 1: Replace the Rule Passage entry.** Replace the paragraph under `## Rule Passage` with:

```
A single checkpoint from the bundled NPL PDP audit guide. Each checkpoint has a declared header: a stable ID, the profiles that run it (Sprint/Launch, R2, R3), the markets it applies to, the page zones it reads, its evaluator, a review rule, and an optional reminder. Market groups (for example EMEA, APJC, IMPERIAL) are declared once at the top of the guide. Nothing is inferred from heading text.
```

- [ ] **Step 2: Commit.**

```bash
git add -- GLOSSARY.md
git commit -m "docs: describe declared checkpoint headers in the glossary"
```

---

### Task 12: Full verification

**Files:** none changed.

- [ ] **Step 1: Run the full backend suite.**

Run: `cd backend && uv run pytest -q tests/unit tests/integration`
Expected: all pass.

- [ ] **Step 2: Run lint.**

Run: `cd backend && uv run ruff check app tests`
Expected: `All checks passed!`

- [ ] **Step 3: Run the type check on changed modules.**

Run: `cd backend && uv run basedpyright app/rule_knowledge app/domain/models.py app/audits/live_page_service.py app/api/mappers.py app/api/schemas.py app/issues/reconciler.py app/persistence/repositories.py app/main.py`
Expected: `0 errors`. Warnings that already exist in these files are fine.

- [ ] **Step 4: Smoke-test the real guide without Mongo.**

Run:

```bash
cd backend && uv run python -c "from pathlib import Path; from app.domain.models import AuditMode; from app.rule_knowledge.ingestion import RuleIngestor; from app.rule_knowledge.selection import RuleSelector; c=RuleIngestor(Path('app/rule_knowledge/npl-pdp-audit-guide.md')).ingest(); s=RuleSelector(c.passages,c.groups); print(len(c.passages), len(s.select(AuditMode.R2,'en-US','features')), len(s.select(AuditMode.R3,'en-CA','dimensions_weight')))"
```

Expected: `65` followed by two non-zero counts.

- [ ] **Step 5: Frontend check.** The API adds a `reminder` field, and no UI changes. Run `cd frontend && npm run build && npm run lint`. Expected: build passes, and lint shows 0 errors.

- [ ] **Step 6: Report to the user.** The user must restart the `:8000` backend. Startup now ingests and validates the guide. A broken header stops the app on startup, by design.

---

## Risks

- **DSX cost rises for English pages.** English pages used to get zero checkpoints. They now get every applicable checkpoint in each zone. Review the number of calls per page before a live demo.
- **Comparisons restart at migration.** This is expected (spec section 6).
- **`get_latest_version` picks the largest version string, not the newest.** The version is a content hash, so "latest" is arbitrary. The selector does not use it, but the audit definition's `rule_version` does. Out of scope here; track as a follow-up.
- **Reminders are stored but not displayed.** The UI does not show `reminder` yet. Adding it is a follow-up.
- **Zones and evaluators are drafts.** Task 10's table is the first pass. Review them in the guide diff before merging.
