"""Testes do Reinforcement Learning Engine v3."""

import pandas as pd

from backend.reinforcement_learning.engine import RLEngine, TradingEnvironment, TradingEnvConfig


def test_trading_environment_reset_and_step(sample_ohlcv_df):
    env = TradingEnvironment(sample_ohlcv_df)
    obs = env.reset()
    assert len(obs) == env.observation_space_size
    next_obs, reward, done, info = env.step(0)
    assert len(next_obs) == env.observation_space_size
    assert isinstance(reward, float)
    assert isinstance(done, bool)


def test_trading_environment_buy_sell(sample_ohlcv_df):
    env = TradingEnvironment(sample_ohlcv_df, TradingEnvConfig(initial_balance=10000))
    env.reset()
    env.step(1)
    assert env.position > 0
    _, reward, _, info = env.step(2)
    assert env.position == 0
    assert env.balance > 0


def test_dqn_training_short(sample_ohlcv_df):
    engine = RLEngine()
    result = engine.train_dqn(sample_ohlcv_df, episodes=3, symbol="TEST/USDT")
    assert result.algorithm == "DQN"
    assert result.episodes == 3
    assert result.checkpoint_path.endswith(".pt")


def test_ppo_training_short(sample_ohlcv_df):
    engine = RLEngine()
    result = engine.train_ppo(sample_ohlcv_df, episodes=2, symbol="TEST/USDT")
    assert result.algorithm == "PPO"
    assert result.avg_reward is not None


def test_sac_training_short(sample_ohlcv_df):
    engine = RLEngine()
    result = engine.train_sac(sample_ohlcv_df, episodes=2, symbol="TEST/USDT")
    assert result.algorithm == "SAC"
    assert "rewards" in result.metrics or result.total_reward is not None
