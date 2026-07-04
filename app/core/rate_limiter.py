import time
import uuid
from redis.asyncio import Redis
from app.core.config import settings


class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.limit = settings.rate_limit
        self.window = settings.rate_limit_window

    async def is_allowed(self, api_key: str, service: str = "global") -> bool:
        now = time.time()
        key = f"rate:{api_key}:{service}"
        window_start = now - self.window

        await self.redis.zremrangebyscore(key, 0, window_start)
        await self.redis.zadd(key, {str(uuid.uuid4()): now})
        count = await self.redis.zcard(key)

        # Берём лимит для этого API-ключа
        limit = self.limit
        if count > limit:
            return False

        await self.redis.expire(key, self.window)
        return True