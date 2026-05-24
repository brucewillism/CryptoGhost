"""CryptoGhost v3 - Reinforcement Learning Engine."""

import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.reinforcement_learning")

ACTIONS = ["hold", "buy", "sell"]
CHECKPOINT_DIR = Path("models/rl")


@dataclass
class TradingEnvConfig:
    initial_balance: float = 10000.0
    slippage_pct: float = 0.0005
    spread_pct: float = 0.0002
    latency_steps: int = 1
    market_impact_pct: float = 0.0001
    max_position_pct: float = 0.1
    commission_pct: float = 0.001


class TradingEnvironment:
    """Ambiente estilo OpenAI Gym com microestrutura realista."""

    def __init__(self, df: pd.DataFrame, config: TradingEnvConfig | None = None):
        self.df = df.reset_index(drop=True)
        self.config = config or TradingEnvConfig()
        self.reset()

    @property
    def observation_space_size(self) -> int:
        return 8

    @property
    def action_space_size(self) -> int:
        return 3

    def reset(self) -> np.ndarray:
        self.step_idx = 30
        self.balance = self.config.initial_balance
        self.position = 0.0
        self.entry_price = 0.0
        self.total_reward = 0.0
        self.trade_count = 0
        return self._get_obs()

    def _get_obs(self) -> np.ndarray:
        row = self.df.iloc[self.step_idx]
        close = float(row["close"])
        returns = self.df["close"].pct_change().iloc[max(0, self.step_idx - 20):self.step_idx + 1]
        vol = float(returns.std()) if len(returns) > 1 else 0.01
        volume = float(row["volume"])
        vol_ma = float(self.df["volume"].iloc[max(0, self.step_idx - 20):self.step_idx + 1].mean())

        return np.array([
            close / 100000, vol * 100, volume / max(vol_ma, 1),
            self.position / max(self.balance, 1), self.balance / self.config.initial_balance,
            float(returns.iloc[-1]) if len(returns) > 0 else 0,
            self.config.spread_pct * 1000, self.trade_count / 100,
        ], dtype=np.float32)

    def step(self, action: int) -> tuple[np.ndarray, float, bool, dict]:
        price = float(self.df.iloc[self.step_idx]["close"])
        spread_cost = price * self.config.spread_pct
        slippage = price * self.config.slippage_pct
        impact = price * self.config.market_impact_pct * abs(action - 1)
        exec_price = price + spread_cost + slippage + impact

        reward = 0.0
        info: dict[str, Any] = {}

        if action == 1 and self.position == 0:
            max_qty = (self.balance * self.config.max_position_pct) / exec_price
            cost = max_qty * exec_price * (1 + self.config.commission_pct)
            if cost <= self.balance:
                self.position = max_qty
                self.entry_price = exec_price
                self.balance -= cost
                self.trade_count += 1
                reward -= self.config.commission_pct * 10

        elif action == 2 and self.position > 0:
            proceeds = self.position * exec_price * (1 - self.config.commission_pct)
            pnl = proceeds - self.position * self.entry_price
            reward = pnl / self.config.initial_balance * 100
            self.balance += proceeds
            info["pnl"] = pnl
            self.position = 0
            self.entry_price = 0
            self.trade_count += 1

        elif action == 0 and self.position > 0:
            unrealized = self.position * (price - self.entry_price)
            reward = unrealized / self.config.initial_balance * 0.1

        if self.position > 0:
            unrealized = self.position * (price - self.entry_price)
            reward += unrealized / self.config.initial_balance * 0.01

        self.step_idx += 1
        self.total_reward += reward
        done = self.step_idx >= len(self.df) - 1

        return self._get_obs(), reward, done, info


class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.buffer: deque = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done) -> None:
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> list:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self) -> int:
        return len(self.buffer)


class DQNetwork(nn.Module):
    def __init__(self, state_size: int, action_size: int, hidden: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, action_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class PPOAgent:
    """Proximal Policy Optimization simplificado."""

    def __init__(self, state_size: int, action_size: int = 3, lr: float = 3e-4):
        self.policy = nn.Sequential(
            nn.Linear(state_size, 128), nn.Tanh(),
            nn.Linear(128, 128), nn.Tanh(),
            nn.Linear(128, action_size), nn.Softmax(dim=-1),
        )
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy.to(self.device)

    def select_action(self, state: np.ndarray) -> tuple[int, float]:
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        probs = self.policy(state_t).detach().cpu().numpy()[0]
        action = int(np.random.choice(len(probs), p=probs))
        return action, float(probs[action])

    def update(self, states, actions, rewards, clip_eps: float = 0.2) -> float:
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        probs = self.policy(states_t)
        selected = probs.gather(1, actions_t.unsqueeze(1)).squeeze()
        loss = -(torch.log(selected + 1e-8) * rewards_t).mean()
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return float(loss.item())

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.policy.state_dict(), path)


class DQNAgent:
    def __init__(self, state_size: int, action_size: int = 3, lr: float = 1e-3, gamma: float = 0.99):
        self.gamma = gamma
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.q_net = DQNetwork(state_size, action_size).to(self.device)
        self.target_net = DQNetwork(state_size, action_size).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.replay = ReplayBuffer()
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995

    def select_action(self, state: np.ndarray) -> int:
        if random.random() < self.epsilon:
            return random.randint(0, 2)
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            return int(self.q_net(state_t).argmax().item())

    def train_step(self, batch_size: int = 64) -> float | None:
        if len(self.replay) < batch_size:
            return None
        batch = self.replay.sample(batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states_t = torch.FloatTensor(np.array(states)).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        next_states_t = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones_t = torch.FloatTensor(dones).to(self.device)

        q_values = self.q_net(states_t).gather(1, actions_t.unsqueeze(1)).squeeze()
        with torch.no_grad():
            next_q = self.target_net(next_states_t).max(1)[0]
            targets = rewards_t + self.gamma * next_q * (1 - dones_t)

        loss = nn.functional.mse_loss(q_values, targets)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return float(loss.item())

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"q_net": self.q_net.state_dict(), "epsilon": self.epsilon}, path)


class SACActor(nn.Module):
    def __init__(self, state_size: int, action_size: int, hidden: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, action_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.net(x), dim=-1)


class SACAgent:
    """Soft Actor-Critic para ações discretas com entropy regularization."""

    def __init__(
        self,
        state_size: int,
        action_size: int = 3,
        lr: float = 3e-4,
        gamma: float = 0.99,
        alpha: float = 0.2,
    ):
        self.gamma = gamma
        self.alpha = alpha
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.actor = SACActor(state_size, action_size).to(self.device)
        self.critic1 = DQNetwork(state_size, action_size).to(self.device)
        self.critic2 = DQNetwork(state_size, action_size).to(self.device)
        self.target_critic1 = DQNetwork(state_size, action_size).to(self.device)
        self.target_critic2 = DQNetwork(state_size, action_size).to(self.device)
        self.target_critic1.load_state_dict(self.critic1.state_dict())
        self.target_critic2.load_state_dict(self.critic2.state_dict())
        self.actor_opt = optim.Adam(self.actor.parameters(), lr=lr)
        self.critic_opt = optim.Adam(
            list(self.critic1.parameters()) + list(self.critic2.parameters()), lr=lr
        )
        self.replay = ReplayBuffer()

    def select_action(self, state: np.ndarray) -> tuple[int, float]:
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probs = self.actor(state_t).cpu().numpy()[0]
        action = int(np.random.choice(len(probs), p=probs))
        return action, float(probs[action])

    def train_step(self, batch_size: int = 64, tau: float = 0.005) -> float | None:
        if len(self.replay) < batch_size:
            return None

        batch = self.replay.sample(batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        states_t = torch.FloatTensor(np.array(states)).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        next_states_t = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones_t = torch.FloatTensor(dones).to(self.device)

        with torch.no_grad():
            next_probs = self.actor(next_states_t)
            next_log_probs = torch.log(next_probs + 1e-8)
            target_q1 = self.target_critic1(next_states_t)
            target_q2 = self.target_critic2(next_states_t)
            min_target_q = torch.min(target_q1, target_q2)
            next_value = (next_probs * (min_target_q - self.alpha * next_log_probs)).sum(dim=1)
            targets = rewards_t + self.gamma * next_value * (1 - dones_t)

        q1 = self.critic1(states_t).gather(1, actions_t.unsqueeze(1)).squeeze()
        q2 = self.critic2(states_t).gather(1, actions_t.unsqueeze(1)).squeeze()
        critic_loss = nn.functional.mse_loss(q1, targets) + nn.functional.mse_loss(q2, targets)

        self.critic_opt.zero_grad()
        critic_loss.backward()
        self.critic_opt.step()

        probs = self.actor(states_t)
        log_probs = torch.log(probs + 1e-8)
        q1_pi = self.critic1(states_t)
        q2_pi = self.critic2(states_t)
        min_q_pi = torch.min(q1_pi, q2_pi)
        actor_loss = (probs * (self.alpha * log_probs - min_q_pi)).sum(dim=1).mean()

        self.actor_opt.zero_grad()
        actor_loss.backward()
        self.actor_opt.step()

        for target, source in (
            (self.target_critic1, self.critic1),
            (self.target_critic2, self.critic2),
        ):
            for tp, sp in zip(target.parameters(), source.parameters()):
                tp.data.copy_(tau * sp.data + (1 - tau) * tp.data)

        return float(critic_loss.item() + actor_loss.item())

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "actor": self.actor.state_dict(),
                "critic1": self.critic1.state_dict(),
                "critic2": self.critic2.state_dict(),
            },
            path,
        )


@dataclass
class RLTrainingResult:
    algorithm: str
    total_reward: float
    episodes: int
    avg_reward: float
    checkpoint_path: str
    metrics: dict = field(default_factory=dict)


class RLEngine:
    """Engine de RL com DQN, PPO e SAC."""

    def train_dqn(self, df: pd.DataFrame, episodes: int = 50, symbol: str = "BTC/USDT") -> RLTrainingResult:
        env = TradingEnvironment(df)
        agent = DQNAgent(env.observation_space_size)
        rewards_history = []

        for ep in range(episodes):
            state = env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                action = agent.select_action(state)
                next_state, reward, done, _ = env.step(action)
                agent.replay.push(state, action, reward, next_state, float(done))
                agent.train_step()
                state = next_state
                ep_reward += reward
            rewards_history.append(ep_reward)

            if ep % 10 == 0:
                agent.target_net.load_state_dict(agent.q_net.state_dict())

        path = CHECKPOINT_DIR / f"dqn_{symbol.replace('/', '_')}.pt"
        agent.save(path)
        logger.info("dqn_trained", episodes=episodes, total_reward=sum(rewards_history))

        return RLTrainingResult(
            algorithm="DQN", total_reward=sum(rewards_history), episodes=episodes,
            avg_reward=float(np.mean(rewards_history)), checkpoint_path=str(path),
            metrics={"rewards": rewards_history[-10:]},
        )

    def train_ppo(self, df: pd.DataFrame, episodes: int = 30, symbol: str = "BTC/USDT") -> RLTrainingResult:
        env = TradingEnvironment(df)
        agent = PPOAgent(env.observation_space_size)
        rewards_history = []

        for ep in range(episodes):
            state = env.reset()
            states, actions, rewards = [], [], []
            done = False
            while not done:
                action, _ = agent.select_action(state)
                next_state, reward, done, _ = env.step(action)
                states.append(state)
                actions.append(action)
                rewards.append(reward)
                state = next_state

            agent.update(states, actions, rewards)
            rewards_history.append(sum(rewards))

        path = CHECKPOINT_DIR / f"ppo_{symbol.replace('/', '_')}.pt"
        agent.save(path)

        return RLTrainingResult(
            algorithm="PPO", total_reward=sum(rewards_history), episodes=episodes,
            avg_reward=float(np.mean(rewards_history)), checkpoint_path=str(path),
        )

    def train_sac(self, df: pd.DataFrame, episodes: int = 40, symbol: str = "BTC/USDT") -> RLTrainingResult:
        env = TradingEnvironment(df)
        agent = SACAgent(env.observation_space_size)
        rewards_history = []

        for _ in range(episodes):
            state = env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                action, _ = agent.select_action(state)
                next_state, reward, done, _ = env.step(action)
                agent.replay.push(state, action, reward, next_state, float(done))
                agent.train_step()
                state = next_state
                ep_reward += reward
            rewards_history.append(ep_reward)

        path = CHECKPOINT_DIR / f"sac_{symbol.replace('/', '_')}.pt"
        agent.save(path)
        logger.info("sac_trained", episodes=episodes, avg_reward=float(np.mean(rewards_history)))

        return RLTrainingResult(
            algorithm="SAC", total_reward=sum(rewards_history), episodes=episodes,
            avg_reward=float(np.mean(rewards_history)), checkpoint_path=str(path),
            metrics={"rewards": rewards_history[-10:]},
        )

    def evaluate(self, df: pd.DataFrame, checkpoint_path: str, algorithm: str = "DQN") -> dict:
        env = TradingEnvironment(df)
        if algorithm == "DQN":
            agent = DQNAgent(env.observation_space_size)
            ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
            agent.q_net.load_state_dict(ckpt["q_net"])
            agent.epsilon = 0

            state = env.reset()
            done = False
            while not done:
                action = agent.select_action(state)
                state, _, done, _ = env.step(action)

        return {"total_reward": env.total_reward, "final_balance": env.balance, "trades": env.trade_count}
