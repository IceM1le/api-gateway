import json
from typing import Any, Optional
from redis.asyncio import Redis


class RedisCache:
    def __init__(self, redis: Redis, default_ttl: int = 300):
        self.redis = redis
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        if value is not None:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        await self.redis.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)