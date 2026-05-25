"""CryptoGhost - API Principal FastAPI."""

from contextlib import asynccontextmanager

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None  # type: ignore

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from backend.api.routes import ai, auth, dashboard, health, intelligence, investment, quant, risk, trading, trial, v5, v6_quant
from backend.api.websocket import router as ws_router, start_realtime_broadcasts, stop_realtime_broadcasts
from backend.shared.config import get_settings
from backend.shared.database import Base, async_engine
from backend.shared import models, models_intelligence, models_quant, models_investment, models_v5, models_v6  # noqa: F401
from backend.shared.logging_config import configure_logging, get_logger
from backend.shared.startup_log import api as api_log, celery_log, database as db_log, ollama as ollama_log, redis_log, startup
from backend.shared.health_service import check_database, check_ollama, check_redis

configure_logging()
logger = get_logger("cryptoghost.api")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup("Iniciando CryptoGhost v5.0.0", env=settings.env)

    if settings.sentry_dsn and sentry_sdk:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    if settings.env != "test":
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            db_log("Schema sincronizado")
        except Exception as exc:
            db_log(
                "PostgreSQL indisponível — API sobe em modo degradado",
                error=str(exc),
            )
            if settings.env == "production":
                raise

    db_status = await check_database()
    db_log("PostgreSQL", status=db_status.get("status"), pgvector=db_status.get("pgvector"))

    redis_status = await check_redis()
    redis_log("Redis", status=redis_status.get("status"))

    ollama_status = await check_ollama()
    ollama_log(
        "Ollama remoto",
        status=ollama_status.get("status"),
        url=settings.effective_ollama_base_url,
        model=settings.effective_ollama_model,
    )

    api_log(
        "API pronta",
        paper_trading=settings.paper_trading,
        live_allowed=settings.is_live_trading_allowed,
        ollama=settings.effective_ollama_base_url,
    )
    celery_log("Broker configurado", url=settings.celery_broker_url)

    logger.info(
        "cryptoghost_started",
        env=settings.env,
        paper_trading=settings.paper_trading,
        live_allowed=settings.is_live_trading_allowed,
    )
    if settings.env != "test":
        start_realtime_broadcasts()
    yield
    await stop_realtime_broadcasts()
    logger.info("cryptoghost_shutdown")


app = FastAPI(
    title="CryptoGhost API",
    description="Plataforma de Inteligência Financeira com IA Explicável - Uso Pessoal/Familiar",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(trading.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(intelligence.router, prefix="/api/v1")
app.include_router(quant.router, prefix="/api/v1")
app.include_router(investment.router, prefix="/api/v1")
app.include_router(trial.router, prefix="/api/v1")
app.include_router(v5.router, prefix="/api/v1")
app.include_router(v6_quant.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(ws_router)

if settings.prometheus_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/")
async def root() -> dict:
    return {
        "message": "CryptoGhost API - Plataforma de Inteligência Financeira com IA Explicável",
        "docs": "/docs",
        "health": "/health",
        "compliance": "Uso exclusivo em contas próprias com APIs oficiais",
    }
