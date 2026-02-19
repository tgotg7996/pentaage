from __future__ import annotations

import time
import uuid

from fastapi import APIRouter

from ...schemas.common import ApiResponse
from ...schemas.formula import FormulaAnalyzeRequest, FormulaAnalyzeResponse
from ...services.formula_service import analyze_formula


router = APIRouter(prefix="/formulas", tags=["formulas"])


@router.post("/analyze")
def formulas_analyze(
    request: FormulaAnalyzeRequest,
) -> ApiResponse[FormulaAnalyzeResponse]:
    start = time.perf_counter()
    request_id = str(uuid.uuid4())

    data = analyze_formula(request)
    processing_time_ms = int((time.perf_counter() - start) * 1000)
    return ApiResponse(
        success=True,
        data=data,
        error=None,
        request_id=request_id,
        processing_time_ms=processing_time_ms,
    )
