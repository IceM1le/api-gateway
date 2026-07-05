import time
from enum import Enum
from redis.asyncio import Redis

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, redis: Redis, service_name: str, failure_threshold: int = 5, reset_timeout: int = 30):
        self.redis = redis
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._state_key = f"cb:{service_name}:state"
        self._failures_key = f"cb:{service_name}:failures"
        self._opened_at_key = f"cb:{service_name}:opened_at"

    async def _get_state(self) -> CircuitState:
        state = await self.redis.get(self._state_key)
        return CircuitState(state) if state else CircuitState.CLOSED

    async def _set_state(self, state: CircuitState):
        await self.redis.set(self._state_key, state.value)

    async def allow_request(self) -> bool:
        state = await self._get_state()
        if state == CircuitState.OPEN:
            opened_at = float(await self.redis.get(self._opened_at_key) or 0)
            if time.time() - opened_at > self.reset_timeout:
                await self._set_state(CircuitState.HALF_OPEN)
                return True
            return False
        return True

    async def success(self):
        await self.redis.delete(self._failures_key)
        await self._set_state(CircuitState.CLOSED)

    async def failure(self):
        failures = await self.redis.incr(self._failures_key)
        if failures >= self.failure_threshold:
            await self._set_state(CircuitState.OPEN)
            await self.redis.set(self._opened_at_key, time.time())

class CircuitBreakerRegistry:
    def __init__(self, redis: Redis, failure_threshold: int = 5, reset_timeout: int = 30):
        self.redis = redis
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._breakers: dict[str, CircuitBreaker] = {}

    def get(self, service_name: str) -> CircuitBreaker:
        if service_name not in self._breakers:
            self._breakers[service_name] = CircuitBreaker(
                self.redis, service_name, self.failure_threshold, self.reset_timeout
            )
        return self._breakers[service_name]