import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.dependencies import AsyncSessionLocal
from app.services.request_log_service import log_request
from app.core.logger import logger
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY

class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # извлекаем API key
        client_key = request.headers.get("X-API-Key", "unknown")

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration_ms / 1000)
        request_id = getattr(request.state, "request_id", None)

        if request_id is None:
            request_id = "no-trace"
        async with AsyncSessionLocal() as db:
            await log_request(
                db=db,
                client_key=client_key,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
            )
            await db.commit()

        return response
