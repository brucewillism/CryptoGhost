"""Quant ML predictors — XGBoost, RF, LSTM ensemble."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.v6.quant_models")

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from sklearn.ensemble import RandomForestRegressor


@dataclass
class QuantPrediction:
    predicted_return_pct: float
    probability_up: float
    method: str
    model_weights: dict[str, float]


class QuantEnsemble:
    """ML quantitativo separado de LLM."""

    def predict(self, df: pd.DataFrame, features: dict[str, float]) -> QuantPrediction:
        if len(df) < 40:
            return QuantPrediction(0.0, 0.5, "insufficient_data", {})

        close = df["close"].astype(float)
        returns = close.pct_change().dropna().values
        X = np.array([returns[i : i + 5] for i in range(len(returns) - 5)])
        y = np.array([returns[i + 5] for i in range(len(returns) - 5)])

        if len(X) < 20:
            mom = features.get("momentum", 0)
            prob = 0.5 + min(0.4, max(-0.4, mom / 50))
            return QuantPrediction(mom, prob, "momentum_fallback", {"momentum": 1.0})

        preds: dict[str, float] = {}
        weights: dict[str, float] = {}

        rf = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        rf.fit(X, y)
        preds["rf"] = float(rf.predict(X[-1:])[0] * 100)
        weights["rf"] = 0.35

        if HAS_XGB:
            xgb = XGBRegressor(n_estimators=50, max_depth=4, random_state=42, verbosity=0)
            xgb.fit(X, y)
            preds["xgb"] = float(xgb.predict(X[-1:])[0] * 100)
            weights["xgb"] = 0.45

        preds["momentum"] = float(features.get("momentum", 0))
        weights["momentum"] = 0.20

        w_sum = sum(weights[k] for k in preds)
        pred = sum(preds[k] * weights[k] for k in preds) / w_sum
        prob_up = 0.5 + min(0.45, max(-0.45, pred / 20))

        return QuantPrediction(
            predicted_return_pct=round(pred, 4),
            probability_up=round(prob_up, 4),
            method="ensemble_rf_xgb_momentum",
            model_weights={k: round(v, 3) for k, v in weights.items()},
        )
