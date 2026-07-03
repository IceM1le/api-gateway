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

http_client = HttpClient(circuit_breaker)

@app.get("/api/weather-test")
async def weather_test(api_key: str = Depends(require_api_key)):
    return await http_client.get("https://httpbin.org/json")
@app.post("/api/cb/reset")
async def reset_cb(api_key: str = Depends(require_api_key)):
    circuit_breaker.state = "closed"
    circuit_breaker.failures = 0
    circuit_breaker.opened_at = None   # 👈 ВОТ ЭТОГО НЕ ХВАТАЛО
    return {"ok": True}
@app.get("/cb-state")
async def cb_state(api_key: str = Depends(require_api_key)):
    return {
        "state": circuit_breaker.state,
        "failures": circuit_breaker.failures,
        "opened_at": circuit_breaker.opened_at
    }