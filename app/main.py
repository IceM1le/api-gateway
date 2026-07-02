from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


@app.get("/")
async def root():
    return {
        "message": "API Gateway is running",
        "debug": settings.debug,
        "cache_ttl": settings.cache_ttl,
    }