from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends

from app.api.dependencies import require_api_key
from app.api.router import router
from app.db.redis import redis
from app.core.config import settings
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.core.circuit_breaker import CircuitBreaker
from app.services.dashboard_service import DashboardService
from app.services.http_client import HttpClient
from app.services.cache_service import CacheService
from app.services.aggregation_service import AggregationService
from app.api.middleware.tracing import TracingMiddleware
from app.core.dependencies import rate_limiter
from app.services.weather_service import WeatherService
from app.api.middleware.metrics import MetricsMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.total_requests = 0
    app.state.total_time = 0.0

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)
app.add_middleware(TracingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)

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

weather_service = WeatherService(http_client)
dashboard_service = DashboardService(http_client)


@app.get("/api/weather")
async def weather(api_key: str = Depends(require_api_key)):
    return await weather_service.get_weather()


@app.get("/api/dashboard")
async def dashboard(api_key: str = Depends(require_api_key)):
    return await dashboard_service.get_dashboard()

@app.get("/metrics")
async def metrics():

    total = app.state.total_requests

    avg = (
        app.state.total_time / total
        if total
        else 0
    )

    return {
        "total_requests": total,
        "average_response_time": round(avg * 1000, 2),
    }