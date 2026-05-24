"""CryptoGhost v5 - Prediction Validation Engine."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.prediction_validation")


@dataclass
class ValidationResult:
    symbol: str
    predicted_return_pct: float
    actual_return_pct: float
    predicted_confidence: float
    calibration_error: float
    direction_correct: bool
    validation_score: float
    false_positive: bool
    rolling_accuracy: float


class PredictionValidationEngine:
    """Validação contínua: previsão vs realidade."""

    def __init__(self, window: int = 30) -> None:
        self._history: list[dict] = []
        self.window = window

    def validate(
        self,
        symbol: str,
        predicted_return: float,
        predicted_confidence: float,
        df: pd.DataFrame,
        lookback_bars: int = 5,
    ) -> ValidationResult:
        close = df["close"].astype(float)
        if len(close) > lookback_bars + 1:
            actual = float((close.iloc[-1] / close.iloc[-lookback_bars - 1] - 1) * 100)
        else:
            actual = 0.0

        cal_error = abs(predicted_confidence - (1.0 if (predicted_return > 0) == (actual > 0) else 0.0))
        direction_ok = (predicted_return > 0 and actual > 0) or (predicted_return <= 0 and actual <= 0)
        false_pos = predicted_return > 0 and actual < 0 and predicted_confidence > 0.6

        ret_error = abs(predicted_return - actual)
        score = max(0, 100 - ret_error * 2 - cal_error * 50)
        if direction_ok:
            score = min(100, score + 15)
        if false_pos:
            score = max(0, score - 25)

        self._history.append({"symbol": symbol, "score": score, "direction_ok": direction_ok})
        if len(self._history) > 500:
            self._history = self._history[-500:]

        recent = [h for h in self._history if h["symbol"] == symbol][-self.window:]
        rolling_acc = float(np.mean([h["direction_ok"] for h in recent])) if recent else 0.5

        return ValidationResult(
            symbol=symbol, predicted_return_pct=round(predicted_return, 2),
            actual_return_pct=round(actual, 2), predicted_confidence=round(predicted_confidence, 4),
            calibration_error=round(cal_error, 4), direction_correct=direction_ok,
            validation_score=round(score, 2), false_positive=false_pos,
            rolling_accuracy=round(rolling_acc, 4),
        )
