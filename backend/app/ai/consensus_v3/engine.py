"""Consensus Engine V3 — weighted voting estatístico com hard rules."""

from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from backend.ai_consensus_engine.consensus import AIConsensusEngine, AgentVote
from backend.app.ai.consensus_v3.scoring import classify_score, compute_final_score, score_to_decision
from backend.app.ai.regime.policies import RegimePolicy
from backend.app.core.types import AgentVoteV3, ConsensusResultV3, MarketRegimeV6, SignalClassification
from backend.app.ai.meta_learning.service import AgentPerformanceService
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.v6.consensus")


class ConsensusEngineV3:
    """Substitui consenso simples por scoring estatístico com supressão de sinais fracos."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.legacy_engine = AIConsensusEngine()
        self.performance = AgentPerformanceService()

    def build_from_votes(
        self,
        symbol: str,
        legacy_votes: list[AgentVote],
        *,
        calibrated_confidence: float = 0.5,
        technical_score: float = 50.0,
        sentiment_score: float = 0.0,
        regime: MarketRegimeV6 = MarketRegimeV6.RANGING,
        policy: RegimePolicy | None = None,
        agent_weights: dict[str, float] | None = None,
    ) -> ConsensusResultV3:
        policy = policy or __import__(
            "backend.app.ai.regime.policies", fromlist=["get_policy"]
        ).get_policy(regime)

        weights = agent_weights or {}
        votes_v3: list[AgentVoteV3] = []
        adjusted_votes: list[AgentVote] = []

        for v in legacy_votes:
            mult = policy.agent_weight_multiplier.get(v.agent, 1.0)
            dyn = weights.get(v.agent, v.weight)
            new_weight = v.weight * mult * (dyn / max(v.weight, 0.01))
            perf_acc = weights.get(f"{v.agent}_acc", 0.5)
            votes_v3.append(AgentVoteV3(
                agent=v.agent,
                signal=v.decision,
                confidence=v.confidence,
                explanation=v.raw_signal,
                historical_accuracy=perf_acc,
                regime_accuracy=perf_acc,
                weight=new_weight,
            ))
            adjusted_votes.append(AgentVote(
                v.agent, v.decision, v.confidence, v.raw_signal, new_weight
            ))

        legacy_result = self.legacy_engine.build_consensus(symbol, adjusted_votes)
        conflicts = list(legacy_result.conflicts)
        agreement = legacy_result.agreement
        disagreement = legacy_result.disagreement

        disagreement_penalty = max(0, (disagreement - 1) * 8.0)
        if len(conflicts) >= 2:
            disagreement_penalty += 15.0

        regime_alignment = 0.7 if regime in (
            MarketRegimeV6.TRENDING_BULL, MarketRegimeV6.ACCUMULATION
        ) else 0.5

        final_score = compute_final_score(
            legacy_result.confidence,
            calibrated_confidence,
            technical_score,
            sentiment_score,
            regime_alignment,
            disagreement_penalty,
        )
        classification = classify_score(final_score)
        decision = score_to_decision(classification)

        rejection: list[str] = []
        min_score = policy.min_final_score

        if final_score < min_score:
            rejection.append(f"final_score {final_score:.1f} < {min_score}")
            decision = "HOLD"
            classification = SignalClassification.HOLD

        if agreement < self.settings.min_consensus_agreement:
            rejection.append(f"agreement {agreement}/{agreement + disagreement} < {self.settings.min_consensus_agreement}")
            decision = "HOLD"
            classification = SignalClassification.HOLD

        if calibrated_confidence < self.settings.min_calibrated_confidence:
            rejection.append(f"calibrated {calibrated_confidence:.2f} < {self.settings.min_calibrated_confidence}")
            decision = "HOLD"
            classification = SignalClassification.HOLD

        if len(conflicts) >= 2:
            rejection.append(f"{len(conflicts)} agent conflicts")
            decision = "HOLD"
            classification = SignalClassification.HOLD

        can_execute = (
            decision == "BUY"
            and classification in (SignalClassification.BUY, SignalClassification.STRONG_BUY)
            and not rejection
        )

        expires = datetime.now(UTC) + timedelta(minutes=self.settings.signal_max_age_minutes)

        result = ConsensusResultV3(
            symbol=symbol,
            final_decision=decision,
            final_score=round(final_score, 2),
            classification=classification,
            consensus=legacy_result.confidence,
            calibrated_confidence=calibrated_confidence,
            technical_score=technical_score,
            sentiment_score=sentiment_score,
            regime_alignment=regime_alignment,
            agreement=agreement,
            disagreement=disagreement,
            conflicts=conflicts,
            agent_votes=votes_v3,
            can_execute=can_execute,
            rejection_reasons=rejection,
            expires_at=expires,
        )
        logger.info(
            "consensus_v3_built",
            symbol=symbol,
            score=final_score,
            decision=decision,
            can_execute=can_execute,
        )
        return result

    @staticmethod
    def to_dict(result: ConsensusResultV3) -> dict:
        return {
            "symbol": result.symbol,
            "final_decision": result.final_decision,
            "final_score": result.final_score,
            "classification": result.classification.value,
            "consensus": result.consensus,
            "calibrated_confidence": result.calibrated_confidence,
            "technical_score": result.technical_score,
            "sentiment_score": result.sentiment_score,
            "regime_alignment": result.regime_alignment,
            "agreement": result.agreement,
            "disagreement": result.disagreement,
            "conflicts": result.conflicts,
            "agent_votes": [asdict(v) for v in result.agent_votes],
            "can_execute": result.can_execute,
            "rejection_reasons": result.rejection_reasons,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None,
        }
