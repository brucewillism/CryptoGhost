"""CryptoGhost - Market AI Analyst."""

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.data_collector.collector import ExchangeConnector
from backend.market_ai_analyst.indicators import TechnicalIndicators
from backend.shared.logging_config import get_logger
from backend.shared.metrics import AI_CONFIDENCE_GAUGE, AI_LATENCY, AI_PREDICTIONS_TOTAL

logger = get_logger("cryptoghost.market_ai_analyst")


@dataclass
class AssetAnalysis:
    symbol: str
    score: int
    trend: str
    risk: str
    confidence: float
    recommendation: str
    strength_score: float
    reversal_probability: float
    indicators: dict
    momentum: float
    volatility: float
    liquidity_score: float
    buy_pressure: float
    sell_pressure: float


class MarketAIAnalyst:
    """Analisa ativos com indicadores técnicos, estatísticos e scoring inteligente."""

    def __init__(self, exchange: str = "binance"):
        self.connector = ExchangeConnector(exchange)

    def fetch_ohlcv_dataframe(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> pd.DataFrame:
        ohlcv = self.connector.fetch_ohlcv(symbol, timeframe, limit)
        return pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])

    def analyze(self, symbol: str, df: pd.DataFrame | None = None) -> AssetAnalysis:
        start = time.perf_counter()
        if df is None:
            df = self.fetch_ohlcv_dataframe(symbol)

        if len(df) < 30:
            raise ValueError(f"Dados insuficientes para {symbol}: {len(df)} candles")

        indicators = TechnicalIndicators.compute(df)
        ind_dict = TechnicalIndicators.to_dict(indicators)
        close = df["close"].astype(float)
        returns = close.pct_change().dropna()
        volatility = float(returns.std() * np.sqrt(252) * 100)

        order_book = self.connector.fetch_order_book(symbol, limit=20)
        bid_vol = sum(b[1] for b in order_book.get("bids", [])[:10])
        ask_vol = sum(a[1] for a in order_book.get("asks", [])[:10])
        total_vol = bid_vol + ask_vol or 1
        buy_pressure = bid_vol / total_vol
        sell_pressure = ask_vol / total_vol
        liquidity_score = min(100, total_vol / 10)

        score_components = []
        if indicators.rsi < 35:
            score_components.append(15)
        elif indicators.rsi > 65:
            score_components.append(-10)
        else:
            score_components.append(5)

        if indicators.macd > indicators.macd_signal:
            score_components.append(20)
        else:
            score_components.append(-5)

        if close.iloc[-1] > indicators.sma_20 > indicators.sma_50:
            score_components.append(20)
        elif close.iloc[-1] < indicators.sma_20 < indicators.sma_50:
            score_components.append(-15)

        if buy_pressure > 0.55:
            score_components.append(10)
        elif sell_pressure > 0.55:
            score_components.append(-10)

        if indicators.volume_ratio > 1.5:
            score_components.append(10)

        if close.iloc[-1] > indicators.vwap:
            score_components.append(5)

        raw_score = 50 + sum(score_components)
        score = int(max(0, min(100, raw_score)))
        strength_score = float(abs(score - 50) * 2)

        if score >= 65:
            trend = "bullish"
        elif score <= 35:
            trend = "bearish"
        else:
            trend = "neutral"

        if volatility > 80:
            risk = "high"
        elif volatility > 40:
            risk = "medium"
        else:
            risk = "low"

        reversal_signals = 0
        if indicators.rsi < 30 or indicators.rsi > 70:
            reversal_signals += 1
        if abs(close.iloc[-1] - indicators.bb_upper) / close.iloc[-1] < 0.005:
            reversal_signals += 1
        if abs(close.iloc[-1] - indicators.bb_lower) / close.iloc[-1] < 0.005:
            reversal_signals += 1
        reversal_probability = min(0.9, reversal_signals * 0.3 + (volatility / 200))

        confidence = min(0.95, 0.5 + strength_score / 200 + liquidity_score / 500)

        if score >= 75:
            recommendation = "strong_buy"
        elif score >= 60:
            recommendation = "moderate_buy"
        elif score <= 25:
            recommendation = "strong_sell"
        elif score <= 40:
            recommendation = "moderate_sell"
        else:
            recommendation = "hold"

        elapsed = time.perf_counter() - start
        AI_LATENCY.labels(agent="market_analyst").observe(elapsed)
        AI_CONFIDENCE_GAUGE.labels(agent="market_analyst").set(confidence)
        AI_PREDICTIONS_TOTAL.labels(agent="market_analyst", symbol=symbol, decision=recommendation).inc()

        logger.info("asset_analyzed", symbol=symbol, score=score, trend=trend, confidence=confidence)

        return AssetAnalysis(
            symbol=symbol,
            score=score,
            trend=trend,
            risk=risk,
            confidence=round(confidence, 2),
            recommendation=recommendation,
            strength_score=round(strength_score, 2),
            reversal_probability=round(reversal_probability, 2),
            indicators=ind_dict,
            momentum=indicators.momentum,
            volatility=round(volatility, 2),
            liquidity_score=round(liquidity_score, 2),
            buy_pressure=round(buy_pressure, 3),
            sell_pressure=round(sell_pressure, 3),
        )

    def analyze_multiple(self, symbols: list[str]) -> list[AssetAnalysis]:
        results = []
        for symbol in symbols:
            try:
                results.append(self.analyze(symbol))
            except Exception as exc:
                logger.error("analysis_failed", symbol=symbol, error=str(exc))
        return results
