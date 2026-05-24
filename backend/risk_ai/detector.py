"""CryptoGhost - Risk AI."""

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.shared.logging_config import get_logger
from backend.shared.metrics import AI_CONFIDENCE_GAUGE, AI_LATENCY

logger = get_logger("cryptoghost.risk_ai")


@dataclass
class RiskAssessment:
    crash_probability: float
    flash_volatility_risk: float
    liquidity_risk: float
    manipulation_score: float
    liquidation_cascade_risk: float
    instability_score: float
    overall_risk: str
    confidence: float
    anomalies_detected: int
    warnings: list[str]


class RiskAI:
    """IA especializada em detecção de risco pré-operacional."""

    def assess(self, df: pd.DataFrame, buy_pressure: float = 0.5, liquidity_score: float = 50.0) -> RiskAssessment:
        start = time.perf_counter()
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)
        returns = close.pct_change().dropna()

        volatility = float(returns.std() * np.sqrt(252))
        vol_cluster = self._volatility_clustering(returns)
        anomalies = self._detect_anomalies(df)
        flash_vol = self._flash_volatility_risk(returns)
        liquidity_risk = max(0, 1 - liquidity_score / 100)
        manipulation = self._manipulation_score(df, volume)
        liquidation = self._liquidation_cascade_risk(returns, volume)
        crash_prob = self._crash_probability(returns, vol_cluster, anomalies)

        instability = (crash_prob + flash_vol + liquidity_risk + manipulation + liquidation) / 5
        warnings = self._generate_warnings(crash_prob, flash_vol, liquidity_risk, manipulation, anomalies)

        if instability > 0.7:
            overall = "critical"
        elif instability > 0.5:
            overall = "high"
        elif instability > 0.3:
            overall = "medium"
        else:
            overall = "low"

        confidence = min(0.95, 0.6 + len(df) / 500)

        elapsed = time.perf_counter() - start
        AI_LATENCY.labels(agent="risk_ai").observe(elapsed)
        AI_CONFIDENCE_GAUGE.labels(agent="risk_ai").set(confidence)

        return RiskAssessment(
            crash_probability=round(crash_prob, 3),
            flash_volatility_risk=round(flash_vol, 3),
            liquidity_risk=round(liquidity_risk, 3),
            manipulation_score=round(manipulation, 3),
            liquidation_cascade_risk=round(liquidation, 3),
            instability_score=round(instability, 3),
            overall_risk=overall,
            confidence=round(confidence, 2),
            anomalies_detected=anomalies,
            warnings=warnings,
        )

    @staticmethod
    def _volatility_clustering(returns: pd.Series) -> float:
        if len(returns) < 20:
            return 0.0
        squared = returns ** 2
        recent_vol = squared.tail(10).mean()
        historical_vol = squared.mean()
        return float(min(1.0, recent_vol / max(historical_vol, 1e-10) - 1))

    @staticmethod
    def _detect_anomalies(df: pd.DataFrame) -> int:
        if len(df) < 30:
            return 0
        features = df[["open", "high", "low", "close", "volume"]].astype(float).pct_change().dropna()
        model = IsolationForest(contamination=0.05, random_state=42)
        predictions = model.fit_predict(features)
        return int((predictions == -1).sum())

    @staticmethod
    def _flash_volatility_risk(returns: pd.Series) -> float:
        if len(returns) < 5:
            return 0.0
        max_move = float(returns.tail(5).abs().max())
        return min(1.0, max_move * 20)

    @staticmethod
    def _manipulation_score(df: pd.DataFrame, volume: pd.Series) -> float:
        if len(df) < 20:
            return 0.0
        close = df["close"].astype(float)
        vol_spike = volume.iloc[-1] / max(volume.tail(20).mean(), 1)
        price_spike = abs(close.pct_change().iloc[-1])
        if vol_spike > 5 and price_spike < 0.005:
            return 0.8
        if vol_spike > 3 and price_spike > 0.05:
            return 0.6
        return min(0.5, vol_spike / 10)

    @staticmethod
    def _liquidation_cascade_risk(returns: pd.Series, volume: pd.Series) -> float:
        if len(returns) < 10:
            return 0.0
        consecutive_down = 0
        for r in returns.tail(10):
            if r < -0.02:
                consecutive_down += 1
            else:
                consecutive_down = 0
        vol_surge = volume.iloc[-1] / max(volume.tail(20).mean(), 1)
        return min(1.0, consecutive_down * 0.15 + (vol_surge - 1) * 0.1)

    @staticmethod
    def _crash_probability(returns: pd.Series, vol_cluster: float, anomalies: int) -> float:
        if len(returns) < 20:
            return 0.1
        skew = float(returns.skew())
        kurt = float(returns.kurtosis())
        tail_risk = max(0, -skew) * 0.2 + max(0, kurt - 3) * 0.05
        return min(0.95, vol_cluster * 0.4 + tail_risk + anomalies * 0.05)

    @staticmethod
    def _generate_warnings(crash, flash, liquidity, manipulation, anomalies) -> list[str]:
        warnings = []
        if crash > 0.6:
            warnings.append("Alta probabilidade de crash detectada")
        if flash > 0.5:
            warnings.append("Risco de flash volatility elevado")
        if liquidity > 0.6:
            warnings.append("Liquidez insuficiente para operação segura")
        if manipulation > 0.5:
            warnings.append("Possível padrão de manipulação de mercado")
        if anomalies > 3:
            warnings.append(f"{anomalies} anomalias estatísticas detectadas")
        return warnings
