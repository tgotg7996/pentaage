from fastapi import APIRouter

from .batch import router as batch_router
from .compounds import router as compounds_router
from .formulas import router as formulas_router


router = APIRouter(prefix="/api/v1")
router.include_router(compounds_router)
router.include_router(formulas_router)
router.include_router(batch_router)
