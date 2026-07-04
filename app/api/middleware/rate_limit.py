import re
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import JSONResponse
from app.core.dependencies import rate_limiter

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(status_code=401, content={"detail": "Missing API key"})

        # Извлекаем service из пути: /api/weather/...
        parts = request.url.path.split("/")
        service = parts[2] if len(parts) > 2 else "unknown"

        allowed = await rate_limiter.is_allowed(api_key, service)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded for {service}"},
                headers={"Retry-After": str(settings.rate_limit_window)},
            )
        return await call_next(request)