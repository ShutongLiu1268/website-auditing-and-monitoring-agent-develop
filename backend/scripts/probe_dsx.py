"""
Opt-in DSX gateway probe.

Checks client-credential authentication, TLS verification, plain JSON prompting,
JSON-object response mode, latency, and token usage. Credentials are never printed.

Usage (from backend/):
    python scripts/probe_dsx.py --env-file ../.vscode/.env
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.json_parsing import parse_json_safely  # noqa: E402
from app.agent.llm_provider import DSXClientProvider, missing_dsx_settings  # noqa: E402
from app.config import Settings  # noqa: E402

PROBE_MESSAGES = [
    {
        "role": "system",
        "content": "You are a website quality auditor. Respond only with one JSON object.",
    },
    {
        "role": "user",
        "content": (
            "Is this sentence grammatically correct? 'The informations is available.' "
            'Respond as {"has_error": true|false, "evidence": "...", "correction": "..."}'
        ),
    },
]


def _redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***")
    return text


def _cause_chain(exc: BaseException) -> str:
    names: list[str] = []
    cause = exc.__cause__ or exc.__context__
    while cause is not None and len(names) < 4:
        names.append(type(cause).__name__)
        cause = cause.__cause__ or cause.__context__
    return " <- ".join(names) or "none"


async def _probe(client: Any, model: str, *, json_mode: bool, secrets: list[str]) -> bool:
    label = "json_object" if json_mode else "plain"
    payload: dict[str, Any] = {
        "model": model,
        "messages": PROBE_MESSAGES,
        "temperature": 0.0,
        "timeout": 60.0,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    started = time.perf_counter()
    try:
        completion = await client.chat.completions.create(**payload)
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        message = _redact(str(exc), secrets)[:300]
        print(f"[{label}] FAILED {type(exc).__name__} status={status} cause={_cause_chain(exc)}")
        print(f"[{label}] message: {message}")
        return False
    elapsed = time.perf_counter() - started
    content = completion.choices[0].message.content if completion.choices else ""
    parsed = parse_json_safely(content)
    usage = completion.usage
    print(
        f"[{label}] OK latency={elapsed:.2f}s json_object_parsed={isinstance(parsed, dict)} "
        f"prompt_tokens={getattr(usage, 'prompt_tokens', None)} "
        f"completion_tokens={getattr(usage, 'completion_tokens', None)}"
    )
    return isinstance(parsed, dict)


async def _run(config: Settings) -> int:
    provider = DSXClientProvider(config)
    if provider.client is None:
        print("DSX client unavailable; check settings and csoutils[ai] installation.")
        return 2
    secrets = [config.DSX_CLIENT_ID, config.DSX_CLIENT_SECRET, config.DSX_API_KEY]
    try:
        plain_ok = await _probe(provider.client, config.DSX_MODEL, json_mode=False, secrets=secrets)
        json_mode_ok = await _probe(
            provider.client, config.DSX_MODEL, json_mode=True, secrets=secrets
        )
    finally:
        await provider.aclose()
    print(f"plain_json_prompting={'supported' if plain_ok else 'failed'}")
    print(f"response_format_json_object={'supported' if json_mode_ok else 'unsupported'}")
    return 0 if plain_ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe the DSX gateway without printing secrets.")
    parser.add_argument("--env-file", type=Path, help="Dotenv file with DSX settings")
    parser.add_argument("--model", help="Override DSX_MODEL for this probe")
    args = parser.parse_args()

    config = Settings()
    if args.env_file:
        config = Settings(_env_file=args.env_file)  # pyright: ignore[reportCallIssue]
    if args.model:
        config = config.model_copy(update={"DSX_MODEL": args.model})
    missing = missing_dsx_settings(config)
    if missing:
        print(f"Missing DSX settings: {', '.join(missing)}")
        return 2
    print(
        f"Probing model={config.DSX_MODEL} auth={config.DSX_AUTH_METHOD} "
        f"verify_tls={config.DSX_VERIFY_TLS}"
    )
    return asyncio.run(_run(config))


if __name__ == "__main__":
    raise SystemExit(main())
