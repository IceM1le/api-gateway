from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import JSONResponse

from app.core.dependencies import rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):

        if not request.url.path.startswith("/api"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key"}
            )

        allowed = await self.rate_limiter.is_allowed(api_key)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )

        return await call_next(request)