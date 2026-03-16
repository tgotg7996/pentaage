from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import json
import os
import re
import uuid
from typing import Any, Protocol, cast
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.fingerprint import morgan_fingerprint
from ..core.reference import load_reference_compounds
from ..core.scoring import total_score
from ..core.similarity import tanimoto
from ..models.compound import CompoundResult
from ..schemas.compound import (
    AnalyzeOptions,
    CompoundAnalyzeRequest,
    CompoundAnalyzeResponse,
    SimilarityResult,
)


_ALLOWED_SMILES = re.compile(r"^[A-Za-z0-9@+\-\[\]\(\)=#$\\/.%]+$")


class CompoundCache(Protocol):
    def get(self, key: str) -> CompoundAnalyzeResponse | None: ...

    def set(self, key: str, value: CompoundAnalyzeResponse) -> None: ...

    def clear(self) -> None: ...


class RedisClient(Protocol):
    def get(self, key: str) -> str | bytes | None: ...

    def setex(self, key: str, ttl_seconds: int, value: str) -> Any: ...

    def keys(self, pattern: str) -> list[str]: ...

    def delete(self, *keys: str) -> Any: ...


@dataclass
class InMemoryCompoundCache:
    _store: dict[str, CompoundAnalyzeResponse] = field(default_factory=dict)

    def get(self, key: str) -> CompoundAnalyzeResponse | None:
        return self._store.get(key)

    def set(self, key: str, value: CompoundAnalyzeResponse) -> None:
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()


@dataclass
class RedisCompoundCache:
    client: RedisClient
    prefix: str = "compound-cache:"
    ttl_seconds: int = 30 * 24 * 60 * 60

    def _cache_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def get(self, key: str) -> CompoundAnalyzeResponse | None:
        try:
            raw = self.client.get(self._cache_key(key))
        except Exception:
            return None
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return _payload_to_response(payload)

    def set(self, key: str, value: CompoundAnalyzeResponse) -> None:
        payload = json.dumps(_response_to_payload(value), ensure_ascii=False, separators=(",", ":"))
        try:
            self.client.setex(self._cache_key(key), self.ttl_seconds, payload)
        except Exception:
            return

    def clear(self) -> None:
        try:
            keys = self.client.keys(f"{self.prefix}*")
            if keys:
                self.client.delete(*keys)
        except Exception:
            return


def _response_to_payload(response: CompoundAnalyzeResponse) -> dict[str, object]:
    return {
        "compound_name": response.compound_name,
        "canonical_smiles": response.canonical_smiles,
        "total_score": response.total_score,
        "base_score": response.base_score,
        "composite_score": response.composite_score,
        "top_similarities": [
            {
                "reference_name": item.reference_name,
                "reference_cas": item.reference_cas,
                "similarity": item.similarity,
                "rank": item.rank,
            }
            for item in response.top_similarities
        ],
        "algorithm_version": response.algorithm_version,
        "fingerprint_params": response.fingerprint_params,
        "cached": response.cached,
        "calc_id": response.calc_id,
    }


def _payload_to_response(payload: object) -> CompoundAnalyzeResponse | None:
    if not isinstance(payload, dict):
        return None
    similarities_raw = payload.get("top_similarities", [])
    if not isinstance(similarities_raw, list):
        similarities_raw = []
    top_similarities: list[SimilarityResult] = []
    for item in similarities_raw:
        if not isinstance(item, dict):
            continue
        reference_name = item.get("reference_name")
        reference_cas = item.get("reference_cas")
        similarity = item.get("similarity")
        rank = item.get("rank")
        if not isinstance(reference_name, str):
            continue
        if not isinstance(reference_cas, str):
            continue
        if not isinstance(similarity, (int, float)):
            continue
        if not isinstance(rank, int):
            continue
        top_similarities.append(
            SimilarityResult(
                reference_name=reference_name,
                reference_cas=reference_cas,
                similarity=float(similarity),
                rank=rank,
            )
        )

    canonical_smiles = payload.get("canonical_smiles")
    total_score_value = payload.get("total_score")
    base_score_value = payload.get("base_score")
    composite_score_value = payload.get("composite_score")
    algorithm_version = payload.get("algorithm_version")
    fingerprint_params = payload.get("fingerprint_params")
    cached_value = payload.get("cached")
    calc_id = payload.get("calc_id")
    compound_name = payload.get("compound_name")

    if not isinstance(canonical_smiles, str):
        return None
    if not isinstance(total_score_value, int):
        return None
    if not isinstance(base_score_value, (int, float)):
        return None
    if not isinstance(composite_score_value, (int, float)):
        return None
    if not isinstance(algorithm_version, str):
        return None
    if not isinstance(fingerprint_params, dict):
        return None
    if not isinstance(cached_value, bool):
        return None
    if not isinstance(calc_id, str):
        return None
    if compound_name is not None and not isinstance(compound_name, str):
        return None

    return CompoundAnalyzeResponse(
        compound_name=compound_name,
        canonical_smiles=canonical_smiles,
        total_score=total_score_value,
        base_score=float(base_score_value),
        composite_score=float(composite_score_value),
        top_similarities=top_similarities,
        algorithm_version=algorithm_version,
        fingerprint_params=fingerprint_params,
        cached=cached_value,
        calc_id=calc_id,
    )


def _create_compound_cache() -> CompoundCache:
    backend = os.getenv("COMPOUND_CACHE_BACKEND", "memory").strip().lower()
    if backend != "redis":
        return InMemoryCompoundCache()

    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return InMemoryCompoundCache()

    try:
        redis_module = importlib.import_module("redis")
    except Exception:
        return InMemoryCompoundCache()

    from_url = getattr(redis_module, "from_url", None)
    if callable(from_url):
        try:
            client = from_url(redis_url, decode_responses=True)
            return RedisCompoundCache(client=cast(RedisClient, client))
        except Exception:
            return InMemoryCompoundCache()

    redis_cls = getattr(redis_module, "Redis", None)
    from_url_cls = getattr(redis_cls, "from_url", None)
    if callable(from_url_cls):
        try:
            client = from_url_cls(redis_url, decode_responses=True)
            return RedisCompoundCache(client=cast(RedisClient, client))
        except Exception:
            return InMemoryCompoundCache()

    return InMemoryCompoundCache()


compound_cache: CompoundCache = _create_compound_cache()


def reset_compound_cache() -> None:
    compound_cache.clear()


def _clone_response(response: CompoundAnalyzeResponse, cached: bool) -> CompoundAnalyzeResponse:
    return CompoundAnalyzeResponse(
        compound_name=response.compound_name,
        canonical_smiles=response.canonical_smiles,
        total_score=response.total_score,
        base_score=response.base_score,
        composite_score=response.composite_score,
        top_similarities=list(response.top_similarities),
        algorithm_version=response.algorithm_version,
        fingerprint_params=dict(response.fingerprint_params),
        cached=cached,
        calc_id=response.calc_id,
    )


def _validate_smiles(value: str) -> str:
    canonical = value.strip()
    if not canonical or not _ALLOWED_SMILES.match(canonical):
        raise ValueError("INVALID_SMILES")
    return canonical


def _persist_result(
    db: Session,
    input_smiles: str,
    response: CompoundAnalyzeResponse,
) -> None:
    calc_uuid = UUID(response.calc_id)
    existing = db.query(CompoundResult.id).filter(CompoundResult.calc_id == calc_uuid).first()
    if existing is not None:
        return

    result = CompoundResult(
        calc_id=calc_uuid,
        input_smiles=input_smiles,
        canonical_smiles=response.canonical_smiles,
        total_score=response.total_score,
        base_score=response.base_score,
        composite_score=response.composite_score,
        algorithm_version=response.algorithm_version,
        fingerprint_params=response.fingerprint_params,
        cached=response.cached,
    )
    db.add(result)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def analyze_compound(
    request: CompoundAnalyzeRequest,
    db: Session | None = None,
) -> CompoundAnalyzeResponse:
    options = request.options or AnalyzeOptions()
    canonical_smiles = _validate_smiles(request.input_value)

    cache_key = (
        f"fp:{canonical_smiles}:{options.radius}:{options.n_bits}:"
        f"{int(options.use_features)}:{options.top_n}"
    )
    cached_value = compound_cache.get(cache_key)
    if cached_value is not None:
        cached_response = _clone_response(cached_value, cached=True)
        if db is not None:
            _persist_result(db=db, input_smiles=request.input_value, response=cached_response)
        return cached_response

    query_fp = morgan_fingerprint(canonical_smiles, radius=options.radius, n_bits=options.n_bits)

    similarities: list[SimilarityResult] = []
    for reference in load_reference_compounds():
        ref_smiles = reference.get("canonical_smiles") or reference.get("smiles") or ""
        if not ref_smiles:
            continue
        ref_fp = morgan_fingerprint(ref_smiles, radius=options.radius, n_bits=options.n_bits)
        score = round(tanimoto(query_fp, ref_fp), 4)
        similarities.append(
            SimilarityResult(
                reference_name=reference.get("name_en", ""),
                reference_cas=reference.get("cas", ""),
                similarity=score,
                rank=0,
            )
        )

    similarities.sort(key=lambda item: item.similarity, reverse=True)
    top_n = max(options.top_n, 1)
    top_similarities = similarities[:top_n]
    for index, item in enumerate(top_similarities, start=1):
        item.rank = index

    max_similarity = top_similarities[0].similarity if top_similarities else 0.0
    top3 = top_similarities[:3]
    top3_avg_similarity = round(sum(item.similarity for item in top3) / len(top3), 4) if top3 else 0.0
    base_score = round(max_similarity * 60, 4)
    composite_score = round(top3_avg_similarity * 40, 4)

    response = CompoundAnalyzeResponse(
        compound_name=None,
        canonical_smiles=canonical_smiles,
        total_score=total_score(max_similarity=max_similarity, top3_avg_similarity=top3_avg_similarity),
        base_score=base_score,
        composite_score=composite_score,
        top_similarities=top_similarities,
        algorithm_version="sim-v1.0.0",
        fingerprint_params={
            "radius": options.radius,
            "n_bits": options.n_bits,
            "use_features": options.use_features,
        },
        cached=False,
        calc_id=str(uuid.uuid4()),
    )

    if db is not None:
        _persist_result(db=db, input_smiles=request.input_value, response=response)

    compound_cache.set(cache_key, response)
    return _clone_response(response, cached=False)
