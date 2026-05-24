"""CryptoGhost v3 - AI Confidence Calibration."""

import math
from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.ai_calibration")


@dataclass
class CalibratedResult:
    raw_confidence: float
    calibrated_confidence: float
    uncertainty: float
    reliability_score: float
    method: str


class ConfidenceCalibrator:
    """Calibra confiança via Platt Scaling e Isotonic Regression."""

    def __init__(self) -> None:
        self._platt: LogisticRegression | None = None
        self._isotonic: IsotonicRegression | None = None
        self._historical_accuracy: list[tuple[float, int]] = []
        self._fitted = False

    def fit(self, confidences: list[float], outcomes: list[int]) -> None:
        if len(confidences) < 10:
            logger.warning("calibration_insufficient_data", samples=len(confidences))
            return

        X = np.array(confidences).reshape(-1, 1)
        y = np.array(outcomes)

        self._platt = LogisticRegression(max_iter=1000)
        self._platt.fit(X, y)

        self._isotonic = IsotonicRegression(out_of_bounds="clip")
        self._isotonic.fit(confidences, outcomes)

        self._historical_accuracy = list(zip(confidences, outcomes))
        self._fitted = True
        logger.info("calibrator_fitted", samples=len(confidences))

    def calibrate(
        self,
        raw_confidence: float,
        agent: str = "consensus",
        regime: str = "neutral",
        agreement_ratio: float = 1.0,
    ) -> CalibratedResult:
        calibrated = raw_confidence
        method = "historical_fallback"

        if self._fitted and self._isotonic is not None:
            calibrated = float(self._isotonic.predict([raw_confidence])[0])
            method = "isotonic_regression"
        elif self._fitted and self._platt is not None:
            calibrated = float(self._platt.predict_proba([[raw_confidence]])[0][1])
            method = "platt_scaling"
        else:
            calibrated = self._fallback_calibrate(raw_confidence, agreement_ratio)

        regime_adj = {"bull_market": 1.05, "bear_market": 0.95, "high_volatility": 0.85}.get(regime, 1.0)
        calibrated = max(0.01, min(0.99, calibrated * regime_adj))

        uncertainty = self._estimate_uncertainty(raw_confidence, agreement_ratio)
        reliability = self._reliability_score(calibrated, uncertainty, agreement_ratio)

        return CalibratedResult(
            raw_confidence=round(raw_confidence, 4),
            calibrated_confidence=round(calibrated, 4),
            uncertainty=round(uncertainty, 4),
            reliability_score=round(reliability, 4),
            method=method,
        )

    @staticmethod
    def _fallback_calibrate(raw: float, agreement: float) -> float:
        return raw * (0.7 + 0.3 * agreement)

    @staticmethod
    def _estimate_uncertainty(confidence: float, agreement: float) -> float:
        base = 1.0 - confidence
        disagreement = 1.0 - agreement
        return min(0.99, math.sqrt(base ** 2 + disagreement ** 2))

    @staticmethod
    def _reliability_score(calibrated: float, uncertainty: float, agreement: float) -> float:
        return max(0.0, min(1.0, calibrated * agreement * (1 - uncertainty)))

    def update_online(self, confidence: float, was_correct: bool) -> None:
        self._historical_accuracy.append((confidence, int(was_correct)))
        if len(self._historical_accuracy) >= 20 and len(self._historical_accuracy) % 10 == 0:
            confs, outs = zip(*self._historical_accuracy[-100:])
            self.fit(list(confs), list(outs))
