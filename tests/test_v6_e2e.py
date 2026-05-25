"""E2E smoke tests for v6 modules wiring."""

from backend.app.ai.consensus_v3.scoring import compute_final_score, classify_score
from backend.app.auto_invest.signal_freshness import SignalFreshnessValidator
from backend.app.core.types import ConsensusResultV3, SignalClassification
from backend.app.risk.position_sizing import PositionSizingService
from backend.shared.config import get_settings


def test_final_score_and_classification_bands():
    score = compute_final_score(
        consensus=0.8,
        calibrated_confidence=0.75,
        technical_score=70,
        sentiment_score=0.5,
        regime_alignment=0.9,
        disagreement_penalty=0,
    )
    assert score >= 60
    assert classify_score(score) in (SignalClassification.BUY, SignalClassification.STRONG_BUY)


def test_signal_freshness_rejects_weak():
    validator = SignalFreshnessValidator()
    result = ConsensusResultV3(
        symbol="BTC/USDT",
        final_score=45,
        classification=SignalClassification.HOLD,
        final_decision="HOLD",
        consensus=0.3,
        calibrated_confidence=0.3,
        technical_score=40,
        sentiment_score=0,
        regime_alignment=0.5,
        agreement=1,
        disagreement=4,
        conflicts=["analyst vs risk", "sentiment vs regime"],
        agent_votes=[],
        can_execute=False,
        rejection_reasons=["agreement too low"],
    )
    ok, reason = validator.validate_result(result)
    assert not ok
    assert reason


def test_position_sizing_tiers():
    from decimal import Decimal

    settings = get_settings()
    svc = PositionSizingService()
    qty, pct = svc.compute_quantity(78, Decimal("50000"), Decimal(str(settings.paper_portfolio_usdt)))
    assert qty > 0
    assert pct >= 4


def test_v6_feature_flags_loaded():
    settings = get_settings()
    assert hasattr(settings, "v6_enabled")
    assert hasattr(settings, "min_final_score_buy")
