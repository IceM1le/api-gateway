import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
from app.db.dependencies import AsyncSessionLocal
from app.services.request_log_service import log_request
from app.core.logger import logger
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Генерируем request_id и сохраняем в состоянии запроса
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Добавляем request_id в текущий OTel спан как атрибут
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attribute("http.request_id", request_id)

        start_time = time.time()
        client_key = request.headers.get("X-API-Key", "unknown")

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # Прометеус метрики
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration_ms / 1000)

        # Асинхронная запись в БД
        async with AsyncSessionLocal() as db:
            await log_request(
                db=db,
                client_key=client_key,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
            )
            try:
                await db.commit()
            except Exception as e:
                logger.error(f"DB logging failed: {e}")
                await db.rollback()

        # Добавляем X-Request-ID в ответ
        response.headers["X-Request-ID"] = request_id
        return response