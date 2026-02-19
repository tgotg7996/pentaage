from fastapi import FastAPI

from .api.v1.router import router as v1_router


def create_app() -> FastAPI:
    api = FastAPI(title="PentaAge API", version="0.1.0")
    api.include_router(v1_router)
    return api


app = create_app()
