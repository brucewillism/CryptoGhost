"""Snapshot compacto para WebSocket / polling em tempo real."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.gpu_inference.engine import get_gpu_engine
from backend.paper_trial.service import _portfolio_metrics
from backend.shared.models import Order, Position
from backend.shared.models_intelligence import AIConsensusRecord, SentimentHistory
from backend.shared.models_v6 import MarketSignalV6Record


async def build_live_snapshot(session: AsyncSession) -> dict:
    open_positions = await session.scalar(
        select(func.count()).select_from(Position).where(Position.is_open == True)  # noqa: E712
    )
    portfolio = await _portfolio_metrics(session)
    gpu = get_gpu_engine().get_status()

    consensus_r = await session.execute(
        select(AIConsensusRecord).order_by(AIConsensusRecord.created_at.desc()).limit(1)
    )
    consensus = consensus_r.scalar_one_or_none()

    v6_r = await session.execute(
        select(MarketSignalV6Record).order_by(MarketSignalV6Record.created_at.desc()).limit(1)
    )
    v6 = v6_r.scalar_one_or_none()

    sent_r = await session.execute(
        select(SentimentHistory).order_by(SentimentHistory.created_at.desc()).limit(1)
    )
    sentiment = sent_r.scalar_one_or_none()

    recent_orders = await session.execute(
        select(Order).order_by(Order.created_at.desc()).limit(5)
    )

    return {
        "open_positions": open_positions or 0,
        "paper_portfolio_value": portfolio["current_value_usdt"],
        "paper_return_pct": portfolio["return_pct"],
        "total_pnl": portfolio.get("total_pnl_usdt", 0),
        "gpu_available": gpu.available,
        "gpu_device": gpu.device_name,
        "consensus": {
            "final_decision": consensus.final_decision if consensus else "hold",
            "confidence": consensus.confidence if consensus else 0,
        } if consensus else None,
        "consensus_v6": {
            "final_score": v6.final_score,
            "classification": v6.classification,
            "can_execute": v6.can_execute,
        } if v6 else None,
        "sentiment": {
            "score": sentiment.score,
            "market_sentiment": sentiment.market_sentiment,
        } if sentiment else None,
        "recent_orders": [
            {"symbol": o.symbol, "status": o.status, "side": o.side}
            for o in recent_orders.scalars().all()
        ],
    }
