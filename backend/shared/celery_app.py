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
        "backend.app.workers.tasks",
    ],
)

celery_app.conf.task_routes = {
    "backend.app.workers.run_market_scan": {"queue": "market_scan"},
    "backend.app.workers.run_auto_invest_v2": {"queue": "analysis"},
    "backend.app.workers.run_backtest": {"queue": "backtesting"},
    "backend.app.workers.run_self_improving_v6": {"queue": "retraining"},
    "backend.intelligence.tasks.*": {"queue": "analysis"},
}

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
        "v6-market-scan": {
            "task": "backend.app.workers.run_market_scan",
            "schedule": 300.0,
            "options": {"queue": "market_scan"},
        },
        "v6-auto-invest": {
            "task": "backend.app.workers.run_auto_invest_v2",
            "schedule": float(settings.auto_invest_interval_minutes * 60),
            "options": {"queue": "analysis"},
        },
        "v6-self-improving": {
            "task": "backend.app.workers.run_self_improving_v6",
            "schedule": 900.0,
            "options": {"queue": "retraining"},
        },
    },
)
