"""Normalização de dados de mercado — UTC, schema unificado."""

from datetime import UTC, datetime
from typing import Any

import pandas as pd


OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_ohlcv(raw: list[list] | pd.DataFrame, symbol: str = "") -> pd.DataFrame:
    """Converte OHLCV bruto CCXT para DataFrame padronizado UTC."""
    if isinstance(raw, pd.DataFrame):
        df = raw.copy()
    else:
        df = pd.DataFrame(raw, columns=OHLCV_COLUMNS)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True, errors="coerce")
        if df["timestamp"].isna().all():
            df["timestamp"] = pd.to_datetime(df.index, utc=True, errors="coerce")

    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["close"])
    df.attrs["symbol"] = symbol
    df.attrs["normalized_at"] = utc_now().isoformat()
    return df


def normalize_ticker(ticker: dict[str, Any], symbol: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "last": float(ticker.get("last") or ticker.get("close") or 0),
        "bid": float(ticker.get("bid") or 0),
        "ask": float(ticker.get("ask") or 0),
        "volume": float(ticker.get("baseVolume") or ticker.get("volume") or 0),
        "timestamp": utc_now().isoformat(),
    }
