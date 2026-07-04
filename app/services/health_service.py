from sqlalchemy import text

from app.db.dependencies import AsyncSessionLocal
from app.db.redis import redis


class HealthService:

    async def postgres(self) -> bool:
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def redis(self) -> bool:
        try:
            await redis.ping()
            return True
        except Exception:
            return False

    async def health(self):
        postgres = await self.postgres()
        redis_status = await self.redis()

        status = (
            "ok"
            if postgres and redis_status
            else "degraded"
        )

        return {
            "status": status,
            "postgres": "up" if postgres else "down",
            "redis": "up" if redis_status else "down",
        }