from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from app.api.router import router
from app.core.logger import logger
from app.db.redis import redis
from app.core.config import settings
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.services.http_client import HttpClient
from app.services.redis_cache import RedisCache
from app.core.tracing import setup_tracing
from app.services.circuit_breaker_registry import CircuitBreakerRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация компонентов, живущих всё время жизни приложения
    cache = RedisCache(redis, default_ttl=settings.cache_ttl)
    cb_registry = CircuitBreakerRegistry(redis, failure_threshold=settings.circuit_breaker_failures,
                                         reset_timeout=settings.circuit_breaker_timeout)
    http_client = HttpClient(cb_registry, cache)
    app.state.http_client = http_client

    # Сохраняем в app.state для доступа через Depends
    app.state.http_client = http_client
    alembic_cfg = Config("alembic.ini")
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        logger.warning(f"Alembic auto-upgrade skipped: {e}")
    yield



app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
setup_tracing(app)



app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(router)
