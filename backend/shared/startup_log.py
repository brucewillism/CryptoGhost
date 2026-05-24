"""CryptoGhost - Logs estruturados de inicialização."""

from backend.shared.logging_config import get_logger

_loggers: dict[str, object] = {}


def _get(tag: str):
    if tag not in _loggers:
        _loggers[tag] = get_logger(f"cryptoghost.{tag.lower()}")
    return _loggers[tag]


def startup(msg: str, **kwargs) -> None:
    _get("startup").info(f"[STARTUP] {msg}", **kwargs)


def database(msg: str, **kwargs) -> None:
    _get("database").info(f"[DATABASE] {msg}", **kwargs)


def redis_log(msg: str, **kwargs) -> None:
    _get("redis").info(f"[REDIS] {msg}", **kwargs)


def ollama(msg: str, **kwargs) -> None:
    _get("ollama").info(f"[OLLAMA] {msg}", **kwargs)


def ai(msg: str, **kwargs) -> None:
    _get("ai").info(f"[AI] {msg}", **kwargs)


def celery_log(msg: str, **kwargs) -> None:
    _get("celery").info(f"[CELERY] {msg}", **kwargs)


def api(msg: str, **kwargs) -> None:
    _get("api").info(f"[API] {msg}", **kwargs)


def frontend(msg: str, **kwargs) -> None:
    _get("frontend").info(f"[FRONTEND] {msg}", **kwargs)
