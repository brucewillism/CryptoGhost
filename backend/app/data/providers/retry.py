"""Retry policy com exponential backoff."""

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = 3,
    backoff: float = 1.5,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except exceptions as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                time.sleep(backoff ** attempt)
    raise last_exc  # type: ignore[misc]
