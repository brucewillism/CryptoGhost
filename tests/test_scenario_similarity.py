"""Testes do Scenario Similarity Engine v3."""

from backend.scenario_similarity.engine import ScenarioSimilarityEngine


def test_build_embedding_normalized():
    engine = ScenarioSimilarityEngine()
    state = {"returns_mean": 0.01, "volatility": 0.2, "rsi": 55, "momentum": 2, "volume_ratio": 1.1, "trend_strength": 0.05}
    emb = engine.build_embedding(state)
    assert len(emb) == len(engine.FEATURE_KEYS)
    norm = sum(v * v for v in emb) ** 0.5
    assert abs(norm - 1.0) < 0.01


def test_cosine_similarity_identical():
    engine = ScenarioSimilarityEngine()
    a = [1.0, 0.0, 0.0]
    assert abs(engine._cosine_similarity(a, a) - 1.0) < 0.001


def test_extract_market_state(sample_ohlcv_df):
    engine = ScenarioSimilarityEngine()
    state = engine.extract_market_state(sample_ohlcv_df, {"rsi": 45, "momentum": 1.5, "volume_ratio": 1.2})
    assert "volatility" in state
    assert "returns_mean" in state


def test_find_similar_empty_session():
    engine = ScenarioSimilarityEngine()
    state = {"returns_mean": 0.01, "volatility": 0.2, "rsi": 50, "momentum": 0, "volume_ratio": 1, "trend_strength": 0}

    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self
        def order_by(self, *args):
            return self
        def limit(self, n):
            return self
        def all(self):
            return []

    class FakeSession:
        def query(self, model):
            return FakeQuery()

    result = engine.find_similar(FakeSession(), "BTC/USDT", state)
    assert result.best_match is None
    assert "Sem cenários" in result.summary or result.summary
