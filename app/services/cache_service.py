import hashlib
import json
from typing import Optional, Any
from redis.asyncio import Redis


class CacheService:
    def __init__(self, redis: Redis, ttl: int = 300):
        self.redis = redis
        self.ttl = ttl

    async def get(self, url: str):
        cache_key = self.build_cache_key(url)

        # 1. CACHE HIT
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # 2. CIRCUIT BREAKER CHECK
        if not self.cb.allow_request():
            raise Exception("Circuit open")

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    data = await resp.json()

            # 3. SUCCESS → cache it
            self.cb.success()
            await self.cache.set(cache_key, data)

            return data

        except Exception:
            self.cb.failure()
            raise

    async def set(self, key: str, value: Any):
        await self.redis.set(
            key,
            json.dumps(value),
            ex=self.ttl
        )

    async def delete(self, key: str):
        await self.redis.delete(key)

def build_cache_key(self, url: str):
    return f"cache:{hashlib.md5(url.encode()).hexdigest()}"