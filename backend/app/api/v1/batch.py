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
    csv_text = content.decode("utf-8")
    try:
        return submit_batch(
            csv_text,
            options=options_payload,
            idempotency_key=idempotency_key.strip() if idempotency_key else None,
        )
    except ValueError as exc:
        if str(exc) == "IDEMPOTENCY_CONFLICT":
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT") from exc
        raise


@router.get("/{job_id}/status")
def batch_status(job_id: str) -> BatchStatusResponse:
    data = get_batch_status(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    return data


@router.get("/{job_id}/download")
def batch_download(job_id: str) -> Response:
    content = get_batch_download(job_id)
    if content is None:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="batch-{job_id}.csv"'},
    )
