"""CryptoGhost v5 - Drift Detection (concept/data/regime)."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.drift_detection")


@dataclass
class DriftAnalysis:
    model_name: str
    drift_type: str
    drift_score: float
    regime_shift_detected: bool
    retrain_triggered: bool
    details: dict


class DriftDetectionEngine:
    """Concept drift, data drift e regime shift."""

    RETRAIN_THRESHOLD = 0.2
    PSI_THRESHOLD = 0.15

    def __init__(self) -> None:
        self._baseline_returns: np.ndarray | None = None
        self._baseline_regime: str | None = None

    def set_baseline(self, df: pd.DataFrame, regime: str) -> None:
        close = df["close"].astype(float)
        self._baseline_returns = close.pct_change().dropna().values
        self._baseline_regime = regime

    def detect(self, df: pd.DataFrame, model_name: str, current_regime: str) -> list[DriftAnalysis]:
        results: list[DriftAnalysis] = []
        close = df["close"].astype(float)
        recent = close.pct_change().dropna().values

        if self._baseline_returns is not None and len(recent) > 20 and len(self._baseline_returns) > 20:
            ks_stat, ks_p = stats.ks_2samp(self._baseline_returns[-100:], recent[-50:])
            data_drift = float(ks_stat)
            results.append(DriftAnalysis(
                model_name, "data_drift", round(data_drift, 4),
                False, data_drift > self.RETRAIN_THRESHOLD,
                {"ks_statistic": round(data_drift, 4), "p_value": round(float(ks_p), 6)},
            ))

            psi = self._population_stability_index(self._baseline_returns[-100:], recent[-50:])
            if psi > self.PSI_THRESHOLD:
                results.append(DriftAnalysis(
                    model_name, "concept_drift", round(psi, 4),
                    False, psi > self.RETRAIN_THRESHOLD,
                    {"psi": round(psi, 4)},
                ))

        regime_shift = self._baseline_regime is not None and self._baseline_regime != current_regime
        if regime_shift:
            results.append(DriftAnalysis(
                model_name, "regime_shift", 0.8, True, True,
                {"from": self._baseline_regime, "to": current_regime},
            ))

        if not results:
            results.append(DriftAnalysis(model_name, "none", 0.0, False, False, {"status": "stable"}))

        return results

    @staticmethod
    def _population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
        breakpoints = np.linspace(min(expected.min(), actual.min()), max(expected.max(), actual.max()), bins + 1)
        expected_pct = np.histogram(expected, breakpoints)[0] / max(len(expected), 1)
        actual_pct = np.histogram(actual, breakpoints)[0] / max(len(actual), 1)
        expected_pct = np.where(expected_pct == 0, 0.0001, expected_pct)
        actual_pct = np.where(actual_pct == 0, 0.0001, actual_pct)
        return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))

    def max_drift_score(self, analyses: list[DriftAnalysis]) -> float:
        return max((a.drift_score for a in analyses), default=0.0)
