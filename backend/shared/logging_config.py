"""CryptoGhost - Logging estruturado."""

import logging
import sys
from typing import Any

import structlog

from backend.shared.config import get_settings


def configure_logging() -> None:
    """Configura logging estruturado para todo o CryptoGhost."""
    settings = get_settings()
    log_level = logging.DEBUG if settings.debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if settings.env == "production"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Retorna logger estruturado nomeado."""
    return structlog.get_logger(name)
