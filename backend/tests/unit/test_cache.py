"""Unit tests for DSX evaluation cache."""

from app.agent.cache import DSXEvaluationCache, EvaluationCacheKey
from app.agent.schemas import DSXEvaluation


def test_cache_key_is_stable():
    """Equivalent inputs produce the same key."""
    first = EvaluationCacheKey.build("v1", "rule", "content", {"a": 1}, "p1", "model")
    second = EvaluationCacheKey.build("v1", "rule", "content", {"a": 1}, "p1", "model")

    assert first == second


def test_cache_stores_and_clears_evaluation():
    """Cached evaluations can be retrieved and cleared."""
    cache = DSXEvaluationCache()
    key = EvaluationCacheKey.build("v1", "rule", "content", {}, "p1", "model")
    value = DSXEvaluation(model="model", attempts=1)

    cache.set(key, value)
    assert cache.get(key) == value
    cache.clear()
    assert cache.get(key) is None
