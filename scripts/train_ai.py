#!/usr/bin/env python3
"""CryptoGhost - Script de treinamento de modelos de IA."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from backend.ai_engine.engine import HybridAISignalGenerator
from backend.shared.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger("cryptoghost.train")


def generate_synthetic_data(n: int = 1000) -> pd.DataFrame:
    np.random.seed(42)
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.01)
    return pd.DataFrame(
        {
            "open": prices * 0.999,
            "high": prices * 1.002,
            "low": prices * 0.998,
            "close": prices,
            "volume": np.random.uniform(100, 1000, n),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Treinar modelos CryptoGhost")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--output", default="models/cryptoghost_hybrid.pt")
    args = parser.parse_args()

    logger.info("training_started", symbol=args.symbol)
    df = generate_synthetic_data()
    generator = HybridAISignalGenerator()
    metrics = generator.train_random_forest(df)
    generator.save_model(Path(args.output))

    logger.info("training_complete", metrics=metrics)
    print(f"Treinamento concluído: {metrics}")


if __name__ == "__main__":
    main()
