"""CryptoGhost v5 - API Self-Improving."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.institutional_data_lake.lake import InstitutionalDataLake
from backend.self_improving.pipeline import SelfImprovingPipeline
from backend.shared.database import get_async_session
from backend.shared.models_v5 import (
    AITruthRecord,
    DriftDetectionRecord,
    MetaLearningRecord,
    PredictionValidationRecord,
    RealPerformanceRecord,
    SelfImprovementRecord,
)
from backend.shared.security import get_current_user

router = APIRouter(prefix="/v5", tags=["Self-Improving v5"])


@router.get("/dashboard")
async def v5_dashboard(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    truth_r = await session.execute(select(AITruthRecord).order_by(AITruthRecord.created_at.desc()).limit(5))
    truths = truth_r.scalars().all()

    drift_r = await session.execute(select(DriftDetectionRecord).order_by(DriftDetectionRecord.created_at.desc()).limit(5))
    drifts = drift_r.scalars().all()

    meta_r = await session.execute(
        select(MetaLearningRecord).where(MetaLearningRecord.is_best.is_(True))
        .order_by(MetaLearningRecord.created_at.desc()).limit(5)
    )
    metas = meta_r.scalars().all()

    val_r = await session.execute(select(PredictionValidationRecord).order_by(PredictionValidationRecord.created_at.desc()).limit(10))
    validations = val_r.scalars().all()

    perf_r = await session.execute(select(RealPerformanceRecord).order_by(RealPerformanceRecord.created_at.desc()).limit(1))
    perf = perf_r.scalar_one_or_none()

    imp_r = await session.execute(select(SelfImprovementRecord).order_by(SelfImprovementRecord.created_at.desc()).limit(10))
    improvements = imp_r.scalars().all()

    avg_accuracy = sum(v.validation_score for v in validations) / max(len(validations), 1)

    return {
        "ai_truth": [
            {"symbol": t.symbol, "truth_score": t.truth_score, "corrected_confidence": t.corrected_confidence,
             "overconfidence": t.overconfidence_detected}
            for t in truths
        ],
        "drift": [
            {"model": d.model_name, "type": d.drift_type, "score": d.drift_score, "retrain": d.retrain_triggered}
            for d in drifts
        ],
        "model_ranking": [
            {"model": m.model_name, "regime": m.market_regime, "accuracy": m.historical_accuracy, "sharpe": m.sharpe_ratio}
            for m in metas
        ],
        "prediction_accuracy": {
            "avg_validation_score": round(avg_accuracy, 2),
            "recent": [
                {"symbol": v.symbol, "predicted": v.predicted_return_pct, "actual": v.actual_return_pct,
                 "correct": v.direction_correct, "score": v.validation_score}
                for v in validations[:5]
            ],
        },
        "real_performance": {
            "sharpe": perf.sharpe_ratio, "sortino": perf.sortino_ratio,
            "max_drawdown": perf.max_drawdown_pct, "hit_rate": perf.hit_rate,
            "expected_vs_actual": perf.expected_vs_actual_pct,
        } if perf else None,
        "self_improvement": [
            {"action": i.action_type, "target": i.target, "improvement_pct": i.improvement_pct}
            for i in improvements
        ],
    }


@router.get("/data-lake/{category}")
async def query_data_lake(
    category: str,
    symbol: str | None = None,
    limit: int = Query(20, le=100),
    _user: dict = Depends(get_current_user),
) -> dict:
    lake = InstitutionalDataLake()
    return {"category": category, "records": lake.query_recent(category, symbol, limit)}
