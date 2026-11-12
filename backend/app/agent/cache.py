"""In-memory cache for validated DSX evaluations."""

import hashlib
import json
from dataclasses import dataclass

from app.agent.schemas import DSXEvaluation


@dataclass(frozen=True)
class EvaluationCacheKey:
    """Stable key for one rule/zone/facts/model evaluation."""

    value: str

    @classmethod
    def build(
        cls,
        rule_version: str,
        rule_id: str,
        zone_text: str,
        facts: dict[str, object],
        prompt_version: str,
        model: str,
    ) -> "EvaluationCacheKey":
        """Build a deterministic SHA-256 cache key."""
        payload = json.dumps(
            {
                "rule_version": rule_version,
                "rule_id": rule_id,
                "zone_text": zone_text,
                "facts": facts,
                "prompt_version": prompt_version,
                "model": model,
            },
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        return cls(hashlib.sha256(payload).hexdigest())


class EvaluationCache[T]:
    """Small process-local cache for successful evaluation values."""

    def __init__(self) -> None:
        self._values: dict[str, T] = {}

    def get(self, key: EvaluationCacheKey) -> T | None:
        """Get a cached value."""
        return self._values.get(key.value)

    def set(self, key: EvaluationCacheKey, value: T) -> None:
        """Store a validated value."""
        self._values[key.value] = value

    def clear(self) -> None:
        """Clear cached values."""
        self._values.clear()


DSXEvaluationCache = EvaluationCache[DSXEvaluation]
