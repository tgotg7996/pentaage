from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ...schemas.batch import BatchStatusResponse, BatchSubmitResponse
from ...services.batch_service import (
    get_batch_download,
    get_batch_status,
    submit_batch,
)


router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("/submit")
async def batch_submit(
    file: UploadFile = File(...),
    options: str = Form("{}"),
) -> BatchSubmitResponse:
    try:
        options_payload = json.loads(options)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="BATCH_FILE_INVALID") from exc
    if not isinstance(options_payload, dict):
        raise HTTPException(status_code=400, detail="BATCH_FILE_INVALID")

    content = await file.read()
    csv_text = content.decode("utf-8")
    return submit_batch(csv_text, options=options_payload)


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
