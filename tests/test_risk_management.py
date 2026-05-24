"""Testes do RiskManager CryptoGhost."""

from decimal import Decimal

from backend.risk_management.manager import PositionRisk, RiskManager


def test_stop_loss_calculation_buy():
    manager = RiskManager(portfolio_value=Decimal("10000"))
    sl = manager.calculate_stop_loss(Decimal("100"), "buy", pct=2.0)
    assert sl == Decimal("98")


def test_take_profit_calculation_buy():
    manager = RiskManager(portfolio_value=Decimal("10000"))
    tp = manager.calculate_take_profit(Decimal("100"), "buy", pct=3.0)
    assert tp == Decimal("103")


def test_daily_loss_limit():
    manager = RiskManager(portfolio_value=Decimal("10000"))
    manager.record_pnl(Decimal("-250"))
    can_trade, reason = manager.can_open_position(Decimal("100"))
    assert not can_trade
    assert "perda" in reason.lower() or "circuit" in reason.lower() or "desligado" in reason.lower()


def test_trailing_stop_buy():
    manager = RiskManager()
    position = PositionRisk(
        symbol="BTC/USDT",
        entry_price=Decimal("100"),
        quantity=Decimal("1"),
        side="buy",
        trailing_stop_pct=1.0,
    )
    manager.update_trailing_stop(position, Decimal("110"))
    assert position.stop_loss is not None
    assert position.stop_loss > Decimal("100")


def test_position_sizing():
    manager = RiskManager(portfolio_value=Decimal("10000"))
    size = manager.calculate_position_size(Decimal("50000"))
    assert size > 0
