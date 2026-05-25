"""CryptoGhost - Schemas Pydantic da API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class OrderCreateRequest(BaseModel):
    exchange: str = "binance"
    symbol: str
    side: str
    quantity: Decimal
    order_type: str = "market"
    price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None


class OrderResponse(BaseModel):
    id: UUID
    exchange: str
    symbol: str
    side: str
    order_type: str
    status: str
    quantity: Decimal
    price: Decimal | None
    filled_quantity: Decimal
    average_price: Decimal | None
    stop_loss: Decimal | None
    take_profit: Decimal | None
    trading_mode: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PositionResponse(BaseModel):
    id: UUID
    exchange: str
    symbol: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal | None
    unrealized_pnl: Decimal
    stop_loss: Decimal | None
    take_profit: Decimal | None
    is_open: bool
    trading_mode: str

    model_config = {"from_attributes": True}


class PredictionResponse(BaseModel):
    id: UUID
    model_name: str
    symbol: str
    signal: str
    confidence: float
    predicted_price: Decimal | None
    explanation: str | None
    metrics: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskStatusResponse(BaseModel):
    daily_pnl: float
    max_daily_loss: float
    total_exposure: float
    max_exposure: float
    trading_halted: bool
    circuit_breaker_active: bool
    paper_trading: bool
    live_trading_enabled: bool


class DashboardStats(BaseModel):
    total_pnl: float = 0.0
    paper_portfolio_value: float = 0.0
    paper_return_pct: float = 0.0
    open_positions: int = 0
    total_orders: int = 0
    ai_signal: str = "hold"
    ai_confidence: float = 0.0
    risk_status: RiskStatusResponse
    system_status: str = "operational"
    auto_invest_interval_minutes: int = 30


class BacktestRequest(BaseModel):
    symbol: str = "BTC/USDT"
    strategy_name: str = "CryptoGhost-Hybrid"
    initial_capital: Decimal = Decimal("10000")


class ApprovedInvestmentRequest(BaseModel):
    """Ordem de investimento — só executa com confirmação explícita do usuário."""

    user_confirmed: bool = Field(..., description="Deve ser true para executar")
    symbol: str
    side: str = "buy"
    quantity: Decimal
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None


class AuditLogResponse(BaseModel):
    id: UUID
    event_type: str
    actor: str
    action: str
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BrokerCompareRequest(BaseModel):
    symbol: str = "BTC/USDT"
    exchanges: list[str] = Field(default=["binance", "kraken"])
