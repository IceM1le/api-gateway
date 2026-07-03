from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.router import router
from app.core.config import settings
from app.api.middleware import LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)

app.include_router(router)
