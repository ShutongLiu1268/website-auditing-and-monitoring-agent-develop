"""Unit tests for the DSX evaluator. The OpenAI-compatible client is always mocked."""

import json
from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError, RateLimitError

from app.agent.evaluator import DSXEvaluator, build_check_result, build_prompt
from app.agent.schemas import DSXEvaluation, DSXEvaluationRequest
from app.domain.models import CheckOutcome, Severity, TokenUsage
from app.errors import ErrorCode

VALID_ISSUE = {
    "outcome": "Issue",
    "problem": "US spelling in EN-CA page.",
    "suggested_correction": "Use Customisation.",
    "proof_text": "Customisation",
    "severity": "Medium",
    "rule_quote": "Use regional spelling.",
    "evidence_quote": "Customization",
    "dom_locator": "#configuration-cards h3",
    "confidence": 0.92,
    "review_required": True,
}


def _completion(content: str, prompt_tokens: int = 100, completion_tokens: int = 20):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


def _request() -> DSXEvaluationRequest:
    return DSXEvaluationRequest(
        url="https://www.dell.com/en-ca/shop/laptops",
        locale="en-CA",
        zone="configuration_cards",
        checkpoint_id="r3-section-8",
        checkpoint_text="Use regional spelling.",
        page_text="Customization",
        deterministic_facts={"metric_first": True},
    )


@pytest.fixture
def client(mocker):
    fake_client = mocker.MagicMock()
    fake_client.chat.completions.create = mocker.AsyncMock()
    return fake_client


@pytest.mark.asyncio
async def test_evaluate_uses_async_client_with_deterministic_payload(client):
    client.chat.completions.create.return_value = _completion(json.dumps(VALID_ISSUE))
    evaluator = DSXEvaluator(client, model="gpt-oss-120b")

    evaluation = await evaluator.evaluate(_request())

    client.chat.completions.create.assert_awaited_once()
    payload = client.chat.completions.create.await_args.kwargs
    assert payload["model"] == "gpt-oss-120b"
    assert payload["temperature"] == 0.0
    assert payload["timeout"] == 60.0
    assert payload["response_format"] == {"type": "json_object"}
    assert [message["role"] for message in payload["messages"]] == ["system", "user"]
    assert evaluation.response is not None
    assert evaluation.response.outcome == "issue"
    assert evaluation.response.severity == "medium"
    assert evaluation.attempts == 1
    assert evaluation.token_usage == TokenUsage(
        prompt_tokens=100, completion_tokens=20, total_tokens=120
    )


@pytest.mark.asyncio
async def test_evaluate_omits_response_format_when_json_mode_disabled(client):
    client.chat.completions.create.return_value = _completion(json.dumps(VALID_ISSUE))
    evaluator = DSXEvaluator(
        client, model="gpt-oss-120b", use_json_mode=False, timeout_seconds=15.0
    )

    await evaluator.evaluate(_request())

    payload = client.chat.completions.create.await_args.kwargs
    assert "response_format" not in payload
    assert payload["timeout"] == 15.0


@pytest.mark.asyncio
async def test_evaluate_parses_code_fenced_json(client):
    client.chat.completions.create.return_value = _completion(
        f"```json\n{json.dumps(VALID_ISSUE)}\n```"
    )

    evaluation = await DSXEvaluator(client, model="gpt-oss-120b").evaluate(_request())

    assert evaluation.response is not None
    assert evaluation.error_code is None


@pytest.mark.asyncio
async def test_evaluate_retries_malformed_output_and_sums_token_usage(client):
    client.chat.completions.create.side_effect = [
        _completion("not json", prompt_tokens=90, completion_tokens=10),
        _completion(json.dumps(VALID_ISSUE), prompt_tokens=95, completion_tokens=25),
    ]

    evaluation = await DSXEvaluator(client, model="gpt-oss-120b").evaluate(_request())

    assert client.chat.completions.create.await_count == 2
    assert evaluation.attempts == 2
    assert evaluation.response is not None
    assert evaluation.token_usage == TokenUsage(
        prompt_tokens=185, completion_tokens=35, total_tokens=220
    )


@pytest.mark.asyncio
async def test_evaluate_reports_malformed_output_after_retry(client):
    client.chat.completions.create.side_effect = [
        _completion("not json"),
        _completion(json.dumps({"outcome": "maybe"})),
    ]

    evaluation = await DSXEvaluator(client, model="gpt-oss-120b").evaluate(_request())

    assert evaluation.response is None
    assert evaluation.error_code == ErrorCode.DSX_MALFORMED_OUTPUT
    assert evaluation.error_reason == "schema_validation_failed"
    assert evaluation.token_usage == TokenUsage(
        prompt_tokens=200, completion_tokens=40, total_tokens=240
    )


@pytest.mark.asyncio
async def test_evaluate_does_not_retry_gateway_errors(client):
    request = httpx.Request("POST", "https://gateway.example.test/v1/chat/completions")
    client.chat.completions.create.side_effect = APIConnectionError(request=request)

    evaluation = await DSXEvaluator(client, model="gpt-oss-120b").evaluate(_request())

    client.chat.completions.create.assert_awaited_once()
    assert evaluation.error_code == ErrorCode.DSX_UNAVAILABLE
    assert evaluation.error_reason == "APIConnectionError"


@pytest.mark.asyncio
async def test_evaluate_maps_rate_limits(client):
    request = httpx.Request("POST", "https://gateway.example.test/v1/chat/completions")
    response = httpx.Response(429, request=request)
    client.chat.completions.create.side_effect = RateLimitError(
        "rate limited", response=response, body=None
    )

    evaluation = await DSXEvaluator(client, model="gpt-oss-120b").evaluate(_request())

    assert evaluation.error_code == ErrorCode.DSX_RATE_LIMITED
    assert evaluation.error_reason == "RateLimitError:429"


@pytest.mark.asyncio
async def test_evaluate_without_client_is_not_evaluated():
    evaluation = await DSXEvaluator(None, model="gpt-oss-120b").evaluate(_request())

    assert evaluation.attempts == 0
    assert evaluation.error_code == ErrorCode.DSX_UNAVAILABLE


def test_build_check_result_records_issue_and_token_usage():
    evaluation = DSXEvaluation.model_validate(
        {
            "model": "gpt-oss-120b",
            "attempts": 1,
            "response": VALID_ISSUE,
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
            },
        }
    )

    result = build_check_result(
        evaluation,
        result_id="result-1",
        run_id="run-1",
        page_snapshot_id="snapshot-1",
        rule_passage_id="r3-section-8",
        zone="configuration_cards",
    )

    assert result.outcome == CheckOutcome.ISSUE
    assert result.severity == Severity.MEDIUM
    assert result.model == "gpt-oss-120b"
    assert result.token_usage == TokenUsage(
        prompt_tokens=100, completion_tokens=20, total_tokens=120
    )


def test_build_check_result_carries_reasoning():
    evaluation = DSXEvaluation.model_validate(
        {
            "model": "gpt-oss-120b",
            "attempts": 1,
            "response": {**VALID_ISSUE, "reasoning": "EN-CA heading uses US spelling."},
        }
    )

    result = build_check_result(
        evaluation,
        result_id="result-1",
        run_id="run-1",
        page_snapshot_id="snapshot-1",
        rule_passage_id="r3-section-8",
        zone="configuration_cards",
    )

    assert result.reasoning == "EN-CA heading uses US spelling."


def test_prompt_asks_for_reasoning():
    assert '"reasoning"' in build_prompt(_request())


@pytest.mark.parametrize(
    ("attempts", "expected_outcome"),
    [(0, CheckOutcome.NOT_EVALUATED), (2, CheckOutcome.ERROR)],
)
def test_build_check_result_records_failures(attempts, expected_outcome):
    evaluation = DSXEvaluation(
        model="gpt-oss-120b",
        attempts=attempts,
        token_usage=(
            TokenUsage(prompt_tokens=10, completion_tokens=2, total_tokens=12)
            if attempts
            else None
        ),
        error_code=(
            ErrorCode.DSX_MALFORMED_OUTPUT if attempts else ErrorCode.DSX_UNAVAILABLE
        ),
        error_reason="invalid_json" if attempts else "client_not_configured",
    )

    result = build_check_result(
        evaluation,
        result_id="result-1",
        run_id="run-1",
        page_snapshot_id="snapshot-1",
        rule_passage_id="r3-section-8",
        zone="configuration_cards",
    )

    assert result.outcome == expected_outcome
    assert result.error == f"{evaluation.error_code}:{evaluation.error_reason}"
    assert result.token_usage == evaluation.token_usage
