from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


@dataclass
class ApiError:
    code: str
    message: str
    details: dict[str, object] = field(default_factory=dict)


@dataclass
class ApiResponse(Generic[T]):
    success: bool
    data: Optional[T]
    error: Optional[ApiError]
    request_id: str
    processing_time_ms: int = 0
