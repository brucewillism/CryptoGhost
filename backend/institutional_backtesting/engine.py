"""CryptoGhost v5 - Institutional Backtesting."""

from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np
import pandas as pd

from backend.market_replay_engine.engine import MarketReplayEngine, ReplayMode
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.institutional_backtesting")


@dataclass
class InstitutionalBacktestResult:
    symbol: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    total_trades: int
    avg_slippage_pct: float
    events: list[str] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)


class InstitutionalBacktestingEngine:
    """Backtest tick-by-tick com slippage, spread, latência e impacto."""

    def __init__(
        self,
        slippage_pct: float = 0.0008,
        spread_pct: float = 0.0004,
        latency_bars: int = 1,
        impact_factor: float = 0.00015,
    ):
        self.slippage_pct = slippage_pct
        self.spread_pct = spread_pct
        self.latency_bars = latency_bars
        self.impact_factor = impact_factor
        self.replay = MarketReplayEngine()

    def run(
        self,
        df: pd.DataFrame,
        symbol: str,
        signals: list[int] | None = None,
        initial_capital: float = 10000.0,
    ) -> InstitutionalBacktestResult:
        df = df.reset_index(drop=True)
        capital = initial_capital
        position = 0.0
        entry = 0.0
        trades = 0
        slippages: list[float] = []
        events: list[str] = []
        equity: list[float] = [capital]

        sigs = signals or [0] * len(df)

        for i in range(30, len(df)):
            row = df.iloc[i]
            price = float(row["close"])
            volume = float(row["volume"])
            vol_ma = float(df["volume"].iloc[max(0, i - 20):i + 1].mean())
            liquidity = volume / max(vol_ma, 1)

            spread = self.spread_pct * (2.0 if liquidity < 0.3 else 1.0)
            slip = self.slippage_pct * (1.5 if liquidity < 0.3 else 1.0)
            impact = self.impact_factor * abs(sigs[i] - 1) / max(liquidity, 0.1)
            exec_price = price * (1 + spread + slip + impact)
            slippages.append(spread + slip + impact)

            if liquidity < 0.2:
                events.append(f"low_liquidity@{i}")

            signal = sigs[min(i + self.latency_bars, len(sigs) - 1)]

            if signal == 1 and position == 0:
                qty = (capital * 0.1) / exec_price
                if qty * exec_price <= capital:
                    position = qty
                    entry = exec_price
                    capital -= qty * exec_price
                    trades += 1
            elif signal == 2 and position > 0:
                capital += position * exec_price * 0.999
                position = 0
                trades += 1

            eq = capital + position * price
            equity.append(eq)

        final = capital + position * float(df.iloc[-1]["close"])
        ret = (final / initial_capital - 1) * 100
        eq_s = pd.Series(equity)
        rets = eq_s.pct_change().dropna()
        sharpe = float(rets.mean() / rets.std() * np.sqrt(252)) if len(rets) > 1 and rets.std() > 0 else 0
        dd = float((eq_s / eq_s.cummax() - 1).min() * 100)

        return InstitutionalBacktestResult(
            symbol=symbol, initial_capital=initial_capital, final_capital=final,
            total_return_pct=round(ret, 2), sharpe_ratio=round(sharpe, 4),
            max_drawdown_pct=round(abs(dd), 2), total_trades=trades,
            avg_slippage_pct=round(float(np.mean(slippages)) * 100, 4) if slippages else 0,
            events=events[:20], equity_curve=equity,
        )

    def replay_backtest(self, df: pd.DataFrame, symbol: str, signals: list[int]) -> InstitutionalBacktestResult:
        self.replay.load_data(df, symbol)
        ticks = list(self.replay.replay(mode=ReplayMode.INSTANT))
        logger.info("institutional_replay", ticks=len(ticks))
        return self.run(df, symbol, signals)
