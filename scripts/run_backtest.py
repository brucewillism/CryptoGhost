#!/usr/bin/env python3
"""CryptoGhost - Script de backtesting."""

import argparse
import json

import numpy as np
import pandas as pd

from backend.backtesting.engine import BacktestEngine
from backend.shared.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger("cryptoghost.backtest_script")


def load_or_generate_data(path: str | None, n: int = 500) -> pd.DataFrame:
    if path:
        return pd.read_csv(path, parse_dates=["timestamp"] if "timestamp" in pd.read_csv(path, nrows=1).columns else None)
    np.random.seed(42)
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.01)
    return pd.DataFrame(
        {"open": prices * 0.999, "high": prices * 1.002, "low": prices * 0.998, "close": prices, "volume": np.random.uniform(100, 1000, n)}
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtesting CryptoGhost")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--strategy", default="CryptoGhost-Hybrid")
    parser.add_argument("--data", default=None, help="CSV com dados históricos")
    parser.add_argument("--capital", type=float, default=10000)
    args = parser.parse_args()

    from decimal import Decimal

    df = load_or_generate_data(args.data)
    engine = BacktestEngine(initial_capital=Decimal(str(args.capital)))
    result = engine.run(df, args.symbol, args.strategy)
    report = engine.generate_report(result)

    logger.info("backtest_done", report=report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
