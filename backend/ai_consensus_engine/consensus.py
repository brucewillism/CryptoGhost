"""CryptoGhost - AI Consensus Engine (Multi-Agent)."""

import time
from dataclasses import dataclass

from backend.shared.logging_config import get_logger
from backend.shared.metrics import AI_CONFIDENCE_GAUGE, AI_LATENCY, CONSENSUS_AGREEMENT

logger = get_logger("cryptoghost.ai_consensus")

AGENT_WEIGHTS = {
    "analyst": 0.30,
    "risk": 0.25,
    "sentiment": 0.20,
    "portfolio": 0.10,
    "regime": 0.15,
}

DECISION_MAP = {
    "strong_buy": "BUY", "moderate_buy": "BUY", "buy": "BUY",
    "strong_sell": "SELL", "moderate_sell": "SELL", "sell": "SELL",
    "hold": "HOLD", "maintain": "HOLD", "neutral": "HOLD",
}


@dataclass
class AgentVote:
    agent: str
    decision: str
    confidence: float
    raw_signal: str
    weight: float


@dataclass
class ConsensusResult:
    final_decision: str
    confidence: float
    agreement: int
    disagreement: int
    agent_votes: list[AgentVote]
    conflicts: list[str]
    weighted_scores: dict


class AIConsensusEngine:
    """Sistema multi-agente com weighted voting e detecção de conflitos."""

    def build_consensus(self, symbol: str, votes: list[AgentVote]) -> ConsensusResult:
        start = time.perf_counter()

        weighted = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        for vote in votes:
            normalized = DECISION_MAP.get(vote.decision.lower(), vote.decision.upper())
            if normalized not in weighted:
                normalized = "HOLD"
            weighted[normalized] += vote.confidence * vote.weight

        final = max(weighted, key=weighted.get)  # type: ignore
        total_weight = sum(v.weight for v in votes) or 1
        confidence = weighted[final] / total_weight

        decisions = [DECISION_MAP.get(v.decision.lower(), v.decision.upper()) for v in votes]
        agreement = sum(1 for d in decisions if d == final)
        disagreement = len(decisions) - agreement

        conflicts = self._detect_conflicts(votes)

        elapsed = time.perf_counter() - start
        AI_LATENCY.labels(agent="consensus").observe(elapsed)
        AI_CONFIDENCE_GAUGE.labels(agent="consensus").set(confidence)
        CONSENSUS_AGREEMENT.labels(symbol=symbol).set(agreement / max(len(votes), 1))

        logger.info("consensus_built", symbol=symbol, decision=final, agreement=agreement, confidence=confidence)

        return ConsensusResult(
            final_decision=final,
            confidence=round(confidence, 2),
            agreement=agreement,
            disagreement=disagreement,
            agent_votes=votes,
            conflicts=conflicts,
            weighted_scores={k: round(v, 3) for k, v in weighted.items()},
        )

    @staticmethod
    def _detect_conflicts(votes: list[AgentVote]) -> list[str]:
        conflicts = []
        buy_agents = [v.agent for v in votes if DECISION_MAP.get(v.decision.lower(), "") == "BUY"]
        sell_agents = [v.agent for v in votes if DECISION_MAP.get(v.decision.lower(), "") == "SELL"]

        if buy_agents and sell_agents:
            conflicts.append(f"Conflito: {', '.join(buy_agents)} (BUY) vs {', '.join(sell_agents)} (SELL)")

        risk_votes = [v for v in votes if v.agent == "risk" and v.confidence > 0.7]
        analyst_votes = [v for v in votes if v.agent == "analyst" and v.confidence > 0.7]
        if risk_votes and analyst_votes:
            risk_dec = DECISION_MAP.get(risk_votes[0].decision.lower(), "HOLD")
            analyst_dec = DECISION_MAP.get(analyst_votes[0].decision.lower(), "HOLD")
            if risk_dec != analyst_dec:
                conflicts.append(f"Risk AI ({risk_dec}) diverge do Analyst AI ({analyst_dec})")

        return conflicts

    @staticmethod
    def vote_from_analyst(recommendation: str, confidence: float) -> AgentVote:
        return AgentVote("analyst", recommendation, confidence, recommendation, AGENT_WEIGHTS["analyst"])

    @staticmethod
    def vote_from_risk(overall_risk: str, crash_prob: float) -> AgentVote:
        if overall_risk in ("critical", "high") or crash_prob > 0.6:
            decision, conf = "SELL", min(0.9, crash_prob + 0.2)
        elif overall_risk == "low":
            decision, conf = "HOLD", 0.6
        else:
            decision, conf = "HOLD", 0.5
        return AgentVote("risk", decision, conf, overall_risk, AGENT_WEIGHTS["risk"])

    @staticmethod
    def vote_from_sentiment(sentiment: str, score: float, confidence: float) -> AgentVote:
        if sentiment == "bullish" and score > 60:
            decision = "BUY"
        elif sentiment == "bearish" and score < 40:
            decision = "SELL"
        else:
            decision = "HOLD"
        return AgentVote("sentiment", decision, confidence, sentiment, AGENT_WEIGHTS["sentiment"])

    @staticmethod
    def vote_from_regime(regime: str, confidence: float) -> AgentVote:
        regime_decisions = {
            "bull_market": "BUY", "bear_market": "SELL", "accumulation": "BUY",
            "distribution": "SELL", "high_volatility": "HOLD", "sideways": "HOLD",
        }
        decision = regime_decisions.get(regime, "HOLD")
        return AgentVote("regime", decision, confidence, regime, AGENT_WEIGHTS["regime"])

    @staticmethod
    def vote_from_portfolio(risk_level: str, top_action: str) -> AgentVote:
        action_map = {
            "reduce_exposure": "SELL", "increase_hedge": "SELL",
            "rebalance": "HOLD", "maintain": "HOLD", "reduce_volatility": "HOLD",
        }
        decision = action_map.get(top_action, "HOLD")
        conf = 0.7 if risk_level == "high" else 0.5
        return AgentVote("portfolio", decision, conf, top_action, AGENT_WEIGHTS["portfolio"])
