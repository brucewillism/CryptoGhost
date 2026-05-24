"""Testes de priorização de investimentos v4."""

import pytest

from backend.investment.context import MarketContext
from backend.opportunity_scoring.engine import OpportunityScoringEngine
from backend.predictive_profit_engine.engine import PredictiveProfitEngine
from backend.probabilistic_analysis.engine import ProbabilisticAnalysisEngine
from backend.profit_probability_engine.engine import ProfitProbabilityEngine
from backend.risk_reward_optimizer.engine import RiskRewardOptimizer
from backend.investment_prioritizer.engine import InvestmentPrioritizer
from backend.alpha_detection.engine import AlphaDetectionEngine
from backend.capital_allocator.engine import CapitalAllocator
from backend.smart_asset_ranking.engine import SmartAssetRankingEngine
from backend.ai_router.router import HybridAIRouter, TaskComplexity


def _ctx(sample_ohlcv_df) -> MarketContext:
    return MarketContext(
        symbol="BTC/USDT",
        df=sample_ohlcv_df,
        analysis={"score": 72, "volatility": 45, "momentum": 8, "strength_score": 68, "indicators": {"rsi": 58, "volume_ratio": 1.4}},
        sentiment={"score": 0.4, "market_sentiment": "bullish"},
        risk={"crash_probability": 0.15, "instability_score": 30, "overall_risk": "medium"},
        regime={"regime": "bull_market", "confidence": 0.7},
        consensus={"final_decision": "BUY", "confidence": 0.75},
        explanation={"reasons": ["Momentum"]},
        calibrated_confidence=0.78,
        liquidity_score=0.7,
    )


def test_opportunity_scoring(sample_ohlcv_df):
    engine = OpportunityScoringEngine()
    result = engine.score(_ctx(sample_ohlcv_df), institutional_strength=0.6)
    assert 0 <= result.opportunity_score <= 100
    assert result.classification in ("institutional_opportunity", "strong_buy", "moderate_buy", "neutral", "avoid")


def test_predictive_profit_monte_carlo(sample_ohlcv_df):
    engine = PredictiveProfitEngine(simulations=500)
    result = engine.forecast(_ctx(sample_ohlcv_df))
    assert result.method == "monte_carlo"
    assert "p5" in result.confidence_interval
    assert result.upside_downside_ratio >= 0


def test_probabilistic_analysis(sample_ohlcv_df):
    engine = ProbabilisticAnalysisEngine()
    result = engine.analyze(_ctx(sample_ohlcv_df))
    total = result.bullish_probability + result.bearish_probability + result.sideways_probability
    assert abs(total - 1.0) < 0.01
    assert result.bullish_probability > result.bearish_probability


def test_profit_probability_pipeline(sample_ohlcv_df):
    ctx = _ctx(sample_ohlcv_df)
    opp = OpportunityScoringEngine().score(ctx)
    forecast = PredictiveProfitEngine(simulations=200).forecast(ctx)
    prob = ProbabilisticAnalysisEngine().analyze(ctx)
    result = ProfitProbabilityEngine().calculate(ctx, prob, forecast, opp)
    assert 0 < result.profit_probability < 1
    assert result.confidence > 0


def test_risk_reward_optimizer(sample_ohlcv_df):
    ctx = _ctx(sample_ohlcv_df)
    forecast = PredictiveProfitEngine(simulations=200).forecast(ctx)
    prob = ProbabilisticAnalysisEngine().analyze(ctx)
    opp = OpportunityScoringEngine().score(ctx)
    pp = ProfitProbabilityEngine().calculate(ctx, prob, forecast, opp)
    rr = RiskRewardOptimizer().assess(ctx, forecast, pp)
    assert rr.sharpe_ratio is not None
    assert isinstance(rr.approved, bool)


def test_investment_prioritizer(sample_ohlcv_df):
    ctx = _ctx(sample_ohlcv_df)
    p = InvestmentPrioritizer().prioritize(ctx, 80, 12.5, 0.72, 65, 55, True, 0.6)
    assert p.priority_score > 0
    assert p.recommendation in ("HIGH_PRIORITY_BUY", "STRONG_BUY", "MODERATE_BUY", "WATCH", "AVOID")
    assert len(p.reasons) > 0


def test_alpha_detection(sample_ohlcv_df):
    result = AlphaDetectionEngine().detect(_ctx(sample_ohlcv_df), market_avg_score=50)
    assert 0 <= result.alpha_score <= 100
    assert result.alpha_type


def test_capital_allocator():
    ranked = [
        {"symbol": "BTC/USDT", "priority_score": 90, "confidence": 0.85, "profit_probability": 0.7, "approved": True, "expected_return": 15},
        {"symbol": "ETH/USDT", "priority_score": 75, "confidence": 0.7, "profit_probability": 0.6, "approved": True, "expected_return": 10},
    ]
    alloc = CapitalAllocator().allocate(ranked, "bull_market")
    assert "Cash" in alloc.allocations
    assert alloc.cash_pct >= 20
    assert sum(alloc.allocations.values()) == pytest.approx(100, abs=1)


def test_smart_asset_ranking():
    assets = [
        {"symbol": "BTC/USDT", "priority_score": 90, "opportunity_score": 85, "profit_probability": 0.8, "risk_reward_score": 70, "alpha_score": 60, "confidence": 0.85, "risk_score": 30, "expected_return": 15, "recommendation": "HIGH_PRIORITY_BUY", "approved": True, "liquidity_score": 0.8},
        {"symbol": "ETH/USDT", "priority_score": 70, "opportunity_score": 65, "profit_probability": 0.6, "risk_reward_score": 55, "alpha_score": 40, "confidence": 0.7, "risk_score": 40, "expected_return": 8, "recommendation": "MODERATE_BUY", "approved": True, "liquidity_score": 0.7},
    ]
    ranked = SmartAssetRankingEngine().rank(assets)
    assert ranked[0].rank == 1
    assert ranked[0].symbol == "BTC/USDT"


def test_hybrid_ai_router_local():
    router = HybridAIRouter()
    decision = router.route(TaskComplexity.FAST)
    assert decision.provider == "ollama"
    assert not decision.use_premium or decision.provider in ("openai", "anthropic", "gemini")
