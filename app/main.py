from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.router import router
from app.db.redis import redis
from app.core.config import settings
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.core.circuit_breaker import CircuitBreaker
from app.services.http_client import HttpClient
from app.services.redis_cache import RedisCache
from app.core.tracing import setup_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация компонентов, живущих всё время жизни приложения
    cache = RedisCache(redis, default_ttl=settings.cache_ttl)
    cb = CircuitBreaker(
        failure_threshold=settings.circuit_breaker_failures,
        reset_timeout=settings.circuit_breaker_timeout,
    )
    http_client = HttpClient(cb, cache)

    # Сохраняем в app.state для доступа через Depends
    app.state.http_client = http_client

    yield
    # cleanup если нужно

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
setup_tracing(app)

# Middleware: порядок важен!
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(router)