"""CryptoGhost - Período de teste paper (30 dias) com aprendizado contínuo."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.audit_logs.service import AuditService
from backend.data_collector.collector import ExchangeConnector
from backend.prediction_validation.engine import PredictionValidationEngine
from backend.real_performance_tracker.engine import RealPerformanceTracker
from backend.self_improvement_engine.engine import SelfImprovementEngine
from backend.shared.config import get_settings
from backend.shared.models import AuditEventType, Order, Position
from backend.shared.models_intelligence import AIConsensusRecord, AIMemoryRecord
from backend.shared.models_investment import ExpectedReturnRecord
from backend.shared.models_v5 import PredictionValidationRecord, RealPerformanceRecord

TRIAL_ACTION = "paper_trial_started"
LEARN_ACTION = "paper_trial_learning"


async def _trial_start_date(session: AsyncSession) -> datetime | None:
    from backend.shared.models import AuditLog

    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.action == TRIAL_ACTION)
        .order_by(AuditLog.created_at.asc())
        .limit(1)
    )
    log = result.scalar_one_or_none()
    return log.created_at if log else None


async def start_trial(session: AsyncSession, actor: str = "user") -> dict:
    settings = get_settings()
    existing = await _trial_start_date(session)
    if existing:
        return await get_trial_status(session)

    now = datetime.now(UTC)
    await AuditService.log(
        session,
        AuditEventType.SYSTEM,
        TRIAL_ACTION,
        actor=actor,
        details={
            "started_at": now.isoformat(),
            "duration_days": settings.paper_trial_days,
            "initial_capital_usdt": settings.paper_portfolio_usdt,
            "mode": "paper",
        },
    )
    await session.flush()
    return await get_trial_status(session)


async def _portfolio_metrics(session: AsyncSession) -> dict:
    settings = get_settings()
    initial = Decimal(str(settings.paper_portfolio_usdt))
    connector = ExchangeConnector("binance")

    result = await session.execute(select(Position).where(Position.is_open == True))  # noqa: E712
    positions = result.scalars().all()

    unrealized = Decimal("0")
    exposure = Decimal("0")
    for pos in positions:
        try:
            ticker = connector.fetch_ticker(pos.symbol)
            current = Decimal(str(ticker.get("last") or ticker.get("close") or pos.entry_price))
        except Exception:
            current = pos.current_price or pos.entry_price
        if pos.side == "buy":
            pnl = (current - pos.entry_price) * pos.quantity
        else:
            pnl = (pos.entry_price - current) * pos.quantity
        unrealized += pnl
        exposure += current * pos.quantity

    orders_count = await session.scalar(select(func.count()).select_from(Order)) or 0
    current_value = initial + unrealized
    return_pct = float((unrealized / initial) * 100) if initial else 0.0

    return {
        "initial_capital_usdt": float(initial),
        "current_value_usdt": float(current_value),
        "total_pnl_usdt": float(unrealized),
        "return_pct": round(return_pct, 2),
        "open_positions": len(positions),
        "total_orders": orders_count,
        "exposure_usdt": float(exposure),
    }


async def _learning_metrics(session: AsyncSession) -> dict:
    val_r = await session.execute(
        select(PredictionValidationRecord).order_by(PredictionValidationRecord.created_at.desc()).limit(100)
    )
    validations = val_r.scalars().all()

    mem_r = await session.execute(
        select(AIMemoryRecord).where(AIMemoryRecord.was_correct.isnot(None)).limit(200)
    )
    memory_evaluated = mem_r.scalars().all()

    direction_ok = [v for v in validations if v.direction_correct]
    accuracy = len(direction_ok) / max(len(validations), 1)
    memory_accuracy = sum(1 for m in memory_evaluated if m.was_correct) / max(len(memory_evaluated), 1)

    return {
        "validations_total": len(validations),
        "direction_accuracy": round(accuracy, 3),
        "memory_evaluated": len(memory_evaluated),
        "memory_accuracy": round(memory_accuracy, 3) if memory_evaluated else None,
        "avg_validation_score": round(
            sum(v.validation_score for v in validations) / max(len(validations), 1), 1
        ),
    }


def _readiness_score(days_elapsed: int, days_total: int, portfolio: dict, learning: dict) -> dict:
    score = 0
    notes = []

    if days_elapsed >= 14:
        score += 25
    else:
        notes.append(f"Aguarde {14 - days_elapsed} dias para baseline mínimo de aprendizado.")

    if days_elapsed >= days_total * 0.8:
        score += 15

    acc = learning.get("direction_accuracy", 0)
    if acc >= 0.55:
        score += 25
    elif acc >= 0.45:
        score += 12
        notes.append("Precisão da IA ainda moderada — continue o teste.")
    else:
        notes.append("Precisão baixa — a IA precisa de mais dados antes do live.")

    if portfolio.get("return_pct", 0) > 0:
        score += 20
    elif portfolio.get("return_pct", 0) > -5:
        score += 8
    else:
        notes.append("P&L paper negativo — revise estratégia antes do live.")

    if portfolio.get("total_orders", 0) >= 10:
        score += 15
    elif portfolio.get("total_orders", 0) >= 3:
        score += 8
    else:
        notes.append("Execute mais operações paper para calibrar a IA.")

    if learning.get("validations_total", 0) >= 20:
        score += 10

    ready_for_live = score >= 70 and days_elapsed >= 14 and acc >= 0.52

    return {
        "score": min(100, score),
        "ready_for_live": ready_for_live,
        "notes": notes,
        "recommendation": (
            "Você pode considerar capital real com cautela e valor inicial baixo."
            if ready_for_live
            else "Continue no modo paper — a IA ainda está aprendendo."
        ),
    }


async def get_trial_status(session: AsyncSession) -> dict:
    settings = get_settings()
    start = await _trial_start_date(session)
    now = datetime.now(UTC)

    if not start:
        return {
            "status": "not_started",
            "message": "Inicie o período de teste de 30 dias para a IA aprender sem risco.",
            "paper_trading": settings.paper_trading,
            "trial_days": settings.paper_trial_days,
            "initial_capital_usdt": settings.paper_portfolio_usdt,
        }

    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    days_elapsed = max(0, (now - start).days)
    days_total = settings.paper_trial_days
    days_remaining = max(0, days_total - days_elapsed)

    portfolio = await _portfolio_metrics(session)
    learning = await _learning_metrics(session)
    readiness = _readiness_score(days_elapsed, days_total, portfolio, learning)

    return {
        "status": "active" if days_remaining > 0 else "completed",
        "started_at": start.isoformat(),
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "days_total": days_total,
        "ends_at": (start + timedelta(days=days_total)).isoformat(),
        "paper_trading": settings.paper_trading,
        "portfolio": portfolio,
        "learning": learning,
        "readiness": readiness,
        "live_trading_allowed": settings.is_live_trading_allowed,
    }


async def run_learning_cycle(session: AsyncSession, actor: str = "system") -> dict:
    """Valida previsões passadas vs mercado real e atualiza memória da IA."""
    settings = get_settings()
    validator = PredictionValidationEngine()
    improver = SelfImprovementEngine()
    tracker = RealPerformanceTracker()
    connector = ExchangeConnector("binance")
    analyst_import = __import__("backend.market_ai_analyst.analyst", fromlist=["MarketAIAnalyst"])
    analyst = analyst_import.MarketAIAnalyst()

    cutoff = datetime.now(UTC) - timedelta(hours=24)
    consensus_r = await session.execute(
        select(AIConsensusRecord)
        .where(AIConsensusRecord.created_at <= cutoff)
        .order_by(AIConsensusRecord.created_at.desc())
        .limit(20)
    )
    consensus_rows = consensus_r.scalars().all()

    validated = 0
    memory_updated = 0
    improvements = 0

    for row in consensus_rows:
        try:
            df = analyst.fetch_ohlcv_dataframe(row.symbol, limit=50)
            exp_r = await session.execute(
                select(ExpectedReturnRecord)
                .where(ExpectedReturnRecord.symbol == row.symbol)
                .order_by(ExpectedReturnRecord.created_at.desc())
                .limit(1)
            )
            exp = exp_r.scalar_one_or_none()
            predicted_return = exp.expected_return_pct if exp else 0.0

            result = validator.validate(row.symbol, predicted_return, row.confidence, df)
            session.add(PredictionValidationRecord(
                symbol=row.symbol,
                predicted_return_pct=result.predicted_return_pct,
                actual_return_pct=result.actual_return_pct,
                predicted_confidence=result.predicted_confidence,
                calibration_error=result.calibration_error,
                direction_correct=result.direction_correct,
                validation_score=result.validation_score,
                window_days=7,
            ))
            validated += 1

            mem_r = await session.execute(
                select(AIMemoryRecord)
                .where(AIMemoryRecord.symbol == row.symbol, AIMemoryRecord.was_correct.is_(None))
                .order_by(AIMemoryRecord.created_at.desc())
                .limit(1)
            )
            mem = mem_r.scalar_one_or_none()
            if mem:
                was_correct = result.direction_correct or (
                    row.final_decision.upper() == "BUY" and result.actual_return_pct > 0
                )
                mem.was_correct = was_correct
                mem.performance_pct = result.actual_return_pct
                mem.outcome = "profit" if result.actual_return_pct > 0 else "loss"
                mem.lesson = (
                    f"Decisão {row.final_decision} validada: retorno real {result.actual_return_pct:+.2f}%"
                )
                memory_updated += 1

            actions = improver.process_feedback(
                result.validation_score / 100,
                result.direction_correct,
                result.false_positive,
                False,
            )
            improvements += len(actions)
        except Exception:
            continue

    portfolio = await _portfolio_metrics(session)
    perf = tracker.compute([portfolio["initial_capital_usdt"], portfolio["current_value_usdt"]])
    session.add(RealPerformanceRecord(
        portfolio_id="paper_trial",
        sharpe_ratio=perf.sharpe_ratio,
        sortino_ratio=perf.sortino_ratio,
        max_drawdown_pct=perf.max_drawdown_pct,
        cagr_pct=perf.cagr_pct,
        hit_rate=perf.hit_rate,
        expected_vs_actual_pct=perf.expected_vs_actual_pct,
        alpha_pct=perf.alpha_pct,
        metrics={"total_return_pct": perf.total_return_pct, "return_pct": portfolio["return_pct"]},
    ))

    await AuditService.log(
        session,
        AuditEventType.SYSTEM,
        LEARN_ACTION,
        actor=actor,
        details={"validated": validated, "memory_updated": memory_updated, "improvements": improvements},
    )

    return {
        "validated_predictions": validated,
        "memory_updated": memory_updated,
        "weight_adjustments": improvements,
        "portfolio": portfolio,
    }
