from __future__ import annotations

import re
import uuid
from uuid import UUID

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
_CACHE: dict[str, CompoundAnalyzeResponse] = {}


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
    result = CompoundResult(
        calc_id=UUID(response.calc_id),
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
    db.commit()


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
    if cache_key in _CACHE:
        return _clone_response(_CACHE[cache_key], cached=True)

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

    _CACHE[cache_key] = response
    return _clone_response(response, cached=False)
