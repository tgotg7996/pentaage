from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass

from ..schemas.batch import BatchProgress, BatchStatusResponse, BatchSubmitResponse


@dataclass
class BatchJobRecord:
    status: str
    total_count: int
    csv_content: str
    options: dict[str, object]


_BATCH_JOBS: dict[str, BatchJobRecord] = {}
_BATCH_IDEMPOTENCY: dict[str, tuple[str, str]] = {}


def _build_payload_hash(csv_text: str, options: dict[str, object]) -> str:
    options_text = json.dumps(options, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload = f"{csv_text}\n{options_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def submit_batch(
    csv_text: str,
    options: dict[str, object] | None = None,
    idempotency_key: str | None = None,
) -> BatchSubmitResponse:
    normalized_options = options or {}
    payload_hash = _build_payload_hash(csv_text, normalized_options)

    if idempotency_key:
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

    lines = [line for line in csv_text.splitlines() if line.strip()]
    total_count = max(len(lines) - 1, 0)
    job_id = str(uuid.uuid4())
    _BATCH_JOBS[job_id] = BatchJobRecord(
        status="completed",
        total_count=total_count,
        csv_content=csv_text,
        options=normalized_options,
    )

    if idempotency_key:
        _BATCH_IDEMPOTENCY[idempotency_key] = (payload_hash, job_id)

    return BatchSubmitResponse(
        job_id=job_id,
        status="completed",
        total_count=total_count,
    )


def get_batch_status(job_id: str) -> BatchStatusResponse | None:
    record = _BATCH_JOBS.get(job_id)
    if record is None:
        return None
    return BatchStatusResponse(
        job_id=job_id,
        status=record.status,
        progress=BatchProgress(
            total=record.total_count,
            success=record.total_count,
            failed=0,
        ),
        eta_seconds=0,
    )


def get_batch_download(job_id: str) -> bytes | None:
    record = _BATCH_JOBS.get(job_id)
    if record is None:
        return None
    lines = [line for line in record.csv_content.splitlines() if line.strip()]
    data_rows = lines[1:] if lines else []
    output_lines = ["smiles,status"]
    for row in data_rows:
        output_lines.append(f"{row},completed")
    return ("\n".join(output_lines) + "\n").encode("utf-8")
