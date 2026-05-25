"""CryptoGhost v4 - API de Priorização de Investimentos."""

import asyncio
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.investment.advisor import build_investment_recommendation
from backend.investment.pipeline import InvestmentPipeline
from backend.market_ai_analyst.analyst import MarketAIAnalyst
from backend.shared.config import get_settings
from backend.shared.database import get_async_session
from backend.shared.models_investment import (
    AdaptiveAllocationRecord,
    InvestmentRankingRecord,
    OpportunityScoreRecord,
)
from backend.shared.security import get_current_user

router = APIRouter(prefix="/investment", tags=["Investment v4"])


@router.get("/recommendation")
async def investment_recommendation(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    """Melhor ativo para investir agora + proposta de ordem (requer aprovação)."""
    return await build_investment_recommendation(session)


@router.post("/auto-run")
async def autonomous_invest_cycle(
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(get_current_user),
) -> dict:
    """IA autônoma: recomenda, investe paper e aprende — sem aprovação manual."""
    from backend.investment.auto_invest import run_autonomous_cycle

    result = await run_autonomous_cycle(session, actor=user["username"])
    await session.commit()
    return result


@router.get("/best-opportunity")
async def best_opportunity(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    """Retorna a melhor oportunidade de investimento agora."""
    from backend.intelligence.orchestrator import IntelligenceOrchestrator

    settings = get_settings()
    orchestrator = IntelligenceOrchestrator()
    pipeline = InvestmentPipeline()
    analyst = MarketAIAnalyst()

    async def analyze_all():
        contexts = []
        v2_results = []
        for symbol in settings.investment_universe_list:
            try:
                v2 = await orchestrator.analyze_symbol(session, symbol)
                df = await asyncio.to_thread(analyst.fetch_ohlcv_dataframe, symbol)
                liq = float(v2.get("analysis", {}).get("indicators", {}).get("volume_ratio", 1)) / 3
                ctx = pipeline.build_context(symbol, df, v2, v2.get("quant_v3"))
                ctx.liquidity_score = min(1.0, max(0.1, liq))
                contexts.append(ctx)
                v2_results.append(v2)
            except Exception:
                continue
        if not contexts:
            return {"status": "no_data", "message": "Execute análises primeiro"}
        return await pipeline.rank_universe(session, contexts)

    result = await analyze_all()
    await session.commit()
    return result


@router.get("/ranking")
async def get_ranking(
    limit: int = Query(10, le=50),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(InvestmentRankingRecord).order_by(InvestmentRankingRecord.created_at.desc()).limit(limit)
    )
    records = result.scalars().all()
    return {
        "ranking": [
            {
                "symbol": r.symbol, "rank": r.rank_position, "priority_score": r.priority_score,
                "expected_return": r.expected_return_pct, "risk_score": r.risk_score,
                "confidence": r.confidence, "recommendation": r.recommendation, "reasons": r.reasons,
            }
            for r in records
        ],
    }


@router.get("/allocation")
async def get_allocation(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(AdaptiveAllocationRecord).order_by(AdaptiveAllocationRecord.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"status": "no_data"}
    return {
        "allocations": record.allocations,
        "total_exposure_pct": record.total_exposure_pct,
        "cash_pct": record.cash_pct,
        "regime": record.regime,
        "rationale": record.rationale,
    }


@router.get("/opportunity/{symbol}")
async def get_opportunity(
    symbol: str,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(OpportunityScoreRecord).where(OpportunityScoreRecord.symbol == symbol)
        .order_by(OpportunityScoreRecord.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"status": "no_data"}
    return {
        "opportunity_score": record.opportunity_score,
        "classification": record.classification,
        "components": record.components,
    }


@router.get("/dashboard")
async def investment_dashboard(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    """Agrega dados para dashboard de investimentos."""
    ranking_r = await session.execute(
        select(InvestmentRankingRecord).order_by(InvestmentRankingRecord.created_at.desc()).limit(10)
    )
    rankings = ranking_r.scalars().all()

    alloc_r = await session.execute(
        select(AdaptiveAllocationRecord).order_by(AdaptiveAllocationRecord.created_at.desc()).limit(1)
    )
    allocation = alloc_r.scalar_one_or_none()

    from backend.shared.models_investment import InstitutionalSignalRecord, ProbabilisticPredictionRecord

    signals_r = await session.execute(
        select(InstitutionalSignalRecord).order_by(InstitutionalSignalRecord.created_at.desc()).limit(10)
    )
    signals = signals_r.scalars().all()

    prob_r = await session.execute(
        select(ProbabilisticPredictionRecord).order_by(ProbabilisticPredictionRecord.created_at.desc()).limit(5)
    )
    probs = prob_r.scalars().all()

    best = rankings[0] if rankings else None

    return {
        "best_opportunity": {
            "symbol": best.symbol, "priority_score": best.priority_score,
            "expected_return": best.expected_return_pct, "recommendation": best.recommendation,
            "confidence": best.confidence, "reasons": best.reasons,
        } if best else None,
        "ranking": [
            {
                "symbol": r.symbol, "rank": r.rank_position, "score": r.priority_score,
                "expected_return": r.expected_return_pct, "risk": r.risk_score,
                "recommendation": r.recommendation,
            }
            for r in rankings
        ],
        "allocation": {
            "allocations": allocation.allocations, "cash_pct": allocation.cash_pct,
            "exposure_pct": allocation.total_exposure_pct, "regime": allocation.regime,
        } if allocation else None,
        "institutional_signals": [
            {"symbol": s.symbol, "type": s.signal_type, "strength": s.strength, "direction": s.direction}
            for s in signals
        ],
        "probabilities": [
            {
                "symbol": p.symbol, "bullish": p.bullish_probability,
                "bearish": p.bearish_probability, "uncertainty": p.uncertainty,
            }
            for p in probs
        ],
    }
