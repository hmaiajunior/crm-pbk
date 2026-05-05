from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.operador import Operador
from src.services.auth_service import (
    create_invite_token,
    create_token,
    decode_invite_token,
    get_current_operador,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class InviteRequest(BaseModel):
    email: EmailStr
    nome: str


class RegisterRequest(BaseModel):
    token: str
    nome: str
    senha: str


@router.post("/login")
async def login(body: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Operador).where(Operador.email == body.email, Operador.ativo == True))
    operador = result.scalar_one_or_none()
    if not operador or not verify_password(body.senha, operador.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return {"token": create_token(operador.id), "operador": {"id": str(operador.id), "nome": operador.nome, "email": operador.email}}


@router.post("/invite", status_code=201)
async def invite(body: InviteRequest, operador: Annotated[Operador, Depends(get_current_operador)]):
    token = create_invite_token(body.email)
    # In production: send token via email (SMTP). Returning token for development ease.
    return {"message": "Convite enviado", "token": token}


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    email = decode_invite_token(body.token)
    result = await db.execute(select(Operador).where(Operador.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    operador = Operador(email=email, nome=body.nome, senha_hash=hash_password(body.senha))
    db.add(operador)
    await db.flush()
    return {"operador": {"id": str(operador.id), "nome": operador.nome, "email": operador.email}}
