"""CryptoGhost v4 - Celery tasks de investimento."""

import asyncio

from backend.investment.pipeline import InvestmentPipeline
from backend.market_ai_analyst.analyst import MarketAIAnalyst
from backend.shared.celery_app import celery_app
from backend.shared.config import get_settings
from backend.shared.database import AsyncSessionLocal
from backend.shared.logging_config import get_logger
from backend.intelligence.orchestrator import IntelligenceOrchestrator

logger = get_logger("cryptoghost.investment.tasks")


@celery_app.task(name="backend.investment.tasks.run_investment_ranking")
def run_investment_ranking() -> dict:
    """Rankeia universo de investimentos e persiste alocação."""
    settings = get_settings()
    orchestrator = IntelligenceOrchestrator()
    pipeline = InvestmentPipeline()
    analyst = MarketAIAnalyst()

    async def _run():
        async with AsyncSessionLocal() as session:
            contexts = []
            for symbol in settings.investment_universe_list:
                try:
                    v2 = await orchestrator.analyze_symbol(session, symbol)
                    df = await asyncio.to_thread(analyst.fetch_ohlcv_dataframe, symbol)
                    ctx = pipeline.build_context(symbol, df, v2, v2.get("quant_v3"))
                    ctx.liquidity_score = min(1.0, float(v2.get("analysis", {}).get("indicators", {}).get("volume_ratio", 1)) / 3)
                    contexts.append(ctx)
                except Exception as exc:
                    logger.error("investment_symbol_failed", symbol=symbol, error=str(exc))
            if not contexts:
                return {"status": "error", "message": "no symbols analyzed"}
            result = await pipeline.rank_universe(session, contexts)
            await session.commit()
            return result

    result = asyncio.run(_run())
    best = result.get("best_opportunity")
    return {
        "status": "ok",
        "best": best.get("symbol") if best else None,
        "total": result.get("total_analyzed", 0),
    }
