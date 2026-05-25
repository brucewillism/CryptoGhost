"""SentimentEngineV2 — FinBERT + agregação multi-fonte."""

from dataclasses import dataclass

from backend.app.data.providers.premium import CryptoPanicProvider, FearGreedProvider
from backend.sentiment_engine.analyzer import SentimentEngine
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.v6.sentiment")


@dataclass
class SentimentV2Result:
    score: float
    confidence: float
    market_sentiment: str
    sources: dict
    news_impact: float
    method: str


class SentimentEngineV2:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.legacy = SentimentEngine()
        self.fear_greed = FearGreedProvider()
        self.cryptopanic = CryptoPanicProvider()

    def analyze(self, symbol: str) -> SentimentV2Result:
        legacy = self.legacy.analyze(symbol)
        fg = self.fear_greed.fetch(symbol)
        cp = self.cryptopanic.fetch(symbol)

        scores = [legacy.score, fg.get("score", 0), cp.get("score", 0)]
        weights = [0.5, 0.2, 0.3]
        combined = sum(s * w for s, w in zip(scores, weights))
        confidence = min(0.95, legacy.confidence * 0.6 + 0.4 * (1 - abs(combined - legacy.score)))

        if combined > 0.2:
            sentiment = "bullish"
        elif combined < -0.2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        method = "finbert" if self.legacy._finbert else "lexical"
        if cp.get("count", 0) > 0:
            method = f"{method}+cryptopanic"

        return SentimentV2Result(
            score=round(combined, 4),
            confidence=round(confidence, 4),
            market_sentiment=sentiment,
            sources={"legacy": legacy.score, "fear_greed": fg, "cryptopanic": cp},
            news_impact=round(abs(cp.get("score", 0)), 4),
            method=method,
        )
