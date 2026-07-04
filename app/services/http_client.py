import hashlib
import aiohttp
from fastapi import HTTPException
from app.core.circuit_breaker import CircuitBreaker
from app.services.redis_cache import RedisCache


class HttpClient:
    def __init__(self, circuit_breaker: CircuitBreaker, cache: RedisCache):
        self.cb = circuit_breaker
        self.cache = cache

    async def get(self, url: str, use_cache: bool = True) -> dict:
        # Проверяем кэш
        if use_cache:
            cache_key = self._cache_key(url)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return cached

        # Проверяем Circuit Breaker
        if not self.cb.allow_request():
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable (circuit open)"
            )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status >= 400:
                        raise aiohttp.ClientResponseError(
                            resp.request_info, resp.history, status=resp.status
                        )
                    data = await resp.json()

            self.cb.success()

            # Сохраняем в кэш
            if use_cache:
                await self.cache.set(cache_key, data)

            return data

        except aiohttp.ClientError as e:
            self.cb.failure()
            raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")

    @staticmethod
    def _cache_key(url: str) -> str:
        return f"cache:{hashlib.md5(url.encode()).hexdigest()}"