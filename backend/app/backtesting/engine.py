"""Backtesting Engine v6 — walk-forward + Monte Carlo."""

import uuid
from dataclasses import asdict

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.backtesting.metrics import BacktestMetrics, compute_metrics
from backend.app.backtesting.simulator import BacktestSimulator
from backend.app.data.collectors.binance_collector import BinanceCollector
from backend.app.features.calculators.technical import compute_all_features
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.models_v6 import BacktestRunRecord, BacktestTradeRecord

logger = get_logger("cryptoghost.v6.backtesting")


class BacktestEngineV6:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.collector = BinanceCollector()
        self.simulator = BacktestSimulator()

    async def run(
        self,
        session: AsyncSession,
        symbols: list[str],
        name: str = "default",
        initial_capital: float = 10000.0,
        min_score: float = 60.0,
    ) -> dict:
        all_pnls: list[float] = []
        all_returns: list[float] = []
        trades: list[dict] = []
        exposure_bars = 0
        total_bars = 0

        for symbol in symbols:
            df = self.collector.fetch_ohlcv(symbol, limit=500)
            total_bars += len(df)
            for i in range(50, len(df) - 1, 24):
                window = df.iloc[: i + 1]
                features = compute_all_features(window)
                score = features.get("momentum", 0) + features.get("trend_strength", 0)
                if score >= min_score:
                    entry = float(window["close"].iloc[-1])
                    exit_p = float(df["close"].iloc[i + 1])
                    pnl_pct = (exit_p - entry) / entry * 100
                    fill = self.simulator.simulate_market_buy(
                        __import__("decimal").Decimal(str(entry)),
                        __import__("decimal").Decimal("0.01"),
                        features.get("liquidity_score", 50),
                    )
                    net_pnl = pnl_pct - float(fill.fees) * 100
                    all_pnls.append(net_pnl)
                    all_returns.append(net_pnl / 100)
                    exposure_bars += 1
                    trades.append({"symbol": symbol, "entry": entry, "exit": exit_p, "pnl": net_pnl})

        metrics = compute_metrics(all_returns, all_pnls, exposure_bars, total_bars)
        mc = self._monte_carlo(all_returns)

        run_id = uuid.uuid4()
        session.add(BacktestRunRecord(
            id=run_id,
            name=name,
            symbols=symbols,
            config={"initial_capital": initial_capital, "min_score": min_score},
            metrics={**asdict(metrics), "monte_carlo": mc},
        ))
        for t in trades[:100]:
            session.add(BacktestTradeRecord(
                run_id=run_id,
                symbol=t["symbol"],
                side="buy",
                entry_price=t["entry"],
                exit_price=t["exit"],
                pnl=t["pnl"],
            ))

        logger.info("backtest_complete", name=name, trades=len(trades), sharpe=metrics.sharpe_ratio)
        return {"run_id": str(run_id), "metrics": asdict(metrics), "monte_carlo": mc, "trades_count": len(trades)}

    def _monte_carlo(self, returns: list[float], simulations: int | None = None) -> dict:
        sims = simulations or self.settings.monte_carlo_simulations
        if not returns:
            return {"p5": 0, "p50": 0, "p95": 0}
        arr = np.array(returns)
        outcomes = []
        for _ in range(min(sims, 500)):
            sample = np.random.choice(arr, size=len(arr), replace=True)
            outcomes.append(float(np.prod(1 + sample) - 1) * 100)
        outcomes.sort()
        n = len(outcomes)
        return {
            "p5": round(outcomes[int(n * 0.05)], 2),
            "p50": round(outcomes[int(n * 0.5)], 2),
            "p95": round(outcomes[int(n * 0.95)], 2),
        }

    async def walk_forward(
        self,
        session: AsyncSession,
        symbol: str,
        train_bars: int = 200,
        test_bars: int = 50,
    ) -> list[dict]:
        df = self.collector.fetch_ohlcv(symbol, limit=800)
        results = []
        for start in range(0, len(df) - train_bars - test_bars, test_bars):
            train = df.iloc[start : start + train_bars]
            test = df.iloc[start + train_bars : start + train_bars + test_bars]
            train_feats = compute_all_features(train)
            threshold = train_feats.get("momentum", 0) + train_feats.get("trend_strength", 0)
            pnls = []
            for j in range(len(test) - 1):
                if threshold >= 5:
                    entry = float(test["close"].iloc[j])
                    exit_p = float(test["close"].iloc[j + 1])
                    pnls.append((exit_p - entry) / entry * 100)
            metrics = compute_metrics([p / 100 for p in pnls], pnls, len(pnls), len(test))
            results.append({"window": start, "metrics": asdict(metrics)})
        return results
