"""Consensus V3 scoring — FINAL_SCORE composto."""

from backend.app.core.types import SignalClassification


def compute_final_score(
    consensus: float,
    calibrated_confidence: float,
    technical_score: float,
    sentiment_score: float,
    regime_alignment: float,
    disagreement_penalty: float = 0.0,
) -> float:
    raw = (
        consensus * 0.30
        + calibrated_confidence * 0.25
        + (technical_score / 100.0) * 0.20
        + ((sentiment_score + 1) / 2) * 0.15
        + regime_alignment * 0.10
    )
    return max(0.0, min(100.0, (raw * 100) - disagreement_penalty))


def classify_score(score: float) -> SignalClassification:
    if score >= 75:
        return SignalClassification.STRONG_BUY
    if score >= 60:
        return SignalClassification.BUY
    if score >= 40:
        return SignalClassification.HOLD
    if score >= 20:
        return SignalClassification.SELL
    return SignalClassification.STRONG_SELL


def score_to_decision(classification: SignalClassification) -> str:
    if classification in (SignalClassification.STRONG_BUY, SignalClassification.BUY):
        return "BUY"
    if classification in (SignalClassification.STRONG_SELL, SignalClassification.SELL):
        return "SELL"
    return "HOLD"
