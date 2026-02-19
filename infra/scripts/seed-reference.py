from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast


REQUIRED_FIELDS = {
    "name_cn",
    "name_en",
    "cas",
    "smiles",
    "canonical_smiles",
    "fingerprint_version",
}


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[2] / "backend/tests/fixtures/reference_compounds.json"


def _load_records(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        data_obj: object = json.load(f)
    if not isinstance(data_obj, list):
        raise ValueError("fixture must be a JSON array")
    data = cast(list[object], data_obj)

    records: list[dict[str, str]] = []
    for index, item_obj in enumerate(data, start=1):
        if not isinstance(item_obj, dict):
            raise ValueError(f"record #{index} must be an object")
        item = cast(dict[str, object], item_obj)
        missing = REQUIRED_FIELDS - set(item.keys())
        if missing:
            missing_csv = ", ".join(sorted(missing))
            raise ValueError(f"record #{index} missing fields: {missing_csv}")
        normalized = {k: str(item.get(k, "")).strip() for k in REQUIRED_FIELDS}
        if not normalized["cas"]:
            raise ValueError(f"record #{index} has empty cas")
        records.append(normalized)

    return records


def _upsert_with_psql(database_url: str, records: list[dict[str, str]]) -> None:
    payload = json.dumps(records, ensure_ascii=False)
    sql = f"""
BEGIN;
WITH payload AS (
  SELECT *
  FROM jsonb_to_recordset($${payload}$$::jsonb) AS x(
    name_cn text,
    name_en text,
    cas text,
    smiles text,
    canonical_smiles text,
    fingerprint_version text
  )
)
INSERT INTO reference_compounds (
  name_cn,
  name_en,
  cas,
  smiles,
  canonical_smiles,
  fingerprint_version
)
SELECT
  name_cn,
  name_en,
  cas,
  smiles,
  canonical_smiles,
  fingerprint_version
FROM payload
ON CONFLICT (cas) DO UPDATE
SET
  name_cn = EXCLUDED.name_cn,
  name_en = EXCLUDED.name_en,
  smiles = EXCLUDED.smiles,
  canonical_smiles = EXCLUDED.canonical_smiles,
  fingerprint_version = EXCLUDED.fingerprint_version;
COMMIT;
"""

    result = subprocess.run(
        ["psql", database_url, "-v", "ON_ERROR_STOP=1", "-c", sql],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "psql execution failed")


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("DATABASE_URL is required")

    fixture = _fixture_path()
    records = _load_records(fixture)
    _upsert_with_psql(database_url, records)
    print(f"seeded {len(records)} reference compounds")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"seed-reference failed: {exc}", file=sys.stderr)
        raise
