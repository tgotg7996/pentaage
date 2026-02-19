from dataclasses import dataclass
from typing import Optional


@dataclass
class BatchSubmitResponse:
    job_id: str
    status: str
    total_count: int


@dataclass
class BatchProgress:
    total: int
    success: int
    failed: int


@dataclass
class BatchStatusResponse:
    job_id: str
    status: str
    progress: BatchProgress
    eta_seconds: Optional[int] = None
