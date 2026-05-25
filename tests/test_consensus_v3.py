"""Tests for Consensus Engine V3."""

from backend.ai_consensus_engine.consensus import AIConsensusEngine, AgentVote
from backend.app.ai.consensus_v3.engine import ConsensusEngineV3
from backend.app.ai.regime.policies import get_policy
from backend.app.core.types import MarketRegimeV6


def test_consensus_v3_blocks_weak_signal():
    engine = ConsensusEngineV3()
    votes = [
        AgentVote("analyst", "buy", 0.3, "weak", 0.30),
        AgentVote("risk", "hold", 0.6, "caution", 0.25),
        AgentVote("sentiment", "sell", 0.5, "bearish", 0.20),
        AgentVote("regime", "hold", 0.5, "range", 0.15),
        AgentVote("portfolio", "hold", 0.5, "maintain", 0.10),
    ]
    policy = get_policy(MarketRegimeV6.RANGING)
    result = engine.build_from_votes(
        "BTC/USDT", votes,
        calibrated_confidence=0.28,
        technical_score=45,
        sentiment_score=-0.2,
        regime=MarketRegimeV6.RANGING,
        policy=policy,
    )
    assert result.final_decision == "HOLD"
    assert not result.can_execute
    assert len(result.rejection_reasons) >= 1


def test_consensus_v3_allows_strong_signal():
    engine = ConsensusEngineV3()
    votes = [
        AgentVote("analyst", "buy", 0.9, "strong", 0.30),
        AgentVote("risk", "buy", 0.7, "low_risk", 0.25),
        AgentVote("sentiment", "buy", 0.8, "bullish", 0.20),
        AgentVote("regime", "buy", 0.75, "bull", 0.15),
        AgentVote("portfolio", "buy", 0.7, "accumulate", 0.10),
    ]
    policy = get_policy(MarketRegimeV6.TRENDING_BULL)
    result = engine.build_from_votes(
        "BTC/USDT", votes,
        calibrated_confidence=0.75,
        technical_score=80,
        sentiment_score=0.5,
        regime=MarketRegimeV6.TRENDING_BULL,
        policy=policy,
    )
    assert result.final_score >= 60
    assert result.can_execute or result.final_decision == "BUY"
