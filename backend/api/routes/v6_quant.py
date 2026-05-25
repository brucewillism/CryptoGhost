"""CryptoGhost v6 — API Quant Platform."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.consensus_v3.engine import ConsensusEngineV3
from backend.app.ai.meta_learning.service import AgentPerformanceService
from backend.app.ai.regime.policies import get_policy
from backend.app.ai.regime.service import RegimeDetectionService
from backend.app.core.types import MarketRegimeV6
from backend.app.auto_invest.service_v2 import AutoInvestV2Service
from backend.app.backtesting.engine import BacktestEngineV6
from backend.app.learning.ai_memory_dashboard import get_ai_memory_dashboard
from backend.app.learning.trade_memory.service import TradeMemoryService
from backend.app.risk.engine_v2 import RiskEngineV2
from backend.app.self_improving_v6.pipeline import SelfImprovingPipelineV6
from backend.app.features.service import FeatureStoreService
from backend.shared.database import get_async_session
from backend.shared.config import get_settings
from backend.shared.models_v6 import AgentPerformanceRecord, BacktestRunRecord, MarketSignalV6Record, RegimeHistoryV6Record, TradeMemoryRecord
from backend.shared.security import get_current_user

router = APIRouter(prefix="/v6", tags=["Quant Platform v6"])


@router.get("/consensus/{symbol}")
async def get_consensus_v3(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(MarketSignalV6Record)
        .where(MarketSignalV6Record.symbol == symbol)
        .order_by(MarketSignalV6Record.created_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return {"symbol": symbol, "status": "no_data"}
    return {
        "symbol": row.symbol,
        "final_score": row.final_score,
        "classification": row.classification,
        "final_decision": row.final_decision,
        "consensus": row.consensus,
        "calibrated_confidence": row.calibrated_confidence,
        "agreement": row.agreement,
        "can_execute": row.can_execute,
        "rejection_reasons": row.rejection_reasons,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
    }


@router.get("/regime/{symbol}")
async def get_regime_v6(
    symbol: str,
    refresh: bool = Query(False, description="Força nova detecção"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    from datetime import UTC, datetime, timedelta

    if not refresh:
        result = await session.execute(
            select(RegimeHistoryV6Record)
            .where(RegimeHistoryV6Record.symbol == symbol)
            .order_by(RegimeHistoryV6Record.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            created = row.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            if datetime.now(UTC) - created < timedelta(minutes=15):
                try:
                    regime_enum = MarketRegimeV6(row.regime)
                except ValueError:
                    regime_enum = MarketRegimeV6.RANGING
                policy = get_policy(regime_enum)
                return {
                    "symbol": symbol,
                    "regime": row.regime,
                    "confidence": row.confidence,
                    "cached": True,
                    "policy": {
                        "exposure_multiplier": policy.exposure_multiplier,
                        "min_final_score": policy.min_final_score,
                        "description": policy.description,
                    },
                }

    svc = RegimeDetectionService()
    regime, policy, confidence = await svc.detect_and_persist(session, symbol)
    await session.commit()
    return {
        "symbol": symbol,
        "regime": regime.value,
        "confidence": confidence,
        "cached": False,
        "policy": {
            "exposure_multiplier": policy.exposure_multiplier,
            "min_final_score": policy.min_final_score,
            "description": policy.description,
        },
    }


@router.get("/agent-performance")
async def get_agent_performance(
    symbol: str = Query("BTC/USDT"),
    regime: str = Query("RANGING"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    svc = AgentPerformanceService()
    weights = await svc.compute_weights(session, symbol, regime)
    result = await session.execute(
        select(AgentPerformanceRecord).where(AgentPerformanceRecord.symbol.in_([symbol, "*"]))
    )
    rows = result.scalars().all()
    return {
        "weights": weights,
        "records": [
            {"agent": r.agent_name, "accuracy": r.accuracy, "weight": r.dynamic_weight, "regime": r.regime}
            for r in rows
        ],
    }


@router.get("/signals/fresh")
async def get_fresh_signals(
    symbol: str | None = Query(None),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    from backend.app.auto_invest.signal_freshness import SignalFreshnessValidator

    validator = SignalFreshnessValidator()
    symbols = [symbol] if symbol else get_settings().investment_universe_list
    fresh = []
    for sym in symbols:
        try:
            row = await validator.get_fresh_signal(session, sym)
            if row:
                fresh.append({
                    "symbol": row.symbol,
                    "final_score": row.final_score,
                    "classification": row.classification,
                    "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                })
        except Exception:
            continue
    return {"signals": fresh, "count": len(fresh)}


@router.get("/backtest/{run_id}")
async def get_backtest_run(
    run_id: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    import uuid

    result = await session.execute(
        select(BacktestRunRecord).where(BacktestRunRecord.id == uuid.UUID(run_id))
    )
    run = result.scalar_one_or_none()
    if not run:
        return {"status": "not_found", "id": run_id}
    return {
        "id": str(run.id),
        "name": run.name,
        "symbols": run.symbols,
        "metrics": run.metrics,
        "status": run.status,
        "config": run.config,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@router.get("/trade-memory/similar")
async def get_similar_trades(
    asset: str = Query("BTC/USDT"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    svc = TradeMemoryService()
    features = await FeatureStoreService().get_or_compute(session, asset)
    similar = await svc.find_similar(session, asset, features)
    return {
        "asset": asset,
        "similar": [
            {
                "regime": t.regime,
                "setup": t.setup,
                "pnl": t.pnl,
                "result": t.result,
                "confidence": t.confidence,
            }
            for t in similar
        ],
    }


@router.get("/config")
async def get_v6_config(_user: dict = Depends(get_current_user)) -> dict:
    settings = get_settings()
    return {
        "v6_enabled": settings.v6_enabled,
        "consensus_v3_enabled": settings.consensus_v3_enabled,
        "auto_invest_v2_enabled": settings.auto_invest_v2_enabled,
        "risk_v2_enabled": settings.risk_v2_enabled,
        "auto_invest_interval_minutes": settings.auto_invest_interval_minutes,
        "signal_max_age_minutes": settings.signal_max_age_minutes,
        "min_final_score_buy": settings.min_final_score_buy,
    }


@router.post("/auto-invest/run")
async def run_auto_invest_v6(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    return await AutoInvestV2Service().run_autonomous_cycle(session)


@router.post("/backtest/run")
async def run_backtest_v6(
    symbols: list[str] | None = None,
    name: str = "api",
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    from backend.shared.config import get_settings
    settings = get_settings()
    syms = symbols or settings.investment_universe_list[:3]
    return await BacktestEngineV6().run(session, syms, name=name)


@router.get("/backtest/runs")
async def list_backtest_runs(
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(BacktestRunRecord).order_by(BacktestRunRecord.created_at.desc()).limit(limit)
    )
    runs = result.scalars().all()
    return {
        "runs": [
            {"id": str(r.id), "name": r.name, "symbols": r.symbols, "metrics": r.metrics, "status": r.status}
            for r in runs
        ]
    }


@router.get("/ai-memory/dashboard")
async def get_ai_memory_panel(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    """Painel Memória da IA — trades, validações, hit rate e última lição."""
    return await get_ai_memory_dashboard(session)


@router.get("/trade-memory")
async def get_trade_memory(
    asset: str = Query("BTC/USDT"),
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(TradeMemoryRecord)
        .where(TradeMemoryRecord.asset == asset)
        .order_by(TradeMemoryRecord.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return {
        "trades": [
            {
                "asset": r.asset, "regime": r.regime, "setup": r.setup,
                "pnl": r.pnl, "result": r.result, "confidence": r.confidence,
            }
            for r in rows
        ]
    }


@router.get("/risk/heat")
async def get_risk_heat(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    risk = RiskEngineV2()
    await risk.load_state(session)
    return risk.get_status()


@router.get("/learning/metrics")
async def get_learning_metrics_v6(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    return await SelfImprovingPipelineV6().run(session)


@router.get("/features/{symbol}")
async def get_features_v6(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    features = await FeatureStoreService().get_or_compute(session, symbol)
    return {"symbol": symbol, "features": features, "count": len(features)}


@router.post("/analyze/{symbol}")
async def analyze_symbol_v6(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    return await AutoInvestV2Service().run_full_analysis(session, symbol)
