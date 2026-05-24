"""CryptoGhost - Celery tasks para coleta de dados."""

from backend.shared.celery_app import celery_app
from backend.shared.database import SyncSessionLocal
from backend.shared.logging_config import get_logger
from backend.shared.models import MarketData
from backend.data_collector.collector import MarketDataCollector

logger = get_logger("cryptoghost.data_collector.tasks")


@celery_app.task(name="backend.data_collector.tasks.collect_market_data")
def collect_market_data() -> dict:
    """Task periódica de coleta de dados de mercado."""
    collector = MarketDataCollector()
    snapshots = collector.collect_all()
    saved = 0

    with SyncSessionLocal() as session:
        for snap in snapshots:
            record = MarketData(
                exchange=snap["exchange"],
                symbol=snap["symbol"],
                timestamp=snap["timestamp"],
                open=snap["open"],
                high=snap["high"],
                low=snap["low"],
                close=snap["close"],
                volume=snap["volume"],
                bid=snap["bid"],
                ask=snap["ask"],
                indicators=snap["indicators"],
            )
            session.add(record)
            saved += 1
        session.commit()

    logger.info("market_data_task_complete", saved=saved)
    return {"status": "ok", "records_saved": saved}
