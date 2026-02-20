from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "healthy",
        "components": {
            "db": "healthy",
            "redis": "healthy",
            "rdkit": "healthy",
        },
    }
