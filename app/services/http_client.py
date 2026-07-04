import hashlib
import json

import aiohttp
from fastapi import HTTPException
from app.services.circuit_breaker_registry import CircuitBreakerRegistry
from app.services.redis_cache import RedisCache


class HttpClient:
    def __init__(self, circuit_breaker_registry: CircuitBreakerRegistry, cache: RedisCache):
        self.cb_registry = circuit_breaker_registry
        self.cache = cache

    async def get(self, service_name: str, url: str, params: dict = None, use_cache: bool = True) -> dict:
        cache_key = self._cache_key(url, params) if use_cache else None

        # Проверяем кэш
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return cached

        cb = self.cb_registry.get(service_name)

        if not await cb.allow_request():
            # Пытаемся вернуть stale cache, если есть
            if use_cache:
                stale = await self.cache.get(cache_key)  # можно хранить отдельно stale данные
                if stale:
                    return {**stale, "_cached": True, "_stale": True}
            raise HTTPException(status_code=503, detail="Service temporarily unavailable (circuit open)")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status >= 400:
                        raise aiohttp.ClientResponseError(
                            resp.request_info, resp.history, status=resp.status
                        )
                    data = await resp.json()

            await cb.success()

            if use_cache:
                await self.cache.set(cache_key, data)
            return data

        except aiohttp.ClientError as e:
            await cb.failure()
            # fallback: возвращаем закэшированные данные, если есть
            if use_cache:
                fallback = await self.cache.get(cache_key)
                if fallback:
                    return {**fallback, "_cached": True, "_fallback": True}
            raise HTTPException(status_code=502, detail=f"Upstream error: {e.status}")

    @staticmethod
    def _cache_key(url: str, params: dict = None) -> str:
        raw = url + (json.dumps(params, sort_keys=True) if params else "")
        return f"cache:{hashlib.md5(raw.encode()).hexdigest()}"
