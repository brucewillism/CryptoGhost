"""CryptoGhost - Segurança: JWT, criptografia e RBAC."""

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Annotated

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.shared.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """Roles RBAC básico do CryptoGhost."""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: UserRole = UserRole.ADMIN) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "role": role.value, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        ) from exc


def _get_fernet() -> Fernet:
    """Deriva chave Fernet a partir do secret_key."""
    settings = get_settings()
    import base64
    import hashlib

    key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
    return Fernet(key)


def encrypt_credential(plain_text: str) -> str:
    """Criptografa credenciais sensíveis para armazenamento."""
    return _get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_credential(cipher_text: str) -> str:
    """Descriptografa credenciais."""
    try:
        return _get_fernet().decrypt(cipher_text.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Credencial criptografada inválida") from exc


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária")
    payload = decode_access_token(credentials.credentials)
    return {"username": payload["sub"], "role": payload.get("role", UserRole.VIEWER.value)}


def require_role(*allowed_roles: UserRole):
    """Dependency factory para RBAC."""

    async def checker(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if user["role"] not in {r.value for r in allowed_roles}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
        return user

    return checker
