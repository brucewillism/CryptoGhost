"""Execução síncrona de tasks quando Redis/Celery indisponível."""

from collections.abc import Callable
from typing import Any, TypeVar

from backend.shared.health_service import check_redis
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.v6.sync_runner")

T = TypeVar("T")


async def run_task_or_sync(
    celery_task: Callable[..., Any],
    sync_fn: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """Tenta Celery; se Redis down, executa função síncrona inline."""
    redis_status = await check_redis()
    if redis_status.get("status") == "healthy":
        try:
            celery_task.delay(*args, **kwargs)
            logger.info("task_queued", task=getattr(celery_task, "name", str(celery_task)))
            return sync_fn(*args, **kwargs)
        except Exception as exc:
            logger.warning("celery_queue_failed", error=str(exc))
    return sync_fn(*args, **kwargs)
