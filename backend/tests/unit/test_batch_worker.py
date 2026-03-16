from __future__ import annotations

import importlib
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def _worker_module():
    return importlib.import_module("worker.tasks.batch_analyze")


def _wait_terminal(task_id: str, timeout_seconds: float = 1.0) -> dict[str, object]:
    module = _worker_module()
    get_batch_task_result = getattr(module, "get_batch_task_result")
    deadline = time.time() + timeout_seconds
    last: dict[str, object] | None = None
    while time.time() < deadline:
        result = get_batch_task_result(task_id)
        if result is None:
            time.sleep(0.01)
            continue
        result_dict = dict(result)
        last = result_dict
        state = str(result_dict.get("state", "")).upper()
        if state in {"SUCCESS", "FAILURE"}:
            return result_dict
        time.sleep(0.01)
    assert last is not None
    raise AssertionError(f"task did not complete in time, last={last}")


def test_worker_batch_task_success() -> None:
    module = _worker_module()
    enqueue_batch_analyze = getattr(module, "enqueue_batch_analyze")
    task_id = enqueue_batch_analyze(["CCO", "CCC"])
    result = _wait_terminal(task_id)

    assert result["state"] == "SUCCESS"
    payload = result.get("result", [])
    assert isinstance(payload, list)
    assert len(payload) == 2


def test_worker_batch_task_failure() -> None:
    module = _worker_module()
    enqueue_batch_analyze = getattr(module, "enqueue_batch_analyze")
    with patch("worker.tasks.batch_analyze.run_batch_analyze", side_effect=RuntimeError("boom")):
        task_id = enqueue_batch_analyze(["CCO"])
        result = _wait_terminal(task_id)

    assert result["state"] == "FAILURE"
    assert "boom" in str(result.get("error", ""))
