from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...dependencies import get_db
from ...schemas.common import ApiError, ApiResponse
from ...schemas.formula import FormulaAnalyzeRequest, FormulaAnalyzeResponse
from ...services.formula_service import analyze_formula


router = APIRouter(prefix="/formulas", tags=["formulas"])


@router.post("/analyze")
def formulas_analyze(
    request: FormulaAnalyzeRequest,
    db: Session | None = Depends(get_db),
) -> ApiResponse[FormulaAnalyzeResponse]:
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    try:
        data = analyze_formula(request, db=db)
        processing_time_ms = int((time.perf_counter() - start) * 1000)
        return ApiResponse(
            success=True,
            data=data,
            error=None,
            request_id=request_id,
            processing_time_ms=processing_time_ms,
        )
    except ValueError as exc:
        code = str(exc)
        message = {
            "EMPTY_INGREDIENTS": "Ingredients list is empty",
            "ALL_UNRESOLVED": "All ingredients are unresolved",
        }.get(code, "Formula analyze failed")
        processing_time_ms = int((time.perf_counter() - start) * 1000)
        return ApiResponse(
            success=False,
            data=None,
            error=ApiError(code=code, message=message),
            request_id=request_id,
            processing_time_ms=processing_time_ms,
        )
