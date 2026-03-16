from __future__ import annotations

import threading
import uuid
from typing import TypedDict


class BatchTaskResult(TypedDict, total=False):
    state: str
    result: list[dict[str, str]]
    error: str


_TASK_LOCK = threading.RLock()
_TASK_RESULTS: dict[str, BatchTaskResult] = {}


def run_batch_analyze(rows: list[str]) -> list[dict[str, str]]:
    return [{"smiles": row, "status": "completed"} for row in rows]


def _execute_task(task_id: str, rows: list[str]) -> None:
    with _TASK_LOCK:
        _TASK_RESULTS[task_id] = {"state": "RUNNING"}

    try:
        result = run_batch_analyze(rows)
    except Exception as exc:
        with _TASK_LOCK:
            _TASK_RESULTS[task_id] = {"state": "FAILURE", "error": str(exc)}
        return

    with _TASK_LOCK:
        _TASK_RESULTS[task_id] = {"state": "SUCCESS", "result": result}


def enqueue_batch_analyze(rows: list[str]) -> str:
    task_id = str(uuid.uuid4())
    with _TASK_LOCK:
        _TASK_RESULTS[task_id] = {"state": "PENDING"}
    threading.Thread(target=_execute_task, args=(task_id, list(rows)), daemon=True).start()
    return task_id


def get_batch_task_result(task_id: str) -> BatchTaskResult | None:
    with _TASK_LOCK:
        result = _TASK_RESULTS.get(task_id)
        if result is None:
            return None
        snapshot: BatchTaskResult = {}
        if "state" in result:
            snapshot["state"] = str(result["state"])
        if "result" in result and isinstance(result["result"], list):
            snapshot["result"] = result["result"]
        if "error" in result:
            snapshot["error"] = str(result["error"])
        return snapshot
