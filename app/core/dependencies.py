from app.core.rate_limiter import RateLimiter
from app.db.redis import redis

rate_limiter = RateLimiter(redis)