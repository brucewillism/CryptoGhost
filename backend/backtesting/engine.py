"""CryptoGhost - Sistema de Backtesting."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd

from backend.ai_engine.engine import HybridAISignalGenerator
from backend.risk_management.manager import RiskManager
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.backtesting")


@dataclass
class BacktestTrade:
    timestamp: datetime
    symbol: str
    side: str
    price: Decimal
    quantity: Decimal
    pnl: Decimal = Decimal("0")
    signal_confidence: float = 0.0


@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    initial_capital: Decimal
    final_capital: Decimal
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)


class BacktestEngine:
    """Engine de backtesting com replay e relatórios."""

    def __init__(self, initial_capital: Decimal = Decimal("10000")):
        self.initial_capital = initial_capital
        self.risk_manager = RiskManager(portfolio_value=initial_capital)
        self.signal_generator = HybridAISignalGenerator()

    def run(self, df: pd.DataFrame, symbol: str, strategy_name: str = "CryptoGhost-Hybrid") -> BacktestResult:
        capital = self.initial_capital
        position: dict | None = None
        trades: list[BacktestTrade] = []
        equity_curve = [float(capital)]
        wins = 0

        for i in range(30, len(df)):
            window = df.iloc[: i + 1].copy()
            indicators = self._compute_indicators(window)
            result = self.signal_generator.generate_signal(symbol, window, indicators)
            current_price = Decimal(str(df.iloc[i]["close"]))
            timestamp = df.iloc[i].get("timestamp", datetime.now())

            if position is None and result.signal == "buy" and result.confidence > 0.6:
                can_trade, _ = self.risk_manager.can_open_position(current_price * Decimal("0.1"))
                if can_trade:
                    qty = self.risk_manager.calculate_position_size(current_price)
                    position = {
                        "entry_price": current_price,
                        "quantity": qty,
                        "stop_loss": self.risk_manager.calculate_stop_loss(current_price, "buy"),
                        "take_profit": self.risk_manager.calculate_take_profit(current_price, "buy"),
                    }
                    trades.append(
                        BacktestTrade(timestamp, symbol, "buy", current_price, qty, signal_confidence=result.confidence)
                    )
            elif position is not None:
                entry = position["entry_price"]
                pnl = (current_price - entry) * position["quantity"]
                should_close = (
                    current_price <= position["stop_loss"]
                    or current_price >= position["take_profit"]
                    or (result.signal == "sell" and result.confidence > 0.6)
                )
                if should_close:
                    capital += pnl
                    if pnl > 0:
                        wins += 1
                    trades.append(
                        BacktestTrade(timestamp, symbol, "sell", current_price, position["quantity"], pnl=pnl)
                    )
                    position = None

            equity_curve.append(float(capital))

        total_return = float((capital - self.initial_capital) / self.initial_capital * 100)
        returns = pd.Series(equity_curve).pct_change().dropna()
        sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 1 and returns.std() > 0 else 0
        equity_series = pd.Series(equity_curve)
        drawdown = ((equity_series - equity_series.cummax()) / equity_series.cummax()).min()

        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            initial_capital=self.initial_capital,
            final_capital=capital,
            total_return_pct=round(total_return, 2),
            sharpe_ratio=round(sharpe, 4),
            max_drawdown_pct=round(float(drawdown) * 100, 2),
            win_rate=round(wins / max(len([t for t in trades if t.side == "sell"]), 1) * 100, 2),
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve,
        )

    def generate_report(self, result: BacktestResult) -> dict:
        return {
            "strategy": result.strategy_name,
            "symbol": result.symbol,
            "performance": {
                "initial_capital": float(result.initial_capital),
                "final_capital": float(result.final_capital),
                "total_return_pct": result.total_return_pct,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown_pct": result.max_drawdown_pct,
                "win_rate_pct": result.win_rate,
            },
            "trades_summary": {"total": result.total_trades},
            "recommendation": (
                "Promissora" if result.sharpe_ratio > 1.5 else "Moderada" if result.sharpe_ratio > 0.5 else "Revisar"
            ),
        }

    @staticmethod
    def _compute_indicators(df: pd.DataFrame) -> dict:
        close = df["close"].astype(float)
        if len(close) < 20:
            return {}
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        return {"rsi_14": float(100 - (100 / (1 + rs.iloc[-1])))}

    def compare_ranking_backtest(
        self,
        df: pd.DataFrame,
        symbol: str,
        ranking_signals: list[dict],
    ) -> dict:
        """Compara ranking IA vs retorno real, drawdown e acurácia probabilística."""
        result = self.run(df, symbol, strategy_name="Ranking-IA")
        close = df["close"].astype(float)
        actual_return = float((close.iloc[-1] / close.iloc[30] - 1) * 100) if len(close) > 30 else 0

        predicted_return = ranking_signals[0].get("expected_return", 0) if ranking_signals else 0
        predicted_prob = ranking_signals[0].get("profit_probability", 0.5) if ranking_signals else 0.5
        prediction_error = abs(predicted_return - actual_return)
        direction_correct = (predicted_return > 0 and actual_return > 0) or (predicted_return <= 0 and actual_return <= 0)

        return {
            "symbol": symbol,
            "backtest": self.generate_report(result),
            "ranking_validation": {
                "predicted_return_pct": predicted_return,
                "actual_return_pct": round(actual_return, 2),
                "prediction_error_pct": round(prediction_error, 2),
                "direction_correct": direction_correct,
                "predicted_profit_probability": predicted_prob,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown_pct": result.max_drawdown_pct,
                "ranking_accuracy_score": round(max(0, 100 - prediction_error * 2), 2),
            },
        }
