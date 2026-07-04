from fastapi import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time, uuid
from app.db.dependencies import AsyncSessionLocal
from app.services.request_log_service import log_request
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY
from opentelemetry import trace
from fastapi import Request


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attribute("http.request_id", request_id)

        start_time = time.time()
        client_key = request.headers.get("X-API-Key", "unknown")
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Записываем метрики
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(duration_ms / 1000)

        # Фоновая задача для логирования
        background = BackgroundTasks()
        background.add_task(self._log_to_db, client_key, str(request.url.path), response.status_code, duration_ms,
                            request_id)

        response.headers["X-Request-ID"] = request_id
        # Добавляем background tasks к ответу (если это обычный Response, не Streaming)
        if isinstance(response, Response):
            response.background = background
        else:
            # Для других типов ответов (например, JSONResponse) нужно так:
            response.raw_headers.append((b"x-request-id", request_id.encode()))
        return response

    @staticmethod
    async def _log_to_db(client_key, endpoint, status_code, duration_ms, request_id):
        async with AsyncSessionLocal() as db:
            await log_request(db, client_key, endpoint, status_code, duration_ms, request_id)
            try:
                await db.commit()
            except Exception as e:
                logger.error(f"DB logging failed: {e}")
                await db.rollback()
