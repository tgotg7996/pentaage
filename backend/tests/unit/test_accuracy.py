from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.fingerprint import morgan_fingerprint
from app.core.reference import load_reference_compounds
from app.core.similarity import tanimoto


def test_reference_top1_hit_rate_at_least_85_percent() -> None:
    references = load_reference_compounds()
    assert references

    hits = 0
    total = 0

    for query in references:
        query_smiles = query.get("canonical_smiles") or query.get("smiles") or ""
        query_cas = query.get("cas") or ""
        if not query_smiles or not query_cas:
            continue

        query_fp = morgan_fingerprint(query_smiles, radius=2, n_bits=2048)
        best_cas = ""
        best_score = -1.0

        for candidate in references:
            cand_smiles = candidate.get("canonical_smiles") or candidate.get("smiles") or ""
            cand_cas = candidate.get("cas") or ""
            if not cand_smiles or not cand_cas:
                continue

            cand_fp = morgan_fingerprint(cand_smiles, radius=2, n_bits=2048)
            score = tanimoto(query_fp, cand_fp)
            if score > best_score:
                best_score = score
                best_cas = cand_cas

        total += 1
        if best_cas == query_cas:
            hits += 1

    assert total > 0
    hit_rate = hits / total
    assert hit_rate >= 0.85
