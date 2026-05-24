"""CryptoGhost - Macro Analysis."""

import time
from dataclasses import dataclass

import httpx
import numpy as np

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.macro_analysis")

FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"
COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"
FRED_DXY_PROXY = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d"


@dataclass
class MacroIndicator:
    name: str
    value: float
    change_pct: float | None
    impact: str
    metadata: dict


@dataclass
class MacroAnalysisResult:
    indicators: list[MacroIndicator]
    market_outlook: str
    crypto_correlation: str
    confidence: float
    summary: str


class MacroAnalyzer:
    """Análise macroeconômica com dados públicos reais."""

    def analyze(self) -> MacroAnalysisResult:
        start = time.perf_counter()
        indicators = []

        for fetcher in [self._fetch_fear_greed, self._fetch_global_market, self._fetch_dxy_proxy]:
            try:
                indicators.append(fetcher())
            except Exception as exc:
                logger.warning("macro_fetch_failed", fetcher=fetcher.__name__, error=str(exc))

        outlook = self._determine_outlook(indicators)
        correlation = self._assess_crypto_correlation(indicators)
        confidence = min(0.9, 0.5 + len(indicators) * 0.1)
        summary = self._generate_summary(indicators, outlook)

        logger.info("macro_analyzed", indicators=len(indicators), outlook=outlook, elapsed=round(time.perf_counter() - start, 2))

        return MacroAnalysisResult(
            indicators=indicators,
            market_outlook=outlook,
            crypto_correlation=correlation,
            confidence=round(confidence, 2),
            summary=summary,
        )

    @staticmethod
    def _fetch_fear_greed() -> MacroIndicator:
        with httpx.Client(timeout=15) as client:
            r = client.get(FEAR_GREED_URL)
            r.raise_for_status()
            data = r.json()["data"][0]

        value = float(data["value"])
        impact = "bullish" if value > 60 else "bearish" if value < 40 else "neutral"
        return MacroIndicator("fear_greed_index", value, None, impact, {"classification": data.get("value_classification")})

    @staticmethod
    def _fetch_global_market() -> MacroIndicator:
        with httpx.Client(timeout=15) as client:
            r = client.get(COINGECKO_GLOBAL)
            r.raise_for_status()
            data = r.json()["data"]

        total_cap = data["total_market_cap"].get("usd", 0)
        change = data["market_cap_change_percentage_24h_usd"]
        btc_dom = data["market_cap_percentage"].get("btc", 0)

        impact = "bullish" if change > 2 else "bearish" if change < -2 else "neutral"
        return MacroIndicator(
            "total_market_cap", total_cap, change, impact,
            {"btc_dominance": btc_dom, "active_cryptocurrencies": data.get("active_cryptocurrencies")},
        )

    @staticmethod
    def _fetch_dxy_proxy() -> MacroIndicator:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            r = client.get(FRED_DXY_PROXY, headers={"User-Agent": "CryptoGhost/1.0"})
            r.raise_for_status()
            result = r.json()["chart"]["result"][0]

        closes = result["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        value = closes[-1]
        change = ((closes[-1] / closes[0]) - 1) * 100 if len(closes) > 1 else 0

        impact = "bearish" if change > 0.5 else "bullish" if change < -0.5 else "neutral"
        return MacroIndicator("dxy_proxy", value, round(change, 2), impact, {"note": "DXY via Yahoo Finance proxy"})

    @staticmethod
    def _determine_outlook(indicators: list[MacroIndicator]) -> str:
        if not indicators:
            return "uncertain"
        bullish = sum(1 for i in indicators if i.impact == "bullish")
        bearish = sum(1 for i in indicators if i.impact == "bearish")
        if bullish > bearish:
            return "risk_on"
        if bearish > bullish:
            return "risk_off"
        return "mixed"

    @staticmethod
    def _assess_crypto_correlation(indicators: list[MacroIndicator]) -> str:
        dxy = next((i for i in indicators if i.name == "dxy_proxy"), None)
        if dxy and dxy.change_pct and dxy.change_pct > 0.5:
            return "inverse_dxy_pressure"
        fg = next((i for i in indicators if i.name == "fear_greed_index"), None)
        if fg and fg.value > 70:
            return "euphoria_risk"
        return "normal"

    @staticmethod
    def _generate_summary(indicators: list[MacroIndicator], outlook: str) -> str:
        parts = [f"Outlook macro: {outlook}"]
        for ind in indicators:
            parts.append(f"{ind.name}: {ind.value:.2f} ({ind.impact})")
        return ". ".join(parts)
