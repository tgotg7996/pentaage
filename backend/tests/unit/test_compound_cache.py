from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Optional
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.schemas.compound import CompoundAnalyzeResponse, SimilarityResult
from app.services.compound_service import (
    InMemoryCompoundCache,
    RedisCompoundCache,
    _create_compound_cache,
    _payload_to_response,
    _response_to_payload,
)


class _FakeRedisClient:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        _ = ttl_seconds
        self.store[key] = value

    def keys(self, pattern: str) -> list[str]:
        prefix = pattern[:-1] if pattern.endswith("*") else pattern
        return [key for key in self.store if key.startswith(prefix)]

    def delete(self, *keys: str) -> None:
        for key in keys:
            _ = self.store.pop(key, None)


def _sample_response() -> CompoundAnalyzeResponse:
    return CompoundAnalyzeResponse(
        compound_name="Sample",
        canonical_smiles="CCO",
        total_score=72,
        base_score=43.2,
        composite_score=28.8,
        top_similarities=[
            SimilarityResult(reference_name="Resveratrol", reference_cas="501-36-0", similarity=0.88, rank=1)
        ],
        algorithm_version="sim-v1.0.0",
        fingerprint_params={"radius": 2, "n_bits": 2048, "use_features": False},
        cached=False,
        calc_id="9d9ff70d-6fd0-4d89-a245-cd4a47c7f5fc",
    )


def test_payload_round_trip_preserves_compound_response() -> None:
    original = _sample_response()
    payload = _response_to_payload(original)
    restored = _payload_to_response(payload)

    assert restored is not None
    assert restored.calc_id == original.calc_id
    assert restored.canonical_smiles == original.canonical_smiles
    assert restored.top_similarities[0].reference_name == original.top_similarities[0].reference_name


def test_redis_cache_set_get_and_clear() -> None:
    redis_client = _FakeRedisClient()
    cache = RedisCompoundCache(client=redis_client)
    response = _sample_response()

    cache.set("fp:CCO:2:2048:0:5", response)
    cached = cache.get("fp:CCO:2:2048:0:5")
    assert cached is not None
    assert cached.calc_id == response.calc_id

    cache.clear()
    assert cache.get("fp:CCO:2:2048:0:5") is None


def test_create_compound_cache_uses_redis_when_enabled(monkeypatch) -> None:
    redis_client = _FakeRedisClient()
    fake_module = SimpleNamespace(from_url=lambda *_args, **_kwargs: redis_client)

    monkeypatch.setenv("COMPOUND_CACHE_BACKEND", "redis")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    with patch("app.services.compound_service.importlib.import_module", return_value=fake_module):
        cache = _create_compound_cache()

    assert isinstance(cache, RedisCompoundCache)


def test_create_compound_cache_falls_back_to_memory_on_import_failure(monkeypatch) -> None:
    monkeypatch.setenv("COMPOUND_CACHE_BACKEND", "redis")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    with patch("app.services.compound_service.importlib.import_module", side_effect=ImportError):
        cache = _create_compound_cache()

    assert isinstance(cache, InMemoryCompoundCache)
