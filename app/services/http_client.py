import hashlib
import json

import aiohttp
from fastapi import HTTPException
from app.core.circuit_breaker import CircuitBreaker
from app.services.redis_cache import RedisCache


class HttpClient:
    def __init__(self, circuit_breaker: CircuitBreaker, cache: RedisCache):
        self.cb = circuit_breaker
        self.cache = cache

    async def get(self, url: str, use_cache: bool = True, params: dict = None) -> dict:
        if use_cache:
            cache_key = self._cache_key(url, params)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return cached

        if not self.cb.allow_request():
            raise HTTPException(status_code=503, detail="Service temporarily unavailable (circuit open)")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status >= 400:
                        raise aiohttp.ClientResponseError(
                            resp.request_info, resp.history, status=resp.status
                        )
                    data = await resp.json()

            self.cb.success()

            if use_cache:
                await self.cache.set(cache_key, data)

            return data

        except aiohttp.ClientError as e:
            self.cb.failure()
            raise HTTPException(status_code=502,
                                detail=f"Upstream error: {e.status}, message='{e.message}', url='{url}'")

    @staticmethod
    def _cache_key(url: str, params: dict = None) -> str:
        raw = url + (json.dumps(params, sort_keys=True) if params else "")
        return f"cache:{hashlib.md5(raw.encode()).hexdigest()}"
