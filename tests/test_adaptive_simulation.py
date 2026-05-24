"""Testes do Adaptive Strategy e Simulation Engine v3."""

from backend.adaptive_strategy.engine import AdaptiveStrategyEngine
from backend.simulation_engine.engine import MarketSimulationEngine


def test_adaptive_strategy_bull():
    engine = AdaptiveStrategyEngine()
    result = engine.adapt("bull_market", volatility=30, crash_probability=0.05)
    assert result.regime == "bull_market"
    assert "max_exposure" in result.adjusted or "stop_loss_pct" in result.adjusted


def test_adaptive_strategy_high_volatility():
    engine = AdaptiveStrategyEngine()
    result = engine.adapt("high_volatility", volatility=85, crash_probability=0.3)
    assert result.adjusted["max_exposure_pct"] <= 10


def test_simulation_normal(sample_ohlcv_df):
    sim = MarketSimulationEngine()
    result = sim.simulate_trading(sample_ohlcv_df, "BTC/USDT")
    assert result.total_trades >= 0
    assert result.final_capital > 0


def test_simulation_stress_flash_crash(sample_ohlcv_df):
    sim = MarketSimulationEngine()
    result = sim.simulate_stress_scenario(sample_ohlcv_df, "BTC/USDT", "flash_crash")
    assert result.simulation_type == "stress_flash_crash"
