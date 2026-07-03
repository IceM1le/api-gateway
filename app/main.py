from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends

from app.api.dependencies import require_api_key
from app.api.router import router
from app.core.rate_limiter import RateLimiter
from app.db.redis import redis
from app.core.config import settings
from app.api.middleware.middleware import LoggingMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.core.circuit_breaker import CircuitBreaker
from app.services.http_client import HttpClient
from app.services.cache_service import CacheService
from app.services.aggregation_service import AggregationService

rate_limiter = RateLimiter(redis)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

app.include_router(router)

circuit_breaker = CircuitBreaker(
    failure_threshold=settings.circuit_breaker_failures,
    reset_timeout=settings.circuit_breaker_timeout
)

cache_service = CacheService(
    redis,
    ttl=settings.cache_ttl
)

http_client = HttpClient(
    circuit_breaker=circuit_breaker,
    cache=cache_service
)

aggregation_service = AggregationService(http_client)


@app.get("/api/dashboard")
async def dashboard(api_key: str = Depends(require_api_key)):
    return await aggregation_service.get_dashboard()
