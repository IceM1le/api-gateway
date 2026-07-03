import time
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

        self.failures = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    def allow_request(self) -> bool:
        if self.state == CircuitState.OPEN:
            if time.time() - self.opened_at > self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        return True

    def success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED

    def failure(self):
        self.failures += 1

        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.time()