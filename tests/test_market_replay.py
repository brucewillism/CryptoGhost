"""Testes do Market Replay Engine v3."""

from backend.market_replay_engine.engine import MarketReplayEngine, ReplayMode


def test_replay_accelerated(sample_ohlcv_df):
    engine = MarketReplayEngine()
    count = engine.load_data(sample_ohlcv_df, "BTC/USDT")
    assert count == len(sample_ohlcv_df)

    ticks = list(engine.replay(mode=ReplayMode.INSTANT, start_idx=0, end_idx=10))
    assert len(ticks) == 10
    assert ticks[0].close > 0
    assert ticks[-1].progress_pct > 0


def test_replay_callback(sample_ohlcv_df):
    engine = MarketReplayEngine()
    engine.load_data(sample_ohlcv_df, "ETH/USDT")
    collected = []

    for tick in engine.replay(mode=ReplayMode.INSTANT, end_idx=5, callback=lambda t: collected.append(t.index)):
        pass

    assert collected == [0, 1, 2, 3, 4]
