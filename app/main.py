from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    print("App starting...")

    yield

    # shutdown
    print("App shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {"message": "API Gateway is running"}