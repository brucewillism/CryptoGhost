"""CryptoGhost - Celery application."""

from celery import Celery

from backend.shared.config import get_settings

settings = get_settings()

celery_app = Celery(
    "cryptoghost",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.data_collector.tasks",
        "backend.ai_engine.tasks",
        "backend.notifications.tasks",
        "backend.risk_management.tasks",
        "backend.intelligence.tasks",
        "backend.quant.tasks",
        "backend.investment.tasks",
        "backend.self_improving.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "collect-market-data": {
            "task": "backend.data_collector.tasks.collect_market_data",
            "schedule": 60.0,
        },
        "run-ai-predictions": {
            "task": "backend.ai_engine.tasks.generate_predictions",
            "schedule": 300.0,
        },
        "risk-monitor": {
            "task": "backend.risk_management.tasks.monitor_risk",
            "schedule": 30.0,
        },
        "intelligence-analysis": {
            "task": "backend.intelligence.tasks.run_intelligence_analysis",
            "schedule": float(settings.intelligence_analysis_interval),
        },
        "sentiment-analysis": {
            "task": "backend.intelligence.tasks.run_sentiment_analysis",
            "schedule": 180.0,
        },
        "quant-drift-detection": {
            "task": "backend.quant.tasks.run_drift_detection",
            "schedule": 600.0,
        },
        "investment-ranking": {
            "task": "backend.investment.tasks.run_investment_ranking",
            "schedule": 300.0,
        },
        "self-improvement-cycle": {
            "task": "backend.self_improving.tasks.run_self_improvement_cycle",
            "schedule": 600.0,
        },
    },
)
