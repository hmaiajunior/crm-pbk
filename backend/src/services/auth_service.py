import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.database import get_db
from src.models.operador import Operador

bearer = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(operador_id: uuid.UUID) -> str:
    payload = {
        "sub": str(operador_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def create_invite_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.INVITE_TOKEN_TTL_HOURS),
        "type": "invite",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_invite_token(token: str) -> str:
    try:
        data = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if data.get("type") != "invite":
            raise ValueError
        return data["email"]
    except Exception:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")


async def get_current_operador(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Operador:
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        operador_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    result = await db.execute(select(Operador).where(Operador.id == operador_id, Operador.ativo == True))
    operador = result.scalar_one_or_none()
    if not operador:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Operador não encontrado")
    return operador
