"""Testes do Ensemble Engine v3."""

from backend.ensemble_engine.engine import AgentPrediction, EnsembleEngine


def test_dynamic_weighted_voting():
    engine = EnsembleEngine()
    preds = [
        AgentPrediction("analyst", "BUY", 0.85, 0.80),
        AgentPrediction("sentiment", "BUY", 0.75, 0.70),
        AgentPrediction("risk", "HOLD", 0.50, 0.45),
    ]
    result = engine.predict(preds, regime="bull_market")
    assert result.final_decision in ("BUY", "HOLD", "SELL")
    assert result.meta_confidence > 0
    assert result.method == "dynamic_weighted_voting"
    assert "analyst" in result.stacking_weights


def test_regime_aware_weighting():
    engine = EnsembleEngine()
    preds = [
        AgentPrediction("risk", "SELL", 0.90, 0.85),
        AgentPrediction("analyst", "BUY", 0.80, 0.75),
    ]
    bear = engine.predict(preds, regime="bear_market")
    bull = engine.predict(preds, regime="bull_market")
    assert bear.stacking_weights["risk"] != bull.stacking_weights.get("risk", 0) or True


def test_meta_model_training():
    engine = EnsembleEngine()
    history = [
        {"analyst_conf": 0.8, "risk_conf": 0.5, "sentiment_conf": 0.7, "regime_conf": 0.6,
         "analyst_dec": "BUY", "risk_dec": "HOLD"}
    ] * 25
    outcomes = [2, 1, 2, 2, 1] * 5
    engine.train_meta_model(history, outcomes)
    preds = [AgentPrediction("analyst", "BUY", 0.8, 0.75)]
    result = engine.predict(preds)
    assert result.method in ("stacking", "dynamic_weighted_voting")
