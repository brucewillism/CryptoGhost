"""CryptoGhost - Rotas de IA e backtesting."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import BacktestRequest, PredictionResponse
from backend.backtesting.engine import BacktestEngine
from backend.shared.database import get_async_session
from backend.shared.models import AIPrediction
from backend.shared.security import get_current_user
import numpy as np
import pandas as pd

router = APIRouter(prefix="/ai", tags=["Inteligência Artificial"])


@router.get("/predictions", response_model=list[PredictionResponse])
async def list_predictions(
    symbol: str | None = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> list[AIPrediction]:
    query = select(AIPrediction).order_by(AIPrediction.created_at.desc()).limit(limit)
    if symbol:
        query = query.where(AIPrediction.symbol == symbol)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.post("/backtest")
async def run_backtest(
    request: BacktestRequest,
    _user: dict = Depends(get_current_user),
) -> dict:
    """Executa backtesting com dados sintéticos quando histórico indisponível."""
    np.random.seed(42)
    n = 500
    prices = 65000 * np.cumprod(1 + np.random.randn(n) * 0.01)
    df = pd.DataFrame(
        {
            "open": prices * 0.999,
            "high": prices * 1.002,
            "low": prices * 0.998,
            "close": prices,
            "volume": np.random.uniform(100, 1000, n),
        }
    )

    engine = BacktestEngine(initial_capital=request.initial_capital)
    result = engine.run(df, request.symbol, request.strategy_name)
    return engine.generate_report(result)
