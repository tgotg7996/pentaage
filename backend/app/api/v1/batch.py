from __future__ import annotations

import json
from typing import cast

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response

from ...schemas.batch import BatchStatusResponse, BatchSubmitResponse
from ...services.batch_service import (
    get_batch_download,
    get_batch_status,
    submit_batch,
)


router = APIRouter(prefix="/batch", tags=["batch"])


def _normalize_idempotency_key(raw_key: str | None) -> str | None:
    if raw_key is None:
        return None
    normalized = raw_key.strip()
    return normalized or None


@router.post("/submit", status_code=202)
async def batch_submit(
    file: UploadFile = File(...),
    options: str = Form("{}"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> BatchSubmitResponse:
    try:
        parsed_options = json.loads(options)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="BATCH_FILE_INVALID") from exc
    if not isinstance(parsed_options, dict):
        raise HTTPException(status_code=400, detail="BATCH_FILE_INVALID")
    options_payload = cast(dict[str, object], parsed_options)

    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="BATCH_FILE_INVALID") from exc
    try:
        return submit_batch(
            csv_text,
            options=options_payload,
            idempotency_key=_normalize_idempotency_key(idempotency_key),
        )
    except ValueError as exc:
        if str(exc) == "IDEMPOTENCY_CONFLICT":
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT") from exc
        if str(exc) == "BATCH_FILE_INVALID":
            raise HTTPException(status_code=400, detail="BATCH_FILE_INVALID") from exc
        if str(exc) == "BATCH_FILE_TOO_LARGE":
            raise HTTPException(status_code=413, detail="BATCH_FILE_TOO_LARGE") from exc
        raise


@router.get("/{job_id}/status")
def batch_status(job_id: str) -> BatchStatusResponse:
    data = get_batch_status(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    return data


@router.get("/{job_id}/download")
def batch_download(job_id: str) -> Response:
    try:
        content = get_batch_download(job_id)
    except ValueError as exc:
        if str(exc) == "JOB_NOT_COMPLETED":
            raise HTTPException(status_code=409, detail="JOB_NOT_COMPLETED") from exc
        raise
    if content is None:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="batch-{job_id}.csv"'},
    )
