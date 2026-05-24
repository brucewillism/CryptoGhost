"""CryptoGhost v5 - AI Truth Engine."""

from dataclasses import dataclass

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.ai_truth_engine")


@dataclass
class TruthAssessment:
    symbol: str
    truth_score: float
    raw_confidence: float
    corrected_confidence: float
    overconfidence_detected: bool
    hallucination_risk: float
    validation_basis: dict
    honest: bool


class AITruthEngine:
    """Impede confiança artificial — validação probabilística honesta."""

    MIN_EVIDENCE_SCORE = 0.35
    OVERCONFIDENCE_THRESHOLD = 0.85

    def assess(
        self,
        symbol: str,
        raw_confidence: float,
        validation_score: float,
        rolling_accuracy: float,
        evidence: dict,
    ) -> TruthAssessment:
        has_forecast = bool(evidence.get("has_forecast"))
        has_orderflow = bool(evidence.get("has_orderflow"))
        has_validation_history = rolling_accuracy > 0
        data_points = sum([has_forecast, has_orderflow, has_validation_history, bool(evidence.get("has_premium_data"))])

        evidence_score = data_points / 4
        if not has_forecast and raw_confidence > 0.7:
            evidence_score *= 0.5

        corrected = raw_confidence * evidence_score * (0.5 + rolling_accuracy * 0.5)
        corrected = min(corrected, validation_score / 100 * 0.9 + 0.1)
        corrected = max(0.05, min(0.95, corrected))

        overconf = raw_confidence > self.OVERCONFIDENCE_THRESHOLD and evidence_score < 0.5
        if overconf:
            corrected = min(corrected, 0.65)

        hallucination = 0.0
        if raw_confidence > 0.9 and evidence_score < 0.3:
            hallucination = min(0.95, raw_confidence - evidence_score)
        if evidence.get("conflicting_signals"):
            hallucination = max(hallucination, 0.4)

        truth = validation_score / 100 * 0.4 + rolling_accuracy * 0.3 + evidence_score * 0.3
        if overconf:
            truth *= 0.7
        truth = max(0, min(1, truth))

        return TruthAssessment(
            symbol=symbol, truth_score=round(truth, 4),
            raw_confidence=round(raw_confidence, 4), corrected_confidence=round(corrected, 4),
            overconfidence_detected=overconf, hallucination_risk=round(hallucination, 4),
            validation_basis={
                "evidence_score": round(evidence_score, 4),
                "validation_score": validation_score,
                "rolling_accuracy": rolling_accuracy,
                "data_points": data_points,
            },
            honest=truth >= self.MIN_EVIDENCE_SCORE and hallucination < 0.5,
        )
