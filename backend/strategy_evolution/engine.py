"""CryptoGhost v5 - Strategy Evolution Engine."""

import random
from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.strategy_evolution")


@dataclass
class StrategyGenome:
    strategy_id: str
    generation: int
    parameters: dict
    fitness_score: float
    sharpe_ratio: float
    max_drawdown_pct: float


class StrategyEvolutionEngine:
    """Evolução genética de parâmetros de estratégia."""

    PARAM_BOUNDS = {
        "stop_loss_pct": (0.5, 3.0),
        "take_profit_pct": (1.0, 8.0),
        "position_size_pct": (0.5, 5.0),
        "confidence_threshold": (0.5, 0.85),
        "momentum_filter": (0, 15),
    }

    def __init__(self, population_size: int = 12) -> None:
        self.population_size = population_size
        self._generation = 0
        self._population: list[StrategyGenome] = []

    def _random_genome(self, sid: str) -> StrategyGenome:
        params = {k: round(random.uniform(lo, hi), 3) for k, (lo, hi) in self.PARAM_BOUNDS.items()}
        return StrategyGenome(sid, self._generation, params, 0, 0, 0)

    def _fitness(self, df: pd.DataFrame, params: dict) -> tuple[float, float, float]:
        close = df["close"].astype(float)
        returns = close.pct_change().dropna()
        if len(returns) < 30:
            return 0, 0, 0

        signals = (close.pct_change(5) > params["momentum_filter"] / 1000).astype(int)
        strat_returns = returns * signals.shift(1).fillna(0)
        if strat_returns.std() == 0:
            return 0, 0, 0

        sharpe = float(strat_returns.mean() / strat_returns.std() * np.sqrt(252))
        equity = (1 + strat_returns).cumprod()
        dd = float((equity / equity.cummax() - 1).min() * 100)
        fitness = sharpe * 20 - abs(dd) * 0.5 + params["confidence_threshold"] * 10
        return max(0, fitness), sharpe, abs(dd)

    def evolve(self, df: pd.DataFrame, generations: int = 3) -> StrategyGenome:
        if not self._population:
            self._population = [self._random_genome(f"strat_{i}") for i in range(self.population_size)]

        best = self._population[0]
        for gen in range(generations):
            self._generation = gen
            scored = []
            for g in self._population:
                fit, sharpe, dd = self._fitness(df, g.parameters)
                g.fitness_score = fit
                g.sharpe_ratio = sharpe
                g.max_drawdown_pct = dd
                g.generation = gen
                scored.append(g)

            scored.sort(key=lambda x: -x.fitness_score)
            best = scored[0]
            survivors = scored[: max(4, self.population_size // 3)]

            new_pop = list(survivors)
            while len(new_pop) < self.population_size:
                p1, p2 = random.sample(survivors, 2)
                child_params = {}
                for k in self.PARAM_BOUNDS:
                    if random.random() < 0.5:
                        child_params[k] = p1.parameters[k]
                    else:
                        child_params[k] = p2.parameters[k]
                    if random.random() < 0.15:
                        lo, hi = self.PARAM_BOUNDS[k]
                        child_params[k] = round(random.uniform(lo, hi), 3)
                new_pop.append(StrategyGenome(f"strat_{len(new_pop)}", gen, child_params, 0, 0, 0))

            self._population = new_pop
            logger.info("strategy_evolved", generation=gen, best_fitness=best.fitness_score)

        return best
