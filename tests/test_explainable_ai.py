"""Testes do Explainable AI."""

from backend.explainable_ai.explainer import ExplainableAI


def test_explanation_has_reasons():
    explainer = ExplainableAI()
    result = explainer.explain(
        "BUY",
        0.91,
        {"rsi": 28, "macd": 0.5, "macd_signal": 0.2, "volume_ratio": 2.0, "buy_pressure": 0.65, "momentum": 8},
    )
    assert result.decision == "BUY"
    assert result.confidence == 0.91
    assert len(result.reasons) > 0
    assert "RSI oversold" in result.reasons[0] or any("RSI" in r for r in result.reasons)
    assert result.textual_explanation
    assert result.feature_importance


def test_explanation_never_empty():
    explainer = ExplainableAI()
    result = explainer.explain("HOLD", 0.5, {"rsi": 50})
    assert len(result.reasons) >= 1
    assert "HOLD" in result.textual_explanation
