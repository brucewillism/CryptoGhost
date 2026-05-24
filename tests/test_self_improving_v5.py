"""Testes Self-Improving v5."""

import pytest

from backend.ai_truth_engine.engine import AITruthEngine
from backend.drift_detection.engine import DriftDetectionEngine
from backend.meta_learning_engine.engine import MetaLearningEngine
from backend.portfolio_survival.engine import PortfolioSurvivalEngine
from backend.prediction_validation.engine import PredictionValidationEngine
from backend.self_improvement_engine.engine import SelfImprovementEngine
from backend.market_state_intelligence.engine import MarketStateIntelligence
from backend.orderflow_ai.engine import OrderflowAI
from backend.timing_optimization.engine import TimingOptimizationEngine
from backend.institutional_backtesting.engine import InstitutionalBacktestingEngine
from backend.strategy_evolution.engine import StrategyEvolutionEngine
from backend.adaptive_weighting.engine import AdaptiveWeightingEngine
from backend.institutional_data_lake.lake import InstitutionalDataLake


def test_meta_learning_select():
    engine = MetaLearningEngine()
    engine.record_outcome("XGBoost", "bull_market", 0.82, 1.5)
    sel = engine.select_best_model("bull_market")
    assert sel.best_model
    assert sel.market_regime == "bull_market"
    assert 0 <= sel.historical_accuracy <= 1


def test_self_improvement_feedback():
    engine = SelfImprovementEngine()
    actions = engine.process_feedback(0.75, True, False, False)
    assert isinstance(actions, list)
    assert engine.current_weights["analyst"] >= 1.0


def test_prediction_validation(sample_ohlcv_df):
    engine = PredictionValidationEngine()
    result = engine.validate("BTC/USDT", 5.0, 0.75, sample_ohlcv_df)
    assert 0 <= result.validation_score <= 100
    assert isinstance(result.direction_correct, bool)


def test_ai_truth_engine():
    engine = AITruthEngine()
    truth = engine.assess("BTC/USDT", 0.9, 70, 0.6, {"has_forecast": True, "has_orderflow": True})
    assert truth.corrected_confidence <= truth.raw_confidence or truth.overconfidence_detected
    assert 0 <= truth.truth_score <= 1


def test_portfolio_survival_emergency():
    surv = PortfolioSurvivalEngine()
    result = surv.assess(crash_probability=0.8, volatility=90, drawdown_pct=20)
    assert result.mode in ("emergency", "survival", "defensive", "normal")
    assert result.recommended_cash_pct >= 20


def test_drift_detection(sample_ohlcv_df):
    engine = DriftDetectionEngine()
    engine.set_baseline(sample_ohlcv_df, "sideways")
    reports = engine.detect(sample_ohlcv_df, "XGBoost", "bull_market")
    assert len(reports) >= 1


def test_orderflow_analysis(sample_ohlcv_df):
    of = OrderflowAI().analyze(sample_ohlcv_df, "BTC/USDT")
    assert of.symbol == "BTC/USDT"
    assert of.smart_money_direction in ("bullish", "bearish", "neutral")


def test_timing_optimization(sample_ohlcv_df):
    t = TimingOptimizationEngine().optimize(sample_ohlcv_df, "BTC/USDT", "BUY")
    assert t.action in ("enter_now", "wait_pullback", "hold")
    assert 0 <= t.fake_breakout_risk <= 1


def test_market_state_intelligence(sample_ohlcv_df):
    st = MarketStateIntelligence().analyze(sample_ohlcv_df, "ETH/USDT")
    assert st.structural_state
    assert 0 <= st.fragility_score <= 1


def test_institutional_backtesting(sample_ohlcv_df):
    bt = InstitutionalBacktestingEngine().run(sample_ohlcv_df, "BTC/USDT")
    assert bt.final_capital > 0
    assert len(bt.equity_curve) > 0


def test_strategy_evolution(sample_ohlcv_df):
    evo = StrategyEvolutionEngine(population_size=6)
    best = evo.evolve(sample_ohlcv_df, generations=2)
    assert best.parameters
    assert best.fitness_score >= 0


def test_adaptive_weighting():
    w = AdaptiveWeightingEngine().compute("bear_market", {"risk": 0.8}, drawdown_pct=12)
    assert w.weights["risk"] > w.weights.get("analyst", 0)


def test_data_lake_ingest(tmp_path):
    lake = InstitutionalDataLake(root=tmp_path)
    path = lake.ingest("ai_decisions", {"test": True}, "BTC/USDT")
    assert path
    records = lake.query_recent("ai_decisions", "BTC/USDT", 5)
    assert len(records) >= 1
