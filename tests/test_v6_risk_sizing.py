"""Tests for v6 position sizing and scoring."""

from decimal import Decimal

from backend.app.ai.consensus_v3.scoring import classify_score, compute_final_score
from backend.app.core.types import SignalClassification
from backend.app.risk.position_sizing import PositionSizingService


def test_final_score_classification():
    score = compute_final_score(0.8, 0.7, 75, 0.3, 0.7)
    assert score >= 60
    assert classify_score(score) in (SignalClassification.BUY, SignalClassification.STRONG_BUY)


def test_position_sizing_tiers():
    svc = PositionSizingService()
    assert svc.allocation_pct(85) >= 8
    assert svc.allocation_pct(55) >= 2
    assert svc.allocation_pct(40) == 0

    qty, pct = svc.compute_quantity(75, Decimal("50000"), Decimal("10000"))
    assert pct > 0
    assert qty > 0
