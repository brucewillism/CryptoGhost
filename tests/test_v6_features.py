"""Tests for v6 feature calculators."""

import pandas as pd

from backend.app.features.calculators.technical import compute_all_features


def test_compute_all_features(sample_ohlcv_df):
    features = compute_all_features(sample_ohlcv_df)
    assert "rsi" in features or "close" in features
    assert "volatility" in features
    assert "liquidity_score" in features
    assert features["close"] > 0


def test_compute_insufficient_data():
    df = pd.DataFrame({"open": [1], "high": [1], "low": [1], "close": [1], "volume": [1]})
    assert compute_all_features(df) == {}
