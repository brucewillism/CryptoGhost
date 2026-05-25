"""Métricas reais para dashboards — substitui placeholders mock."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai_consensus_engine.consensus import AGENT_WEIGHTS
from backend.shared.models_intelligence import AIConsensusRecord
from backend.shared.models_v5 import PredictionValidationRecord
from backend.shared.models_v6 import AgentPerformanceRecord, MarketSignalV6Record, TradeMemoryRecord


async def build_neural_activity(session: AsyncSession, symbol: str) -> list[dict]:
    """Atividade neural a partir de performance DB + votos do último consenso."""
    agents = list(AGENT_WEIGHTS.keys())
    perf_r = await session.execute(
        select(AgentPerformanceRecord).where(AgentPerformanceRecord.symbol.in_([symbol, "*"]))
    )
    perf_rows = {r.agent_name: r for r in perf_r.scalars().all()}

    consensus_r = await session.execute(
        select(AIConsensusRecord)
        .where(AIConsensusRecord.symbol == symbol)
        .order_by(AIConsensusRecord.created_at.desc())
        .limit(1)
    )
    consensus = consensus_r.scalar_one_or_none()
    vote_map: dict[str, float] = {}
    if consensus and consensus.agent_votes:
        for v in consensus.agent_votes:
            if isinstance(v, dict):
                vote_map[v.get("agent", "")] = float(v.get("confidence", 0.5))

    val_r = await session.execute(
        select(PredictionValidationRecord)
        .where(PredictionValidationRecord.symbol == symbol)
        .order_by(PredictionValidationRecord.created_at.desc())
        .limit(50)
    )
    validations = val_r.scalars().all()
    global_hit = (
        sum(1 for v in validations if v.direction_correct) / len(validations)
        if validations else None
    )

    result = []
    for agent in agents:
        perf = perf_rows.get(agent)
        if perf:
            activity = round(perf.accuracy * 100, 1)
            status = "active" if perf.accuracy >= 0.55 else "degraded" if perf.accuracy >= 0.45 else "idle"
        elif agent in vote_map:
            activity = round(vote_map[agent] * 100, 1)
            status = "active" if vote_map[agent] >= 0.6 else "degraded"
        elif global_hit is not None:
            activity = round(global_hit * 100, 1)
            status = "active" if global_hit >= 0.55 else "degraded"
        else:
            activity = round(AGENT_WEIGHTS.get(agent, 0.2) * 100, 1)
            status = "idle"

        result.append({"agent": agent, "activity": activity, "status": status})

    return result


async def build_ensemble_fallback(session: AsyncSession, symbol: str) -> dict | None:
    ens_r = await session.execute(
        select(MarketSignalV6Record)
        .where(MarketSignalV6Record.symbol == symbol)
        .order_by(MarketSignalV6Record.created_at.desc())
        .limit(1)
    )
    v6 = ens_r.scalar_one_or_none()
    if v6:
        weights = {}
        for v in v6.agent_votes or []:
            if isinstance(v, dict):
                weights[v.get("agent", "?")] = float(v.get("weight", 0.2))
        return {
            "final_decision": v6.final_decision,
            "meta_confidence": v6.calibrated_confidence,
            "stacking_weights": weights or dict(AGENT_WEIGHTS),
            "agent_predictions": {},
            "method": "consensus_v6",
        }

    con_r = await session.execute(
        select(AIConsensusRecord)
        .where(AIConsensusRecord.symbol == symbol)
        .order_by(AIConsensusRecord.created_at.desc())
        .limit(1)
    )
    con = con_r.scalar_one_or_none()
    if not con:
        return None

    weights = {}
    for v in con.agent_votes or []:
        if isinstance(v, dict):
            weights[v.get("agent", "?")] = float(v.get("weight", AGENT_WEIGHTS.get(v.get("agent", ""), 0.2)))

    return {
        "final_decision": con.final_decision,
        "meta_confidence": con.confidence,
        "stacking_weights": weights or dict(AGENT_WEIGHTS),
        "agent_predictions": {},
        "method": "consensus_v2",
    }


async def build_calibration_fallback(session: AsyncSession, symbol: str) -> dict | None:
    sig_r = await session.execute(
        select(MarketSignalV6Record)
        .where(MarketSignalV6Record.symbol == symbol)
        .order_by(MarketSignalV6Record.created_at.desc())
        .limit(1)
    )
    sig = sig_r.scalar_one_or_none()
    if sig:
        return {
            "raw_confidence": sig.consensus,
            "calibrated_confidence": sig.calibrated_confidence,
            "uncertainty": max(0, 1 - sig.calibrated_confidence),
            "reliability_score": sig.calibrated_confidence,
        }
    return None


async def build_similarity_from_trades(session: AsyncSession, symbol: str, limit: int = 5) -> list[dict]:
    r = await session.execute(
        select(TradeMemoryRecord)
        .where(TradeMemoryRecord.asset == symbol)
        .order_by(TradeMemoryRecord.created_at.desc())
        .limit(limit)
    )
    rows = r.scalars().all()
    return [
        {
            "label": t.setup,
            "outcome": t.result,
            "state": {"regime": t.regime, "pnl": t.pnl, "confidence": t.confidence},
        }
        for t in rows
    ]


async def build_temporal_from_trades(session: AsyncSession, symbol: str, limit: int = 15) -> list[dict]:
    r = await session.execute(
        select(TradeMemoryRecord)
        .where(TradeMemoryRecord.asset == symbol)
        .order_by(TradeMemoryRecord.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "agent": "auto_invest",
            "type": "trade",
            "decision": t.setup,
            "context": {"regime": t.regime, "result": t.result},
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in r.scalars().all()
    ]
