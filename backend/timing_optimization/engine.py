"""CryptoGhost v5 - Timing Optimization."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.timing_optimization")


@dataclass
class TimingRecommendation:
    symbol: str
    action: str
    enter_now: bool
    wait_for_pullback: bool
    fake_breakout_risk: float
    optimal_timing_score: float
    probabilistic_window_hours: int
    reasons: list[str]


class TimingOptimizationEngine:
    """Otimização de timing de entrada/saída via microestrutura."""

    def optimize(self, df: pd.DataFrame, symbol: str, decision: str, orderflow_imbalance: float = 0) -> TimingRecommendation:
        close = df["close"].astype(float)
        returns = close.pct_change().dropna()
        vol = float(returns.tail(20).std()) if len(returns) > 20 else 0.02
        rsi_proxy = 50 + float(returns.tail(14).mean() / max(returns.tail(14).std(), 1e-6) * 20)
        momentum = float(close.pct_change(5).iloc[-1]) if len(close) > 5 else 0

        resistance = float(df["high"].astype(float).tail(20).max())
        support = float(df["low"].astype(float).tail(20).min())
        price = float(close.iloc[-1])
        near_resistance = (resistance - price) / price < 0.01
        near_support = (price - support) / price < 0.01

        fake_breakout = 0.3
        if near_resistance and momentum > 0.02 and vol > 0.03:
            fake_breakout = min(0.9, 0.5 + vol * 5)
        if orderflow_imbalance < 0 and decision == "BUY":
            fake_breakout = min(0.95, fake_breakout + 0.2)

        timing_score = 50.0
        reasons: list[str] = []
        if decision == "BUY":
            if near_support:
                timing_score += 25
                reasons.append("Preço próximo ao suporte")
            if orderflow_imbalance > 0.1:
                timing_score += 15
                reasons.append("Delta positivo — compra agressiva")
            if near_resistance:
                timing_score -= 20
                reasons.append("Próximo à resistência — cautela")
        elif decision == "SELL":
            if near_resistance:
                timing_score += 20
                reasons.append("Resistência — saída favorável")

        timing_score -= fake_breakout * 30
        timing_score = max(0, min(100, timing_score))

        enter_now = timing_score >= 65 and fake_breakout < 0.5
        wait_pullback = not enter_now and decision == "BUY" and near_resistance

        action = "enter_now" if enter_now else "wait_pullback" if wait_pullback else "hold"

        return TimingRecommendation(
            symbol=symbol, action=action, enter_now=enter_now, wait_for_pullback=wait_pullback,
            fake_breakout_risk=round(fake_breakout, 4), optimal_timing_score=round(timing_score, 2),
            probabilistic_window_hours=4 if vol > 0.03 else 12, reasons=reasons or ["Timing neutro"],
        )
