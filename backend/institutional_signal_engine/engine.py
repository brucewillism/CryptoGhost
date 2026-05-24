"""CryptoGhost v4 - Institutional Signal Engine."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.investment.context import MarketContext
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.institutional_signal_engine")


@dataclass
class InstitutionalSignal:
    symbol: str
    signal_type: str
    strength: float
    direction: str
    source: str
    details: dict


@dataclass
class InstitutionalAnalysis:
    symbol: str
    signals: list[InstitutionalSignal]
    net_flow_score: float
    accumulation_detected: bool
    whale_activity: bool
    overall_strength: float


class InstitutionalSignalEngine:
    """Detecta fluxo institucional via volume, OI e padrões de mercado."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def analyze(self, ctx: MarketContext) -> InstitutionalAnalysis:
        signals: list[InstitutionalSignal] = []
        df = ctx.df
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)

        vol_ma = volume.tail(20).mean()
        vol_ratio = float(volume.iloc[-1] / max(vol_ma, 1))
        price_change = float(close.pct_change().iloc[-1]) if len(close) > 1 else 0

        if vol_ratio > 2.5:
            direction = "bullish" if price_change > 0 else "bearish"
            signals.append(InstitutionalSignal(
                ctx.symbol, "unusual_volume", min(1.0, vol_ratio / 5), direction, "market_microstructure",
                {"volume_ratio": round(vol_ratio, 2), "price_change_pct": round(price_change * 100, 2)},
            ))

        body = abs(close.iloc[-1] - df["open"].astype(float).iloc[-1])
        range_hl = high.iloc[-1] - low.iloc[-1]
        if range_hl > 0 and body / range_hl < 0.3 and vol_ratio > 1.5:
            signals.append(InstitutionalSignal(
                ctx.symbol, "accumulation_distribution", 0.7, "bullish" if close.iloc[-1] > df["open"].astype(float).iloc[-1] else "bearish",
                "candle_analysis", {"body_ratio": round(body / range_hl, 2)},
            ))

        returns = close.pct_change().dropna()
        if len(returns) > 10:
            z_score = abs(float(returns.iloc[-1] - returns.mean()) / max(returns.std(), 1e-6))
            if z_score > 2.5:
                signals.append(InstitutionalSignal(
                    ctx.symbol, "statistical_anomaly", min(1.0, z_score / 4), "bullish" if returns.iloc[-1] > 0 else "bearish",
                    "statistical", {"z_score": round(z_score, 2)},
                ))

        oi_signal = self._fetch_open_interest_proxy(ctx.symbol, vol_ratio, price_change)
        if oi_signal:
            signals.append(oi_signal)

        whale = vol_ratio > 3 and abs(price_change) > 0.02
        if whale:
            signals.append(InstitutionalSignal(
                ctx.symbol, "whale_movement", min(1.0, vol_ratio / 4), "bullish" if price_change > 0 else "bearish",
                "volume_spike", {"volume_ratio": round(vol_ratio, 2)},
            ))

        if ctx.sentiment.get("whale_movement"):
            signals.append(InstitutionalSignal(
                ctx.symbol, "whale_movement", 0.75, "neutral", "sentiment_engine", {"detected": True},
            ))

        net_flow = sum(s.strength * (1 if s.direction == "bullish" else -1 if s.direction == "bearish" else 0) for s in signals)
        net_flow_norm = max(-1, min(1, net_flow / max(len(signals), 1)))
        accumulation = any(s.signal_type == "accumulation_distribution" and s.direction == "bullish" for s in signals)
        overall = min(1.0, sum(s.strength for s in signals) / max(len(signals), 1)) if signals else 0.3

        return InstitutionalAnalysis(
            symbol=ctx.symbol, signals=signals, net_flow_score=round(net_flow_norm, 4),
            accumulation_detected=accumulation, whale_activity=whale, overall_strength=round(overall, 4),
        )

    def _fetch_open_interest_proxy(self, symbol: str, vol_ratio: float, price_change: float) -> InstitutionalSignal | None:
        try:
            import ccxt
            exchange = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
            if not symbol.replace("/", "").endswith("USDT"):
                return None
            oi_data = exchange.fetch_open_interest(symbol)
            if oi_data and oi_data.get("openInterestAmount"):
                oi = float(oi_data["openInterestAmount"])
                if oi > 0 and vol_ratio > 1.8:
                    return InstitutionalSignal(
                        symbol, "open_interest_surge", min(1.0, vol_ratio / 3),
                        "bullish" if price_change > 0 else "bearish", "binance_futures",
                        {"open_interest": oi},
                    )
        except Exception as exc:
            logger.debug("oi_fetch_skipped", symbol=symbol, error=str(exc))
        return None
