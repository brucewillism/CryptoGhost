"""Self-Improving Pipeline V6 — drift, adaptive thresholds, recalibration."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai_calibration.calibrator import ConfidenceCalibrator
from backend.app.ai.meta_learning.service import AgentPerformanceService
from backend.paper_trial.service import _portfolio_metrics
from backend.self_improving.pipeline import SelfImprovingPipeline
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.models_v5 import PredictionValidationRecord

logger = get_logger("cryptoghost.v6.self_improving")


class SelfImprovingPipelineV6:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.v5 = SelfImprovingPipeline()
        self.calibrator = ConfidenceCalibrator()
        self.performance = AgentPerformanceService()

    async def run(self, session: AsyncSession, symbol: str = "BTC/USDT") -> dict:
        portfolio = await _portfolio_metrics(session)

        val_r = await session.execute(
            select(PredictionValidationRecord)
            .order_by(PredictionValidationRecord.created_at.desc())
            .limit(100)
        )
        validations = val_r.scalars().all()

        if len(validations) >= 10:
            confs = [v.predicted_confidence for v in validations]
            outs = [int(v.direction_correct) for v in validations if v.direction_correct is not None]
            if len(outs) >= 10:
                self.calibrator.fit(confs[: len(outs)], outs)

        hit_rate = sum(1 for v in validations if v.direction_correct) / max(len(validations), 1)
        adaptive_threshold = self.settings.min_calibrated_confidence
        if hit_rate < 0.45:
            adaptive_threshold = min(0.85, adaptive_threshold + 0.05)
        elif hit_rate > 0.60:
            adaptive_threshold = max(0.50, adaptive_threshold - 0.02)

        drift_detected = hit_rate < 0.40 and len(validations) >= 20
        recalibration_triggered = drift_detected

        return {
            "version": "v6",
            "portfolio": portfolio,
            "hit_rate": round(hit_rate, 4),
            "adaptive_threshold": round(adaptive_threshold, 4),
            "validations_count": len(validations),
            "drift_detected": drift_detected,
            "recalibration_triggered": recalibration_triggered,
            "calibrator_fitted": self.calibrator._fitted,
        }
