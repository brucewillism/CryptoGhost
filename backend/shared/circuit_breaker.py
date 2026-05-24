"""CryptoGhost - Circuit breaker e retry patterns."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, TypeVar

from tenacity import retry, stop_after_attempt, wait_exponential

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.circuit_breaker")

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker para proteção contra falhas em cascata."""

    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    _callbacks: list[Callable[[], None]] = field(default_factory=list)

    def call(self, func: Callable[[], T]) -> T:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("circuit_breaker_half_open", name=self.name)
            else:
                raise RuntimeError(f"Circuit breaker '{self.name}' está OPEN")

        try:
            result = func()
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure(exc)
            raise

    def _on_success(self) -> None:
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("circuit_breaker_closed", name=self.name)

    def _on_failure(self, exc: Exception) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning("circuit_breaker_failure", name=self.name, count=self.failure_count, error=str(exc))
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error("circuit_breaker_open", name=self.name)
            for callback in self._callbacks:
                callback()

    def on_open(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)


def with_retry(max_attempts: int = 3):
    """Decorator de retry com backoff exponencial."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
