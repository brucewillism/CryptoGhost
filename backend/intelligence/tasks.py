"""CryptoGhost - Celery tasks de inteligência."""

from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.shared.celery_app import celery_app
from backend.shared.config import get_settings
from backend.shared.database import SyncSessionLocal
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.intelligence.tasks")


@celery_app.task(name="backend.intelligence.tasks.run_intelligence_analysis")
def run_intelligence_analysis() -> dict:
    """Executa análise completa multi-agente para todos os símbolos."""
    settings = get_settings()
    orchestrator = IntelligenceOrchestrator()
    results = []

    import asyncio

    async def _run():
        from backend.shared.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            for symbol in settings.intelligence_symbols_list:
                try:
                    result = await orchestrator.analyze_symbol(session, symbol)
                    results.append({"symbol": symbol, "decision": result["consensus"]["final_decision"]})
                except Exception as exc:
                    logger.error("intelligence_failed", symbol=symbol, error=str(exc))
            await orchestrator.analyze_macro_and_news(session)
            await session.commit()

    asyncio.run(_run())
    return {"status": "ok", "analyzed": len(results), "results": results}


@celery_app.task(name="backend.intelligence.tasks.run_sentiment_analysis")
def run_sentiment_analysis() -> dict:
    from backend.sentiment_engine.analyzer import SentimentEngine
    from backend.shared.models_intelligence import SentimentHistory

    engine = SentimentEngine()
    result = engine.analyze()

    with SyncSessionLocal() as session:
        session.add(SentimentHistory(
            market_sentiment=result.market_sentiment, score=result.score,
            confidence=result.confidence, sources=result.sources,
            bullish_pct=result.bullish_pct, bearish_pct=result.bearish_pct,
            panic_detected=result.panic_detected, euphoria_detected=result.euphoria_detected,
        ))
        session.commit()

    return {"status": "ok", "sentiment": result.market_sentiment, "score": result.score}
