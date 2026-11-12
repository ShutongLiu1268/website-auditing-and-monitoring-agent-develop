"""Unit tests for tolerant LLM JSON parsing."""

import pytest

from app.agent.json_parsing import parse_json_safely


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"outcome": "pass"}', {"outcome": "pass"}),
        ('```json\n{"outcome": "issue"}\n```', {"outcome": "issue"}),
        (
            'Result follows: {"outcome": "pass", "confidence": 0.9} done',
            {"outcome": "pass", "confidence": 0.9},
        ),
        ('Items: [{"id": 1}]', [{"id": 1}]),
    ],
)
def test_parse_json_safely_extracts_structured_json(text, expected):
    assert parse_json_safely(text) == expected


@pytest.mark.parametrize("text", [None, "", "not json", "42", '"just a string"', "{broken"])
def test_parse_json_safely_rejects_non_structured_output(text):
    assert parse_json_safely(text) is None
