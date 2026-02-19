from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...dependencies import get_db
from ...schemas.common import ApiError, ApiResponse
from ...schemas.compound import CompoundAnalyzeRequest, CompoundAnalyzeResponse
from ...services.compound_service import analyze_compound


router = APIRouter(prefix="/compounds", tags=["compounds"])


def post_compounds_analyze(
    request: CompoundAnalyzeRequest,
    db: Session | None = None,
) -> ApiResponse[CompoundAnalyzeResponse]:
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    try:
        data = analyze_compound(request, db=db)
        processing_time_ms = int((time.perf_counter() - start) * 1000)
        return ApiResponse(
            success=True,
            data=data,
            error=None,
            request_id=request_id,
            processing_time_ms=processing_time_ms,
        )
    except ValueError:
        processing_time_ms = int((time.perf_counter() - start) * 1000)
        return ApiResponse(
            success=False,
            data=None,
            error=ApiError(code="INVALID_SMILES", message="Invalid smiles string"),
            request_id=request_id,
            processing_time_ms=processing_time_ms,
        )


@router.post("/analyze")
def compounds_analyze(
    request: CompoundAnalyzeRequest,
    db: Session | None = Depends(get_db),
) -> ApiResponse[CompoundAnalyzeResponse]:
    return post_compounds_analyze(request, db=db)
