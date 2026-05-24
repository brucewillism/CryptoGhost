"""CryptoGhost - Verificações de saúde reais dos serviços."""

import time
from typing import Any

import httpx
import redis
import redis.asyncio as aioredis
from sqlalchemy import text

from backend.shared.config import get_settings
from backend.shared.database import async_engine
from backend.shared.ai_providers.ollama_provider import OllamaProvider


async def check_database() -> dict[str, Any]:
    start = time.perf_counter()
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            pgvector = await conn.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            )
            has_pgvector = bool(pgvector.scalar())
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "healthy",
            "pgvector": has_pgvector,
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


async def check_redis() -> dict[str, Any]:
    settings = get_settings()
    start = time.perf_counter()
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        try:
            pong = await client.ping()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {"status": "healthy" if pong else "unhealthy", "latency_ms": latency_ms}
        finally:
            await client.aclose()
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


async def check_ollama() -> dict[str, Any]:
    settings = get_settings()
    if not settings.ollama_enabled:
        return {"status": "disabled", "message": "Ollama desabilitado via config"}

    provider = OllamaProvider()
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=settings.effective_ollama_timeout) as client:
            response = await client.get(f"{provider.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        primary = settings.effective_ollama_model
        secondary = settings.effective_ollama_model_secondary
        primary_available = any(primary in name or name.startswith(primary) for name in models)
        secondary_available = any(secondary in name or name.startswith(secondary) for name in models)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        status = "healthy" if primary_available or models else "degraded"
        return {
            "status": status,
            "url": provider.base_url,
            "latency_ms": latency_ms,
            "models_available": models[:10],
            "model_count": len(models),
            "primary_model": primary,
            "primary_available": primary_available,
            "secondary_model": secondary,
            "secondary_available": secondary_available,
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "url": provider.base_url,
            "error": str(exc),
        }


def check_celery() -> dict[str, Any]:
    settings = get_settings()
    start = time.perf_counter()
    broker_ok = False
    workers: list[str] = []
    error: str | None = None

    try:
        broker_client = redis.from_url(settings.celery_broker_url)
        try:
            broker_ok = bool(broker_client.ping())
        finally:
            broker_client.close()
    except Exception as exc:
        error = f"broker: {exc}"

    if broker_ok:
        try:
            from backend.shared.celery_app import celery_app

            inspect = celery_app.control.inspect(timeout=3.0)
            ping = inspect.ping()
            if ping:
                workers = list(ping.keys())
        except Exception as exc:
            if not error:
                error = f"inspect: {exc}"

    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    if broker_ok and workers:
        status = "healthy"
    elif broker_ok:
        status = "degraded"
    else:
        status = "unhealthy"

    result: dict[str, Any] = {
        "status": status,
        "broker_ok": broker_ok,
        "workers_online": len(workers),
        "workers": workers,
        "latency_ms": latency_ms,
    }
    if error:
        result["warning"] = error
    return result


async def check_full() -> dict[str, Any]:
    settings = get_settings()
    db = await check_database()
    redis_result = await check_redis()
    ollama_result = await check_ollama()
    celery_result = check_celery()

    checks = {
        "database": db,
        "redis": redis_result,
        "ollama": ollama_result,
        "celery": celery_result,
    }

    security = {
        "paper_trading": settings.paper_trading,
        "live_trading_enabled": settings.live_trading_enabled,
        "live_trading_allowed": settings.is_live_trading_allowed,
        "jwt_configured": bool(settings.jwt_secret and len(settings.jwt_secret) >= 32),
    }

    statuses = [c.get("status") for c in checks.values()]
    if any(s == "unhealthy" for s in statuses):
        overall = "unhealthy"
    elif any(s in ("degraded", "disabled") for s in statuses):
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "app": settings.app_name,
        "version": "5.0.0",
        "env": settings.env,
        "checks": checks,
        "security": security,
    }
