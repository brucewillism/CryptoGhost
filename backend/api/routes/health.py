"""CryptoGhost - Endpoints de health check com validação real."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.shared.config import get_settings
from backend.shared.health_service import (
    check_celery,
    check_database,
    check_full,
    check_ollama,
    check_redis,
)

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health_basic() -> dict:
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "5.0.0",
        "env": settings.env,
        "paper_trading": settings.paper_trading,
        "live_trading_enabled": settings.live_trading_enabled,
        "ollama_url": settings.effective_ollama_base_url,
    }


@router.get("/health/db")
async def health_db():
    result = await check_database()
    code = status.HTTP_200_OK if result["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=result, status_code=code)


@router.get("/health/redis")
async def health_redis():
    result = await check_redis()
    code = status.HTTP_200_OK if result["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=result, status_code=code)


@router.get("/health/ollama")
async def health_ollama():
    result = await check_ollama()
    code = status.HTTP_200_OK if result["status"] in ("healthy", "degraded", "disabled") else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=result, status_code=code)


@router.get("/health/celery")
async def health_celery():
    result = check_celery()
    code = status.HTTP_200_OK if result["status"] in ("healthy", "degraded") else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=result, status_code=code)


@router.get("/health/full")
async def health_full():
    result = await check_full()
    code = status.HTTP_200_OK if result["status"] in ("healthy", "degraded") else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=result, status_code=code)
