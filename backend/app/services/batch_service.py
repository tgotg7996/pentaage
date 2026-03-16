from __future__ import annotations

import hashlib
import importlib
import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Optional, cast

from ..schemas.batch import BatchProgress, BatchStatusResponse, BatchSubmitResponse


BatchAnalyzeRunner = Callable[[list[str]], list[dict[str, str]]]
WorkerEnqueue = Callable[[list[str]], str]
WorkerResultGetter = Callable[[str], Optional[dict[str, object]]]


@dataclass
class BatchJobRecord:
    status: str
    total_count: int
    csv_content: str
    options: dict[str, object]
    success_count: int
    failed_count: int
    download_content: bytes | None
    worker_task_id: str | None


_BATCH_JOBS: dict[str, BatchJobRecord] = {}
_BATCH_IDEMPOTENCY: dict[str, tuple[str, str]] = {}
_BATCH_LOCK = threading.RLock()


def _build_payload_hash(csv_text: str, options: dict[str, object]) -> str:
    options_text = json.dumps(options, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload = f"{csv_text}\n{options_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _extract_data_rows(csv_text: str) -> list[str]:
    lines = [line for line in csv_text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("BATCH_FILE_INVALID")

    header = lines[0].strip().lower()
    if header != "smiles":
        raise ValueError("BATCH_FILE_INVALID")

    return lines[1:]


def _build_download_content(data_rows: list[str]) -> bytes:
    output_lines = ["smiles,status"]
    for row in data_rows:
        output_lines.append(f"{row},completed")
    return ("\n".join(output_lines) + "\n").encode("utf-8")


def _default_batch_analyze(rows: list[str]) -> list[dict[str, str]]:
    return [{"smiles": row, "status": "completed"} for row in rows]


def _get_batch_analyze_runner() -> BatchAnalyzeRunner:
    try:
        module = importlib.import_module("worker.tasks.batch_analyze")
        runner = getattr(module, "run_batch_analyze")
    except (ModuleNotFoundError, AttributeError):
        return _default_batch_analyze
    if not callable(runner):
        return _default_batch_analyze
    return cast(BatchAnalyzeRunner, runner)


def _get_batch_worker_bridge() -> Optional[tuple[WorkerEnqueue, WorkerResultGetter]]:
    try:
        module = importlib.import_module("worker.tasks.batch_analyze")
    except ModuleNotFoundError:
        return None

    enqueue = getattr(module, "enqueue_batch_analyze", None)
    get_result = getattr(module, "get_batch_task_result", None)
    if not callable(enqueue) or not callable(get_result):
        return None
    return cast(WorkerEnqueue, enqueue), cast(WorkerResultGetter, get_result)


def _build_download_from_results(analyze_results: list[dict[str, str]]) -> bytes:
    output_lines = ["smiles,status"]
    for item in analyze_results:
        smiles = str(item.get("smiles", "")).strip()
        status = str(item.get("status", "failed")).strip() or "failed"
        output_lines.append(f"{smiles},{status}")
    return ("\n".join(output_lines) + "\n").encode("utf-8")


def _apply_terminal_result(job_id: str, analyze_results: list[dict[str, str]]) -> None:
    success_count = sum(1 for item in analyze_results if item.get("status") == "completed")
    failed_count = max(len(analyze_results) - success_count, 0)
    download_content = _build_download_from_results(analyze_results)

    with _BATCH_LOCK:
        record = _BATCH_JOBS.get(job_id)
        if record is None or record.status != "running":
            return
        record.download_content = download_content
        record.success_count = success_count
        record.failed_count = failed_count
        record.status = "completed"


def _apply_failed_result(job_id: str) -> None:
    with _BATCH_LOCK:
        record = _BATCH_JOBS.get(job_id)
        if record is None or record.status != "running":
            return
        record.success_count = 0
        record.failed_count = record.total_count
        record.status = "failed"


def _run_job_via_worker(job_id: str, data_rows: list[str]) -> bool:
    bridge = _get_batch_worker_bridge()
    if bridge is None:
        return False

    enqueue, get_result = bridge
    worker_task_id = enqueue(data_rows)
    with _BATCH_LOCK:
        record = _BATCH_JOBS.get(job_id)
        if record is None or record.status != "running":
            return True
        record.worker_task_id = worker_task_id

    for _ in range(300):
        task_result = get_result(worker_task_id)
        if task_result is None:
            time.sleep(0.01)
            continue

        state = str(task_result.get("state", "PENDING")).upper()
        if state in {"PENDING", "RUNNING"}:
            time.sleep(0.01)
            continue

        if state == "SUCCESS":
            raw_results = task_result.get("result", [])
            if isinstance(raw_results, list):
                analyze_results = [item for item in raw_results if isinstance(item, dict)]
                normalized = [cast(dict[str, str], item) for item in analyze_results]
                _apply_terminal_result(job_id, normalized)
            else:
                _apply_failed_result(job_id)
            return True

        _apply_failed_result(job_id)
        return True

    _apply_failed_result(job_id)
    return True


def _run_job_async(job_id: str) -> None:
    with _BATCH_LOCK:
        record = _BATCH_JOBS.get(job_id)
        if record is None or record.status != "pending":
            return
        record.status = "running"

    time.sleep(0.05)

    with _BATCH_LOCK:
        record = _BATCH_JOBS.get(job_id)
        if record is None or record.status != "running":
            return
        csv_text = record.csv_content

    try:
        data_rows = _extract_data_rows(csv_text)
    except Exception:
        _apply_failed_result(job_id)
        return

    try:
        if _run_job_via_worker(job_id, data_rows):
            return
        analyze_results = _get_batch_analyze_runner()(data_rows)
    except Exception:
        _apply_failed_result(job_id)
        return

    _apply_terminal_result(job_id, analyze_results)


def submit_batch(
    csv_text: str,
    options: dict[str, object] | None = None,
    idempotency_key: str | None = None,
) -> BatchSubmitResponse:
    normalized_options = options or {}
    payload_hash = _build_payload_hash(csv_text, normalized_options)

    if idempotency_key:
        with _BATCH_LOCK:
            hit = _BATCH_IDEMPOTENCY.get(idempotency_key)
            if hit is not None:
                existing_hash, existing_job_id = hit
                if existing_hash != payload_hash:
                    raise ValueError("IDEMPOTENCY_CONFLICT")
                record = _BATCH_JOBS[existing_job_id]
                return BatchSubmitResponse(
                    job_id=existing_job_id,
                    status=record.status,
                    total_count=record.total_count,
                )

    csv_bytes_size = len(csv_text.encode("utf-8"))
    if csv_bytes_size > 10 * 1024 * 1024:
        raise ValueError("BATCH_FILE_TOO_LARGE")

    data_rows = _extract_data_rows(csv_text)
    total_count = len(data_rows)
    if total_count > 10000:
        raise ValueError("BATCH_FILE_TOO_LARGE")

    job_id = str(uuid.uuid4())
    with _BATCH_LOCK:
        _BATCH_JOBS[job_id] = BatchJobRecord(
            status="pending",
            total_count=total_count,
            csv_content=csv_text,
            options=normalized_options,
            success_count=0,
            failed_count=0,
            download_content=None,
            worker_task_id=None,
        )

        if idempotency_key:
            _BATCH_IDEMPOTENCY[idempotency_key] = (payload_hash, job_id)

    threading.Thread(target=_run_job_async, args=(job_id,), daemon=True).start()

    return BatchSubmitResponse(
        job_id=job_id,
        status="pending",
        total_count=total_count,
    )


def get_batch_status(job_id: str) -> BatchStatusResponse | None:
    with _BATCH_LOCK:
        record = _BATCH_JOBS.get(job_id)
        if record is None:
            return None

        return BatchStatusResponse(
            job_id=job_id,
            status=record.status,
            progress=BatchProgress(
                total=record.total_count,
                success=record.success_count,
                failed=record.failed_count,
            ),
            eta_seconds=0 if record.status in {"completed", "failed"} else 3,
        )


def get_batch_download(job_id: str) -> bytes | None:
    with _BATCH_LOCK:
        record = _BATCH_JOBS.get(job_id)
        if record is None:
            return None
        if record.status != "completed":
            raise ValueError("JOB_NOT_COMPLETED")
        if record.download_content is None:
            data_rows = _extract_data_rows(record.csv_content)
            record.download_content = _build_download_content(data_rows)
        return record.download_content
