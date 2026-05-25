"""Tests for SentimentEngineV2 and TradeMemoryService."""

from backend.app.ai.sentiment_v2.engine import SentimentEngineV2
from backend.app.learning.trade_memory.service import TradeMemoryService


def test_sentiment_v2_analyze():
    engine = SentimentEngineV2()
    result = engine.analyze("BTC/USDT")
    assert result.score is not None
    assert result.market_sentiment in ("bullish", "bearish", "neutral")
    assert "legacy" in result.sources


def test_trade_memory_simple_embed():
    svc = TradeMemoryService()
    e1 = svc._simple_embed("test features rsi=50")
    e2 = svc._simple_embed("test features rsi=50")
    e3 = svc._simple_embed("different")
    assert len(e1) == 32
    assert e1 == e2
    assert e1 != e3
