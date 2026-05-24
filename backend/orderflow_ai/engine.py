"""CryptoGhost v5 - Orderflow AI."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.orderflow_ai")


@dataclass
class OrderflowAnalysis:
    symbol: str
    cumulative_delta: float
    delta_imbalance: float
    absorption_detected: bool
    spoofing_detected: bool
    iceberg_detected: bool
    smart_money_direction: str
    aggressive_buy_pct: float
    aggressive_sell_pct: float
    footprint: dict
    liquidity_imbalance: float


class OrderflowAI:
    """Análise de fluxo institucional: delta, absorção, spoofing."""

    def analyze(self, df: pd.DataFrame, symbol: str, orderbook: dict | None = None) -> OrderflowAnalysis:
        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float)
        open_ = df["open"].astype(float)

        buy_vol = volume * ((close - low) / (high - low + 1e-10)).clip(0, 1)
        sell_vol = volume - buy_vol
        delta = buy_vol - sell_vol
        cum_delta = float(delta.tail(20).sum())
        total_vol = float(volume.tail(20).sum()) or 1
        imbalance = cum_delta / total_vol

        body = (close - open_).abs()
        range_hl = high - low + 1e-10
        small_body = (body / range_hl).tail(5).mean() < 0.25
        high_vol = volume.tail(5).mean() / max(volume.tail(20).mean(), 1) > 1.8
        absorption = bool(small_body and high_vol and abs(imbalance) > 0.15)

        wick_ratio = ((high - pd.concat([close, open_], axis=1).max(axis=1)) + (pd.concat([close, open_], axis=1).min(axis=1) - low)) / range_hl
        spoofing = bool(wick_ratio.tail(3).mean() > 0.6 and volume.tail(3).std() / max(volume.tail(3).mean(), 1) > 0.8)

        vol_std = volume.tail(10).std()
        vol_steps = volume.tail(10).diff().abs()
        iceberg = bool(vol_std > 0 and vol_steps.tail(5).mean() < vol_std * 0.3 and volume.tail(5).mean() > volume.tail(20).mean())

        agg_buy = float(buy_vol.tail(10).sum() / max(volume.tail(10).sum(), 1))
        agg_sell = 1 - agg_buy

        if orderbook:
            bids = orderbook.get("bids", [])[:10]
            asks = orderbook.get("asks", [])[:10]
            bid_depth = sum(b[1] for b in bids) if bids else 0
            ask_depth = sum(a[1] for a in asks) if asks else 0
            liq_imb = (bid_depth - ask_depth) / max(bid_depth + ask_depth, 1)
        else:
            liq_imb = imbalance * 0.5

        direction = "bullish" if imbalance > 0.1 else "bearish" if imbalance < -0.1 else "neutral"

        footprint = {
            "delta_last_5": [round(float(d), 2) for d in delta.tail(5).tolist()],
            "buy_pressure": round(agg_buy, 4),
            "sell_pressure": round(agg_sell, 4),
            "volume_surge": round(float(volume.iloc[-1] / max(volume.tail(20).mean(), 1)), 2),
        }

        return OrderflowAnalysis(
            symbol=symbol, cumulative_delta=round(cum_delta, 2), delta_imbalance=round(imbalance, 4),
            absorption_detected=absorption, spoofing_detected=spoofing, iceberg_detected=iceberg,
            smart_money_direction=direction, aggressive_buy_pct=round(agg_buy, 4),
            aggressive_sell_pct=round(agg_sell, 4), footprint=footprint,
            liquidity_imbalance=round(liq_imb, 4),
        )

    def fetch_orderbook(self, symbol: str) -> dict | None:
        try:
            import ccxt
            ex = ccxt.binance({"enableRateLimit": True})
            return ex.fetch_order_book(symbol, limit=20)
        except Exception as exc:
            logger.debug("orderbook_fetch_failed", symbol=symbol, error=str(exc))
            return None
