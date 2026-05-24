"""Testes do AI Consensus Engine."""

from backend.ai_consensus_engine.consensus import AIConsensusEngine, AgentVote


def test_consensus_buy_majority():
    engine = AIConsensusEngine()
    votes = [
        AgentVote("analyst", "moderate_buy", 0.85, "moderate_buy", 0.30),
        AgentVote("sentiment", "BUY", 0.75, "bullish", 0.20),
        AgentVote("regime", "BUY", 0.70, "bull_market", 0.15),
        AgentVote("risk", "HOLD", 0.50, "medium", 0.25),
        AgentVote("portfolio", "HOLD", 0.50, "maintain", 0.10),
    ]
    result = engine.build_consensus("BTC/USDT", votes)
    assert result.final_decision == "BUY"
    assert result.agreement >= 2
    assert result.confidence > 0


def test_consensus_detects_conflict():
    engine = AIConsensusEngine()
    votes = [
        AgentVote("analyst", "strong_buy", 0.9, "strong_buy", 0.30),
        AgentVote("risk", "SELL", 0.85, "critical", 0.25),
    ]
    result = engine.build_consensus("ETH/USDT", votes)
    assert len(result.conflicts) > 0
