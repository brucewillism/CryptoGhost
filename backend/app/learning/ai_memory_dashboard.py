"""Agregador de métricas de memória/aprendizado para o dashboard."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.models_intelligence import AIMemoryRecord
from backend.shared.models_v5 import PredictionValidationRecord
from backend.shared.models_v6 import AgentPerformanceRecord, TradeMemoryRecord


async def get_ai_memory_dashboard(session: AsyncSession, recent_limit: int = 8) -> dict:
    trade_total_r = await session.execute(select(func.count()).select_from(TradeMemoryRecord))
    trade_total = trade_total_r.scalar() or 0

    trade_open_r = await session.execute(
        select(func.count()).select_from(TradeMemoryRecord).where(TradeMemoryRecord.result == "open")
    )
    trade_open = trade_open_r.scalar() or 0

    closed_r = await session.execute(
        select(TradeMemoryRecord).where(TradeMemoryRecord.result.in_(["profit", "loss"]))
    )
    closed_trades = closed_r.scalars().all()
    trade_wins = sum(1 for t in closed_trades if t.result == "profit")
    trade_hit_rate = round(trade_wins / max(len(closed_trades), 1), 3) if closed_trades else None

    val_r = await session.execute(
        select(PredictionValidationRecord)
        .order_by(PredictionValidationRecord.created_at.desc())
        .limit(100)
    )
    validations = val_r.scalars().all()
    val_correct = sum(1 for v in validations if v.direction_correct)
    validation_hit_rate = round(val_correct / max(len(validations), 1), 3) if validations else None

    mem_eval_r = await session.execute(
        select(AIMemoryRecord).where(AIMemoryRecord.was_correct.isnot(None)).limit(500)
    )
    memory_evaluated = mem_eval_r.scalars().all()
    mem_correct = sum(1 for m in memory_evaluated if m.was_correct)
    memory_hit_rate = (
        round(mem_correct / max(len(memory_evaluated), 1), 3) if memory_evaluated else None
    )

    lesson_r = await session.execute(
        select(AIMemoryRecord)
        .where(AIMemoryRecord.lesson.isnot(None))
        .order_by(AIMemoryRecord.created_at.desc())
        .limit(1)
    )
    last_lesson_row = lesson_r.scalar_one_or_none()

    pending_r = await session.execute(
        select(func.count())
        .select_from(AIMemoryRecord)
        .where(AIMemoryRecord.was_correct.is_(None))
    )
    memory_pending = pending_r.scalar() or 0

    recent_trades_r = await session.execute(
        select(TradeMemoryRecord)
        .order_by(TradeMemoryRecord.created_at.desc())
        .limit(recent_limit)
    )
    recent_trades = recent_trades_r.scalars().all()

    recent_val_r = await session.execute(
        select(PredictionValidationRecord)
        .order_by(PredictionValidationRecord.created_at.desc())
        .limit(5)
    )
    recent_validations = recent_val_r.scalars().all()

    agent_r = await session.execute(
        select(AgentPerformanceRecord).order_by(AgentPerformanceRecord.updated_at.desc()).limit(12)
    )
    agents = agent_r.scalars().all()

    overall_hits = []
    if validation_hit_rate is not None:
        overall_hits.append(validation_hit_rate)
    if memory_hit_rate is not None:
        overall_hits.append(memory_hit_rate)
    if trade_hit_rate is not None:
        overall_hits.append(trade_hit_rate)
    overall_hit_rate = round(sum(overall_hits) / len(overall_hits), 3) if overall_hits else None

    return {
        "summary": {
            "trades_memorized": trade_total,
            "trades_open": trade_open,
            "trades_closed": len(closed_trades),
            "trade_hit_rate": trade_hit_rate,
            "validations_total": len(validations),
            "validation_hit_rate": validation_hit_rate,
            "memory_evaluated": len(memory_evaluated),
            "memory_pending": memory_pending,
            "memory_hit_rate": memory_hit_rate,
            "overall_hit_rate": overall_hit_rate,
            "agents_tracked": len(agents),
        },
        "last_lesson": (
            {
                "symbol": last_lesson_row.symbol,
                "decision": last_lesson_row.decision,
                "outcome": last_lesson_row.outcome,
                "performance_pct": last_lesson_row.performance_pct,
                "was_correct": last_lesson_row.was_correct,
                "lesson": last_lesson_row.lesson,
                "created_at": last_lesson_row.created_at.isoformat() if last_lesson_row.created_at else None,
            }
            if last_lesson_row
            else None
        ),
        "recent_trades": [
            {
                "asset": t.asset,
                "regime": t.regime,
                "setup": t.setup,
                "result": t.result,
                "pnl": t.pnl,
                "confidence": t.confidence,
                "final_score": (t.market_conditions or {}).get("final_score"),
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in recent_trades
        ],
        "recent_validations": [
            {
                "symbol": v.symbol,
                "predicted_return_pct": v.predicted_return_pct,
                "actual_return_pct": v.actual_return_pct,
                "direction_correct": v.direction_correct,
                "validation_score": v.validation_score,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in recent_validations
        ],
        "agent_weights": [
            {
                "agent": a.agent_name,
                "regime": a.regime,
                "accuracy": round(a.accuracy, 3),
                "dynamic_weight": round(a.dynamic_weight, 3),
                "sample_count": a.sample_count,
            }
            for a in agents
        ],
        "learning_in_decisions": {
            "agent_performance_weights": True,
            "prediction_validations": len(validations) > 0,
            "regime_policy": True,
            "risk_engine_v2": True,
            "calibrated_confidence": True,
            "trade_memory_recall": False,
            "ai_memory_recall": False,
            "note": (
                "Pesos dos agentes, calibração e validações entram no consenso v3 a cada investimento. "
                "Recall de trades/lições similares ainda não bloqueia ordens — só grava e valida."
            ),
        },
    }
