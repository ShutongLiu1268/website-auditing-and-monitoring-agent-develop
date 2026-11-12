"""Tolerant JSON extraction for LLM output."""

import json
import re
from collections.abc import Iterator
from typing import Any

_CODE_FENCE = re.compile(r"```(?:json)?\s*", re.IGNORECASE)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)
_JSON_ARRAY = re.compile(r"\[.*\]", re.DOTALL)


def parse_json_safely(text: str | None) -> dict[str, Any] | list[Any] | None:
    """Return the first JSON object or array found in model output."""
    if not text:
        return None
    cleaned = _CODE_FENCE.sub("", text).strip().rstrip("`").strip()
    for candidate in (cleaned, *_embedded_candidates(cleaned)):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict | list):
            return parsed
    return None


def _embedded_candidates(text: str) -> Iterator[str]:
    matches = [match for match in (_JSON_OBJECT.search(text), _JSON_ARRAY.search(text)) if match]
    for match in sorted(matches, key=lambda found: found.start()):
        yield match.group()
