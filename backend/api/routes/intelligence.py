"""CryptoGhost - API de Inteligência Financeira."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.intelligence.orchestrator import IntelligenceOrchestrator
from backend.shared.config import get_settings
from backend.shared.database import get_async_session
from backend.shared.models_intelligence import (
    AIConsensusRecord,
    AIExplanation,
    AssetAnalysisRecord,
    MacroIndicatorRecord,
    MarketRegimeRecord,
    NewsAnalysisRecord,
    SentimentHistory,
)
from backend.shared.security import get_current_user

router = APIRouter(prefix="/intelligence", tags=["Inteligência Financeira"])


@router.post("/analyze")
async def analyze_symbol(
    symbol: str = Query(..., description="Par de trading, ex: BTC/USDT"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    """Executa análise completa multi-agente com IA explicável."""
    orchestrator = IntelligenceOrchestrator()
    return await orchestrator.analyze_symbol(session, symbol)


@router.get("/analysis")
async def get_latest_analysis(
    symbol: str = Query(..., description="Par de trading, ex: BTC/USDT"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(AssetAnalysisRecord).where(AssetAnalysisRecord.symbol == symbol)
        .order_by(AssetAnalysisRecord.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"symbol": symbol, "status": "no_data"}
    return {
        "symbol": record.symbol, "score": record.score, "trend": record.trend,
        "risk": record.risk, "confidence": record.confidence,
        "recommendation": record.recommendation, "indicators": record.indicators,
    }


@router.get("/consensus")
async def get_consensus(
    symbol: str = Query(..., description="Par de trading, ex: BTC/USDT"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(AIConsensusRecord).where(AIConsensusRecord.symbol == symbol)
        .order_by(AIConsensusRecord.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"symbol": symbol, "status": "no_data"}
    return {
        "final_decision": record.final_decision, "confidence": record.confidence,
        "agreement": record.agreement, "disagreement": record.disagreement,
        "agent_votes": record.agent_votes, "conflicts": record.conflicts,
    }


@router.get("/explanation")
async def get_explanation(
    symbol: str = Query(..., description="Par de trading, ex: BTC/USDT"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(AIExplanation).where(AIExplanation.symbol == symbol)
        .order_by(AIExplanation.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"symbol": symbol, "status": "no_data"}
    return {
        "decision": record.decision, "confidence": record.confidence,
        "reasons": record.reasons, "feature_importance": record.feature_importance,
        "shap_values": record.shap_values, "decision_trace": record.decision_trace,
        "textual_explanation": record.textual_explanation,
    }


@router.get("/sentiment")
async def get_sentiment(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(SentimentHistory).order_by(SentimentHistory.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        orchestrator = IntelligenceOrchestrator()
        import asyncio
        sentiment = await asyncio.to_thread(orchestrator.sentiment.analyze)
        return {"market_sentiment": sentiment.market_sentiment, "score": sentiment.score, "confidence": sentiment.confidence}
    return {
        "market_sentiment": record.market_sentiment, "score": record.score,
        "confidence": record.confidence, "bullish_pct": record.bullish_pct,
        "bearish_pct": record.bearish_pct, "panic_detected": record.panic_detected,
    }


@router.get("/regime")
async def get_regime(
    symbol: str = Query(..., description="Par de trading, ex: BTC/USDT"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(MarketRegimeRecord).where(MarketRegimeRecord.symbol == symbol)
        .order_by(MarketRegimeRecord.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"symbol": symbol, "status": "no_data"}
    return {
        "regime": record.regime, "confidence": record.confidence,
        "volatility": record.volatility, "strategy_adjustment": record.strategy_adjustment,
    }


@router.get("/heatmap")
async def get_heatmap(
    refresh: bool = Query(False, description="Força recálculo ao vivo"),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    settings = get_settings()
    symbols = settings.intelligence_symbols_list
    max_age = timedelta(minutes=30)
    now = datetime.now(UTC)
    cached_assets: list[dict] = []
    stale_symbols: list[str] = []

    for symbol in symbols:
        result = await session.execute(
            select(AssetAnalysisRecord)
            .where(AssetAnalysisRecord.symbol == symbol)
            .order_by(AssetAnalysisRecord.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if record and not refresh:
            created = record.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            age = now - created
            momentum = 0.0
            if record.indicators and isinstance(record.indicators, dict):
                momentum = float(record.indicators.get("momentum", 0))
            if age <= max_age:
                cached_assets.append({
                    "symbol": symbol,
                    "score": record.score,
                    "trend": record.trend,
                    "change": momentum,
                })
                continue
        stale_symbols.append(symbol)

    if not stale_symbols and cached_assets:
        return {"assets": cached_assets, "cached": True}

    orchestrator = IntelligenceOrchestrator()
    live = await orchestrator.get_market_heatmap(stale_symbols or symbols)
    by_symbol = {a["symbol"]: a for a in cached_assets}
    for item in live:
        by_symbol[item["symbol"]] = item
    ordered = [by_symbol[s] for s in symbols if s in by_symbol]
    return {"assets": ordered, "cached": not bool(stale_symbols)}


@router.get("/macro")
async def get_macro(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(MacroIndicatorRecord).order_by(MacroIndicatorRecord.created_at.desc()).limit(10)
    )
    records = result.scalars().all()
    if not records:
        orchestrator = IntelligenceOrchestrator()
        import asyncio
        macro = await asyncio.to_thread(orchestrator.macro.analyze)
        return {"outlook": macro.market_outlook, "indicators": [{"name": i.name, "value": i.value, "impact": i.impact} for i in macro.indicators]}
    return {"indicators": [{"name": r.indicator_name, "value": r.value, "change_pct": r.change_pct, "impact": r.impact} for r in records]}


@router.get("/news")
async def get_news_analysis(
    limit: int = Query(10, le=50),
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    result = await session.execute(
        select(NewsAnalysisRecord).order_by(NewsAnalysisRecord.created_at.desc()).limit(limit)
    )
    records = result.scalars().all()
    return {"news": [{"title": r.title, "source": r.source, "impact": r.impact, "direction": r.direction, "confidence": r.confidence} for r in records]}


@router.post("/macro-news/analyze")
async def run_macro_news(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    orchestrator = IntelligenceOrchestrator()
    return await orchestrator.analyze_macro_and_news(session)
