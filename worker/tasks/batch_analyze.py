from __future__ import annotations


def run_batch_analyze(rows: list[str]) -> list[dict[str, str]]:
    return [{"smiles": row, "status": "completed"} for row in rows]
