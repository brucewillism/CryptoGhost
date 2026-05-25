"""Calculadores de features técnicas."""

import numpy as np
import pandas as pd

from backend.market_ai_analyst.indicators import TechnicalIndicators


def compute_all_features(df: pd.DataFrame) -> dict[str, float]:
    """Calcula features reutilizáveis para IA e backtesting."""
    if len(df) < 30:
        return {}

    indicators = TechnicalIndicators.compute(df)
    ind = TechnicalIndicators.to_dict(indicators)
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)
    returns = close.pct_change().dropna()

    # ATR
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1]) if len(tr) >= 14 else 0.0

    # OBV
    obv_dir = np.sign(close.diff()).fillna(0)
    obv = float((obv_dir * volume).cumsum().iloc[-1])

    # Volume delta proxy
    vol_delta = float(volume.iloc[-5:].mean() - volume.iloc[-20:-5].mean()) if len(volume) >= 20 else 0.0

    # Spread proxy from range
    spread = float((high.iloc[-1] - low.iloc[-1]) / close.iloc[-1] * 100) if close.iloc[-1] else 0.0

    # Order imbalance proxy
    up_vol = volume[close > close.shift()].iloc[-20:].sum()
    down_vol = volume[close <= close.shift()].iloc[-20:].sum()
    total = up_vol + down_vol or 1
    order_imbalance = float((up_vol - down_vol) / total)

    volatility = float(returns.std() * np.sqrt(252) * 100) if len(returns) > 5 else 0.0
    momentum = float(close.pct_change(10).iloc[-1] * 100) if len(close) > 10 else 0.0

    sma20 = ind.get("sma_20", close.iloc[-1])
    sma50 = ind.get("sma_50", close.iloc[-1])
    trend_strength = float(abs(close.iloc[-1] - sma20) / close.iloc[-1] * 100) if close.iloc[-1] else 0.0

    if close.iloc[-1] > sma20 > sma50:
        structure = 1.0
    elif close.iloc[-1] < sma20 < sma50:
        structure = -1.0
    else:
        structure = 0.0

    liquidity = min(100.0, float(volume.iloc[-5:].mean() / max(volume.mean(), 1) * 50))

    return {
        **{k: float(v) for k, v in ind.items() if isinstance(v, (int, float, np.floating))},
        "atr": round(atr, 6),
        "obv": round(obv, 2),
        "volume_delta": round(vol_delta, 4),
        "spread_pct": round(spread, 4),
        "order_imbalance": round(order_imbalance, 4),
        "volatility": round(volatility, 4),
        "momentum": round(momentum, 4),
        "trend_strength": round(trend_strength, 4),
        "market_structure": structure,
        "liquidity_score": round(liquidity, 2),
        "close": float(close.iloc[-1]),
    }
