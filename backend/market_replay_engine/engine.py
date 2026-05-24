"""CryptoGhost v3 - Market Replay Engine."""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generator

import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.market_replay_engine")


class ReplayMode(str, Enum):
    REALTIME = "realtime"
    ACCELERATED = "accelerated"
    INSTANT = "instant"


@dataclass
class ReplayTick:
    index: int
    timestamp: object
    open: float
    high: float
    low: float
    close: float
    volume: float
    progress_pct: float


@dataclass
class ReplaySession:
    symbol: str
    total_ticks: int
    mode: ReplayMode
    speed_multiplier: float
    duration_seconds: float


class MarketReplayEngine:
    """Replay histórico tick-by-tick para RL, backtesting e validação."""

    def __init__(self) -> None:
        self._sessions: dict[str, ReplaySession] = {}

    def load_data(self, df: pd.DataFrame, symbol: str) -> int:
        self._data = df.reset_index(drop=True)
        self._symbol = symbol
        return len(self._data)

    def replay(
        self,
        mode: ReplayMode = ReplayMode.ACCELERATED,
        speed: float = 10.0,
        start_idx: int = 0,
        end_idx: int | None = None,
        callback: Callable[[ReplayTick], None] | None = None,
    ) -> Generator[ReplayTick, None, ReplaySession]:
        end = end_idx or len(self._data)
        total = end - start_idx
        start_time = time.perf_counter()

        for i in range(start_idx, end):
            row = self._data.iloc[i]
            tick = ReplayTick(
                index=i,
                timestamp=row.get("timestamp", i),
                open=float(row["open"]), high=float(row["high"]),
                low=float(row["low"]), close=float(row["close"]),
                volume=float(row["volume"]),
                progress_pct=round((i - start_idx) / total * 100, 2),
            )

            if callback:
                callback(tick)
            yield tick

            if mode == ReplayMode.REALTIME:
                time.sleep(1.0)
            elif mode == ReplayMode.ACCELERATED:
                time.sleep(1.0 / speed)

        duration = time.perf_counter() - start_time
        session = ReplaySession(
            symbol=self._symbol, total_ticks=total, mode=mode,
            speed_multiplier=speed, duration_seconds=round(duration, 2),
        )
        self._sessions[self._symbol] = session
        logger.info("replay_complete", symbol=self._symbol, ticks=total, duration=duration)
        return session

    def replay_for_rl(self, df: pd.DataFrame, symbol: str, env_factory: Callable) -> dict:
        self.load_data(df, symbol)
        env = env_factory(df)
        state = env.reset()
        total_reward = 0.0
        ticks = 0

        for tick in self.replay(mode=ReplayMode.INSTANT):
            action = 0
            state, reward, done, _ = env.step(action)
            total_reward += reward
            ticks += 1
            if done:
                break

        return {"total_reward": total_reward, "ticks_processed": ticks}

    def compare_agents_on_replay(self, df: pd.DataFrame, agents: dict[str, Callable]) -> dict:
        results = {}
        for name, agent_fn in agents.items():
            self.load_data(df, "compare")
            rewards = []
            for tick in self.replay(mode=ReplayMode.INSTANT):
                reward = agent_fn(tick)
                rewards.append(reward)
            results[name] = {"total_reward": sum(rewards), "avg_reward": sum(rewards) / max(len(rewards), 1)}
        return results
