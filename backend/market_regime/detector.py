"""CryptoGhost - Market Regime Detection."""

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture

from backend.shared.logging_config import get_logger
from backend.shared.metrics import AI_CONFIDENCE_GAUGE, AI_LATENCY, MARKET_REGIME_GAUGE

logger = get_logger("cryptoghost.market_regime")

REGIME_LABELS = {
    0: "low_volatility",
    1: "bull_market",
    2: "bear_market",
    3: "high_volatility",
    4: "sideways",
    5: "accumulation",
    6: "distribution",
}

STRATEGY_MAP = {
    "bull_market": "trend_following_aggressive",
    "bear_market": "defensive_short_bias",
    "sideways": "mean_reversion",
    "high_volatility": "reduce_position_size",
    "low_volatility": "breakout_watch",
    "accumulation": "gradual_accumulation",
    "distribution": "gradual_distribution",
}


@dataclass
class RegimeDetection:
    regime: str
    confidence: float
    volatility: float
    trend_strength: float
    features: dict
    strategy_adjustment: str
    all_regime_probs: dict


class MarketRegimeDetector:
    """Detecta regimes de mercado via GMM (aproximação HMM) e análise de volatilidade."""

    def detect(self, df: pd.DataFrame, symbol: str = "BTC/USDT") -> RegimeDetection:
        start = time.perf_counter()
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)
        returns = close.pct_change().dropna()

        features_df = pd.DataFrame({
            "returns": returns,
            "volatility": returns.rolling(10).std(),
            "volume_change": volume.pct_change(),
            "trend": close.pct_change(20),
        }).dropna()

        if len(features_df) < 30:
            return self._rule_based_detection(close, returns, symbol)

        X = features_df[["returns", "volatility", "volume_change", "trend"]].values
        n_components = min(4, len(features_df) // 10)
        gmm = GaussianMixture(n_components=max(2, n_components), random_state=42, covariance_type="full")
        gmm.fit(X)
        probs = gmm.predict_proba(X[-1:])
        regime_idx = int(np.argmax(probs[0]))

        regime_map = self._map_component_to_regime(gmm.means_, regime_idx)
        regime = REGIME_LABELS.get(regime_map, "sideways")
        confidence = float(probs[0][regime_idx])

        volatility = float(returns.std() * np.sqrt(252) * 100)
        trend_strength = abs(float(close.pct_change(20).iloc[-1] * 100))

        all_probs = {REGIME_LABELS.get(i, f"regime_{i}"): round(float(p), 3) for i, p in enumerate(probs[0])}

        elapsed = time.perf_counter() - start
        AI_LATENCY.labels(agent="regime").observe(elapsed)
        AI_CONFIDENCE_GAUGE.labels(agent="regime").set(confidence)
        MARKET_REGIME_GAUGE.labels(symbol=symbol, regime=regime).set(confidence)

        return RegimeDetection(
            regime=regime,
            confidence=round(confidence, 2),
            volatility=round(volatility, 2),
            trend_strength=round(trend_strength, 2),
            features={"returns_mean": round(float(returns.mean()), 5), "volatility": round(volatility, 2)},
            strategy_adjustment=STRATEGY_MAP.get(regime, "hold"),
            all_regime_probs=all_probs,
        )

    def _rule_based_detection(self, close: pd.Series, returns: pd.Series, symbol: str) -> RegimeDetection:
        vol = float(returns.std() * np.sqrt(252) * 100) if len(returns) > 1 else 0
        trend = float(close.pct_change(min(20, len(close))).iloc[-1] * 100) if len(close) > 1 else 0

        if vol > 80:
            regime = "high_volatility"
        elif trend > 10:
            regime = "bull_market"
        elif trend < -10:
            regime = "bear_market"
        elif abs(trend) < 3:
            regime = "sideways"
        else:
            regime = "accumulation" if trend > 0 else "distribution"

        return RegimeDetection(
            regime=regime, confidence=0.6, volatility=vol, trend_strength=abs(trend),
            features={"trend": trend}, strategy_adjustment=STRATEGY_MAP.get(regime, "hold"),
            all_regime_probs={regime: 0.6},
        )

    @staticmethod
    def _map_component_to_regime(means: np.ndarray, idx: int) -> int:
        mean = means[idx]
        ret, vol, _, trend = mean[0], mean[1], mean[2], mean[3]
        if vol > 0.03:
            return 3
        if ret > 0.005 and trend > 0:
            return 1
        if ret < -0.005 and trend < 0:
            return 2
        if vol < 0.01:
            return 0
        if trend > 0:
            return 5
        return 4
