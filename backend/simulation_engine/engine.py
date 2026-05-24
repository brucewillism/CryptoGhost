"""CryptoGhost v3 - Market Simulation Engine."""

import random
from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.simulation_engine")


@dataclass
class SimulationConfig:
    slippage_pct: float = 0.0005
    spread_pct: float = 0.0003
    latency_ms: float = 50.0
    market_impact_factor: float = 0.0001
    spoofing_probability: float = 0.01
    flash_crash_probability: float = 0.005
    whale_order_probability: float = 0.02
    low_liquidity_threshold: float = 0.3


@dataclass
class SimulationResult:
    symbol: str
    simulation_type: str
    initial_capital: float
    final_capital: float
    pnl: float
    pnl_pct: float
    total_trades: int
    max_drawdown_pct: float
    events: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


class MarketSimulationEngine:
    """Simulação institucional com microestrutura de mercado."""

    def __init__(self, config: SimulationConfig | None = None):
        self.config = config or SimulationConfig()

    def simulate_trading(
        self,
        df: pd.DataFrame,
        symbol: str,
        initial_capital: float = 10000.0,
        strategy_signals: list[int] | None = None,
    ) -> SimulationResult:
        capital = initial_capital
        position = 0.0
        entry = 0.0
        trades = 0
        events: list[str] = []
        equity_curve = [capital]

        signals = strategy_signals or [0] * len(df)

        for i in range(30, len(df)):
            price = float(df.iloc[i]["close"])
            volume = float(df.iloc[i]["volume"])
            vol_ma = float(df["volume"].iloc[max(0, i - 20):i + 1].mean())
            liquidity = volume / max(vol_ma, 1)

            if random.random() < self.config.flash_crash_probability:
                price *= 0.95
                events.append(f"flash_crash at step {i}")

            if random.random() < self.config.whale_order_probability:
                price *= 1 + random.choice([-1, 1]) * 0.02
                events.append(f"whale_movement at step {i}")

            spread = self.config.spread_pct * (2.0 if liquidity < self.config.low_liquidity_threshold else 1.0)
            slippage = self.config.slippage_pct * (1.5 if liquidity < self.config.low_liquidity_threshold else 1.0)
            exec_price = price * (1 + spread + slippage)

            signal = signals[i] if i < len(signals) else 0

            if signal == 1 and position == 0:
                qty = (capital * 0.1) / exec_price
                position = qty
                entry = exec_price
                capital -= qty * exec_price
                trades += 1
            elif signal == 2 and position > 0:
                capital += position * exec_price * 0.999
                position = 0
                trades += 1

            equity = capital + position * price
            equity_curve.append(equity)

        final = capital + position * float(df.iloc[-1]["close"])
        pnl = final - initial_capital
        eq = pd.Series(equity_curve)
        drawdown = ((eq - eq.cummax()) / eq.cummax()).min()

        return SimulationResult(
            symbol=symbol, simulation_type="microstructure", initial_capital=initial_capital,
            final_capital=final, pnl=pnl, pnl_pct=pnl / initial_capital * 100,
            total_trades=trades, max_drawdown_pct=float(drawdown) * 100, events=events,
            metrics={"liquidity_events": len([e for e in events if "whale" in e or "flash" in e])},
        )

    def simulate_stress_scenario(self, df: pd.DataFrame, symbol: str, scenario: str = "flash_crash") -> SimulationResult:
        df = df.copy()
        if scenario == "flash_crash":
            crash_idx = len(df) // 2
            df.loc[crash_idx:, "close"] = df.loc[crash_idx:, "close"] * 0.7
            df.loc[crash_idx:, "volume"] = df.loc[crash_idx:, "volume"] * 3
        elif scenario == "low_liquidity":
            df["volume"] = df["volume"] * 0.1
        elif scenario == "spoofing":
            for i in range(0, len(df), 50):
                df.loc[i, "high"] = df.loc[i, "close"] * 1.05
                df.loc[i, "low"] = df.loc[i, "close"] * 0.95

        config = SimulationConfig(
            flash_crash_probability=0.1 if scenario == "flash_crash" else 0.005,
            spoofing_probability=0.1 if scenario == "spoofing" else 0.01,
        )
        engine = MarketSimulationEngine(config)
        result = engine.simulate_trading(df, symbol)
        result.simulation_type = f"stress_{scenario}"
        return result
