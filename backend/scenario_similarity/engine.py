"""CryptoGhost v3 - Scenario Similarity Engine."""

import math
from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.shared.logging_config import get_logger
from backend.shared.models_quant import ScenarioEmbeddingRecord

logger = get_logger("cryptoghost.scenario_similarity")


@dataclass
class SimilarScenario:
    scenario_label: str
    similarity: float
    outcome: str | None
    outcome_pct: float | None
    market_state: dict
    created_at: datetime | None


@dataclass
class SimilarityResult:
    symbol: str
    current_state: dict
    best_match: SimilarScenario | None
    similar_scenarios: list[SimilarScenario]
    aggregate_probability: dict[str, float]
    summary: str


class ScenarioSimilarityEngine:
    """Busca vetorial de cenários históricos similares via embeddings."""

    FEATURE_KEYS = ["returns_mean", "volatility", "rsi", "momentum", "volume_ratio", "trend_strength"]

    def build_embedding(self, market_state: dict) -> list[float]:
        values = [float(market_state.get(k, 0)) for k in self.FEATURE_KEYS]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def store_scenario(
        self,
        session: Session,
        symbol: str,
        label: str,
        market_state: dict,
        outcome: str | None = None,
        outcome_pct: float | None = None,
    ) -> ScenarioEmbeddingRecord:
        embedding = self.build_embedding(market_state)
        record = ScenarioEmbeddingRecord(
            symbol=symbol,
            scenario_label=label,
            embedding=embedding,
            market_state=market_state,
            outcome=outcome,
            outcome_pct=outcome_pct,
        )
        session.add(record)
        session.flush()
        return record

    def find_similar(
        self,
        session: Session,
        symbol: str,
        current_state: dict,
        top_k: int = 5,
    ) -> SimilarityResult:
        query_emb = self.build_embedding(current_state)
        records = (
            session.query(ScenarioEmbeddingRecord)
            .filter(ScenarioEmbeddingRecord.symbol == symbol)
            .order_by(ScenarioEmbeddingRecord.created_at.desc())
            .limit(500)
            .all()
        )

        scored: list[SimilarScenario] = []
        for rec in records:
            if not rec.embedding:
                continue
            sim = self._cosine_similarity(query_emb, rec.embedding)
            scored.append(SimilarScenario(
                scenario_label=rec.scenario_label,
                similarity=round(sim, 4),
                outcome=rec.outcome,
                outcome_pct=rec.outcome_pct,
                market_state=rec.market_state,
                created_at=rec.created_at,
            ))

        scored.sort(key=lambda x: -x.similarity)
        top = scored[:top_k]
        best = top[0] if top else None

        outcomes = [s for s in top if s.outcome]
        bullish = sum(1 for s in outcomes if s.outcome in ("bullish", "positive", "buy"))
        bearish = sum(1 for s in outcomes if s.outcome in ("bearish", "negative", "sell"))
        total = len(outcomes) or 1

        aggregate = {
            "bullish_prob": round(bullish / total, 3),
            "bearish_prob": round(bearish / total, 3),
            "neutral_prob": round(1 - bullish / total - bearish / total, 3),
        }

        summary = (
            f"Mercado atual é {best.similarity * 100:.0f}% similar a '{best.scenario_label}'"
            if best else "Sem cenários históricos comparáveis"
        )

        return SimilarityResult(
            symbol=symbol,
            current_state=current_state,
            best_match=best,
            similar_scenarios=top,
            aggregate_probability=aggregate,
            summary=summary,
        )

    @staticmethod
    def extract_market_state(df: pd.DataFrame, indicators: dict) -> dict:
        close = df["close"].astype(float)
        returns = close.pct_change().dropna()
        return {
            "returns_mean": float(returns.mean()),
            "volatility": float(returns.std() * np.sqrt(252)),
            "rsi": float(indicators.get("rsi", 50)),
            "momentum": float(indicators.get("momentum", 0)),
            "volume_ratio": float(indicators.get("volume_ratio", 1)),
            "trend_strength": float(close.pct_change(20).iloc[-1]) if len(close) > 20 else 0,
        }

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        min_len = min(len(a), len(b))
        dot = sum(a[i] * b[i] for i in range(min_len))
        norm_a = math.sqrt(sum(x * x for x in a[:min_len])) or 1
        norm_b = math.sqrt(sum(x * x for x in b[:min_len])) or 1
        return dot / (norm_a * norm_b)
