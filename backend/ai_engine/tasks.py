"""CryptoGhost - Celery tasks de IA."""

from decimal import Decimal

import pandas as pd

from backend.ai_engine.engine import HybridAISignalGenerator
from backend.shared.celery_app import celery_app
from backend.shared.database import SyncSessionLocal
from backend.shared.logging_config import get_logger
from backend.shared.models import AIPrediction, MarketData

logger = get_logger("cryptoghost.ai_engine.tasks")
_signal_generator = HybridAISignalGenerator()


@celery_app.task(name="backend.ai_engine.tasks.generate_predictions")
def generate_predictions() -> dict:
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    predictions_saved = 0

    with SyncSessionLocal() as session:
        for symbol in symbols:
            records = (
                session.query(MarketData)
                .filter(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp.desc())
                .limit(200)
                .all()
            )

            if len(records) < 20:
                continue

            df = pd.DataFrame(
                [
                    {
                        "open": float(r.open),
                        "high": float(r.high),
                        "low": float(r.low),
                        "close": float(r.close),
                        "volume": float(r.volume),
                    }
                    for r in reversed(records)
                ]
            )

            result = _signal_generator.generate_signal(symbol, df, records[0].indicators or {})
            session.add(
                AIPrediction(
                    model_name=result.model_name,
                    symbol=symbol,
                    signal=result.signal,
                    confidence=result.confidence,
                    predicted_price=Decimal(str(result.predicted_price)) if result.predicted_price else None,
                    features=result.features,
                    metrics=result.metrics,
                    explanation=result.explanation,
                )
            )
            predictions_saved += 1

        session.commit()

    return {"status": "ok", "predictions_saved": predictions_saved}
