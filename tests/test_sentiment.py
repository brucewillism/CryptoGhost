"""Testes do Sentiment Engine (lexical fallback)."""

from backend.sentiment_engine.analyzer import SentimentEngine


def test_lexical_bullish():
    engine = SentimentEngine()
    engine._finbert = None
    score, bull, bear = engine._score_text_lexical("Bitcoin surge rally institutional adoption bullish gain")
    assert score > 0.5


def test_lexical_bearish():
    engine = SentimentEngine()
    engine._finbert = None
    score, bull, bear = engine._score_text_lexical("Market crash panic sell regulation ban hack fraud")
    assert score < 0.5
