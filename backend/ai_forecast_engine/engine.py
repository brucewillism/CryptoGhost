"""CryptoGhost v4 - AI Forecast Engine."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import GradientBoostingRegressor

from backend.investment.context import MarketContext
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.ai_forecast_engine")

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


class LSTMForecaster(nn.Module):
    def __init__(self, input_size: int = 5, hidden: int = 32):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden, batch_first=True)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


@dataclass
class ForecastResult:
    symbol: str
    trend: str
    reversal_probability: float
    breakout_probability: float
    crash_probability: float
    momentum_continuation: float
    predicted_return_pct: float
    method: str
    model_weights: dict


class AIForecastEngine:
    """Ensemble: LSTM + XGBoost/GBM + momentum extrapolation."""

    def __init__(self) -> None:
        self._lstm: LSTMForecaster | None = None

    def forecast(self, ctx: MarketContext, horizon: int = 7) -> ForecastResult:
        df = ctx.df
        features, targets = self._build_features(df)
        predictions: dict[str, float] = {}

        if len(features) >= 30:
            predictions["gbm"] = self._gbm_forecast(features, targets)
            predictions["lstm"] = self._lstm_forecast(features)
        predictions["momentum"] = float(df["close"].pct_change(5).iloc[-1] * 100) if len(df) > 5 else 0

        weights = {"gbm": 0.4, "lstm": 0.35, "momentum": 0.25}
        active = {k: v for k, v in predictions.items() if k in weights}
        w_sum = sum(weights[k] for k in active)
        pred_return = sum(active[k] * weights[k] for k in active) / w_sum if w_sum else 0

        vol = float(df["close"].pct_change().std() * np.sqrt(252)) if len(df) > 10 else 0.3
        reversal = min(0.9, max(0.05, float(ctx.analysis.get("reversal_probability", 0.2))))
        breakout = min(0.9, max(0.05, abs(ctx.momentum) / 20))
        crash = min(0.95, ctx.crash_probability + (0.1 if vol > 0.8 else 0))
        momentum_cont = min(0.95, max(0.05, 0.5 + ctx.momentum / 30))

        trend = "bullish" if pred_return > 1 else "bearish" if pred_return < -1 else "neutral"

        return ForecastResult(
            symbol=ctx.symbol, trend=trend, reversal_probability=round(reversal, 4),
            breakout_probability=round(breakout, 4), crash_probability=round(crash, 4),
            momentum_continuation=round(momentum_cont, 4), predicted_return_pct=round(pred_return, 2),
            method="ensemble_lstm_xgb_momentum", model_weights={k: round(v, 4) for k, v in active.items()},
        )

    @staticmethod
    def _build_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)
        ret = close.pct_change().fillna(0)
        vol_ma = volume / volume.rolling(10).mean().fillna(volume.mean())
        rsi_proxy = ret.rolling(14).mean().fillna(0)
        mom = close.pct_change(5).fillna(0)
        feat = np.column_stack([ret.values, vol_ma.values, rsi_proxy.values, mom.values, volume.values / volume.max()])
        target = close.pct_change(3).shift(-3).fillna(0).values * 100
        valid = ~np.isnan(feat).any(axis=1) & ~np.isnan(target)
        return feat[valid], target[valid]

    def _gbm_forecast(self, features: np.ndarray, targets: np.ndarray) -> float:
        X, y = features[:-3], targets[:-3]
        if len(X) < 20:
            return 0.0
        model = XGBRegressor(n_estimators=50, max_depth=4) if HAS_XGB else GradientBoostingRegressor(n_estimators=50, max_depth=3)
        model.fit(X, y)
        return float(model.predict(features[-1:].reshape(1, -1))[0])

    def _lstm_forecast(self, features: np.ndarray, seq_len: int = 20) -> float:
        if len(features) < seq_len + 5:
            return 0.0
        device = torch.device("cpu")
        model = LSTMForecaster(features.shape[1]).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        X_seq = torch.FloatTensor(np.array([features[i:i + seq_len] for i in range(len(features) - seq_len - 1)])).to(device)
        y_seq = torch.FloatTensor(features[seq_len + 1:, 0] * 100).to(device)
        if len(X_seq) < 10:
            return 0.0
        model.train()
        for _ in range(15):
            optimizer.zero_grad()
            pred = model(X_seq).squeeze()
            loss = nn.functional.mse_loss(pred, y_seq[:len(pred)])
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            last = torch.FloatTensor(features[-seq_len:].reshape(1, seq_len, -1)).to(device)
            return float(model(last).item())
