"""Celery tasks self-improving v5."""

import asyncio

from backend.self_improving.pipeline import SelfImprovingPipeline
from backend.investment.pipeline import InvestmentPipeline
from backend.market_ai_analyst.analyst import MarketAIAnalyst
from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.shared.celery_app import celery_app
from backend.shared.config import get_settings
from backend.shared.database import AsyncSessionLocal
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.self_improving.tasks")


@celery_app.task(name="backend.self_improving.tasks.run_self_improvement_cycle")
def run_self_improvement_cycle() -> dict:
    """Ciclo completo de auto-melhoria para universo de símbolos."""
    settings = get_settings()
    orchestrator = IntelligenceOrchestrator()
    inv = InvestmentPipeline()
    si = SelfImprovingPipeline()
    analyst = MarketAIAnalyst()
    improved = 0

    async def _run():
        nonlocal improved
        async with AsyncSessionLocal() as session:
            for symbol in settings.investment_universe_list[:3]:
                try:
                    v2 = await orchestrator.analyze_symbol(session, symbol)
                    df = await asyncio.to_thread(analyst.fetch_ohlcv_dataframe, symbol)
                    si_ctx = si.build_context(symbol, df, v2, v2.get("quant_v3"), v2.get("investment_v4"))
                    await si.enhance(session, si_ctx)
                    improved += 1
                except Exception as exc:
                    logger.error("self_improvement_failed", symbol=symbol, error=str(exc))
            await session.commit()

    asyncio.run(_run())
    return {"status": "ok", "improved": improved}
