import time
import uuid
from redis.asyncio import Redis
from app.core.config import settings


class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.limit = settings.rate_limit
        self.window = settings.rate_limit_window

    async def is_allowed(self, api_key: str) -> bool:
        now = time.time()
        key = f"rate:{api_key}"
        window_start = now - self.window

        # 1. сначала чистим старые
        await self.redis.zremrangebyscore(key, 0, window_start)

        # 2. добавляем текущий запрос
        await self.redis.zadd(key, {str(uuid.uuid4()): now})

        # 3. считаем
        count = await self.redis.zcard(key)

        # 4. ограничение
        if count > self.limit:
            return False

        # 5. TTL
        await self.redis.expire(key, self.window)

        return True