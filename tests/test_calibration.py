"""Testes de calibração de confiança v3."""

from backend.ai_calibration.calibrator import ConfidenceCalibrator


def test_calibrate_fallback():
    cal = ConfidenceCalibrator()
    result = cal.calibrate(0.8, regime="bull_market", agreement_ratio=0.9)
    assert 0 < result.calibrated_confidence <= 0.99
    assert result.uncertainty >= 0
    assert result.reliability_score >= 0


def test_calibrate_with_fit():
    cal = ConfidenceCalibrator()
    confidences = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99] * 2
    outcomes = [0, 0, 0, 1, 1, 1, 1, 1, 1, 1] * 2
    cal.fit(confidences, outcomes)
    result = cal.calibrate(0.75, agreement_ratio=0.8)
    assert result.method in ("isotonic_regression", "platt_scaling", "historical_fallback")
    assert result.calibrated_confidence != result.raw_confidence or result.method != "historical_fallback"


def test_online_update():
    cal = ConfidenceCalibrator()
    for i in range(25):
        cal.update_online(0.6 + i * 0.01, i % 2 == 0)
    result = cal.calibrate(0.7)
    assert result.calibrated_confidence > 0
