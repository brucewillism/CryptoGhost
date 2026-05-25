"""Backtest simulator — slippage, spread, fees."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class SimulatedFill:
    price: Decimal
    quantity: Decimal
    slippage: Decimal
    fees: Decimal
    filled: bool


class BacktestSimulator:
    def __init__(
        self,
        slippage_bps: float = 5.0,
        spread_bps: float = 3.0,
        fee_bps: float = 10.0,
        partial_fill_threshold: float = 0.95,
    ) -> None:
        self.slippage_bps = slippage_bps
        self.spread_bps = spread_bps
        self.fee_bps = fee_bps
        self.partial_fill_threshold = partial_fill_threshold

    def simulate_market_buy(self, price: Decimal, quantity: Decimal, liquidity_score: float = 50.0) -> SimulatedFill:
        slip_mult = Decimal(str(1 + (self.slippage_bps + self.spread_bps) / 10000))
        if liquidity_score < 30:
            slip_mult *= Decimal("1.002")
        fill_price = price * slip_mult
        fees = fill_price * quantity * Decimal(str(self.fee_bps / 10000))
        filled = liquidity_score / 100 >= (1 - self.partial_fill_threshold)
        qty = quantity if filled else quantity * Decimal(str(self.partial_fill_threshold))
        slippage = fill_price - price
        return SimulatedFill(fill_price, qty, slippage, fees, filled)

    def simulate_market_sell(self, price: Decimal, quantity: Decimal, liquidity_score: float = 50.0) -> SimulatedFill:
        slip_mult = Decimal(str(1 - (self.slippage_bps + self.spread_bps) / 10000))
        fill_price = price * slip_mult
        fees = fill_price * quantity * Decimal(str(self.fee_bps / 10000))
        qty = quantity
        slippage = price - fill_price
        return SimulatedFill(fill_price, qty, slippage, fees, True)
