"""CryptoGhost - Rotas de autenticação."""

from fastapi import APIRouter, HTTPException, status

from backend.api.schemas import LoginRequest, TokenResponse
from backend.shared.config import get_settings
from backend.shared.security import UserRole, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    settings = get_settings()
    if request.username != settings.admin_username or request.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    token = create_access_token(request.username, UserRole.ADMIN)
    return TokenResponse(access_token=token, role=UserRole.ADMIN.value)
