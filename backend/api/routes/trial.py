"""CryptoGhost - API do período de teste paper (30 dias)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.paper_trial.service import get_trial_status, run_learning_cycle, start_trial
from backend.shared.database import get_async_session
from backend.shared.security import get_current_user

router = APIRouter(prefix="/trial", tags=["Paper Trial — 30 dias"])


@router.get("/status")
async def trial_status(
    session: AsyncSession = Depends(get_async_session),
    _user: dict = Depends(get_current_user),
) -> dict:
    """Progresso do teste, P&L paper e prontidão para live."""
    return await get_trial_status(session)


@router.post("/start")
async def trial_start(
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(get_current_user),
) -> dict:
    """Inicia contagem de 30 dias de teste paper."""
    result = await start_trial(session, actor=user["username"])
    await session.commit()
    return result


@router.post("/learn")
async def trial_learn(
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(get_current_user),
) -> dict:
    """Roda ciclo de aprendizado: valida previsões vs mercado e ajusta memória IA."""
    result = await run_learning_cycle(session, actor=user["username"])
    await session.commit()
    status = await get_trial_status(session)
    return {"learning_cycle": result, "trial": status}
