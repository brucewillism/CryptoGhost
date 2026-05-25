"""Celery workers v6 — filas dedicadas."""

import asyncio

from backend.shared.celery_app import celery_app
from backend.shared.database import AsyncSessionLocal
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.v6.workers")


@celery_app.task(name="backend.app.workers.run_market_scan", queue="market_scan")
def run_market_scan() -> dict:
    from backend.app.auto_invest.service_v2 import AutoInvestV2Service

    async def _run():
        service = AutoInvestV2Service()
        async with AsyncSessionLocal() as session:
            results = []
            for sym in service.settings.investment_universe_list:
                try:
                    await service.run_full_analysis(session, sym)
                    results.append(sym)
                except Exception as exc:
                    logger.warning("scan_failed", symbol=sym, error=str(exc))
            await session.commit()
            return {"scanned": results}

    return asyncio.run(_run())


@celery_app.task(name="backend.app.workers.run_auto_invest_v2", queue="analysis")
def run_auto_invest_v2() -> dict:
    from backend.app.auto_invest.service_v2 import AutoInvestV2Service

    async def _run():
        service = AutoInvestV2Service()
        async with AsyncSessionLocal() as session:
            result = await service.run_autonomous_cycle(session)
            await session.commit()
            return result

    return asyncio.run(_run())


@celery_app.task(name="backend.app.workers.run_backtest", queue="backtesting")
def run_backtest(symbols: list[str] | None = None, name: str = "celery") -> dict:
    from backend.app.backtesting.engine import BacktestEngineV6
    from backend.shared.config import get_settings

    settings = get_settings()
    syms = symbols or settings.investment_universe_list[:3]

    async def _run():
        engine = BacktestEngineV6()
        async with AsyncSessionLocal() as session:
            result = await engine.run(session, syms, name=name)
            await session.commit()
            return result

    return asyncio.run(_run())


@celery_app.task(name="backend.app.workers.run_self_improving_v6", queue="retraining")
def run_self_improving_v6() -> dict:
    from backend.app.self_improving_v6.pipeline import SelfImprovingPipelineV6

    async def _run():
        pipeline = SelfImprovingPipelineV6()
        async with AsyncSessionLocal() as session:
            result = await pipeline.run(session)
            await session.commit()
            return result

    return asyncio.run(_run())
