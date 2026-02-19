from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import cast


@lru_cache(maxsize=1)
def load_reference_compounds() -> list[dict[str, str]]:
    fixture_path = Path(__file__).resolve().parents[2] / "tests/fixtures/reference_compounds.json"
    with fixture_path.open("r", encoding="utf-8") as file_obj:
        payload_obj = cast(object, json.load(file_obj))

    if not isinstance(payload_obj, list):
        return []
    payload = cast(list[object], payload_obj)

    records: list[dict[str, str]] = []
    for item_obj in payload:
        if not isinstance(item_obj, dict):
            continue
        item = cast(dict[str, object], item_obj)
        normalized = {key: str(value) for key, value in item.items()}
        records.append(normalized)

    return records
