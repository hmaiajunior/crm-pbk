import asyncio
import uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.database import get_db, AsyncSessionLocal
from src.models.mensagem import DirecaoMensagem, Mensagem, SentimentoMensagem, TemaMensagem
from src.services import cliente_service, conversa_service, evento_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class NinoWebhookPayload(BaseModel):
    mensagem_id: uuid.UUID
    telefone: str
    conteudo: str
    direcao: DirecaoMensagem
    sentimento: SentimentoMensagem | None = None
    tema: TemaMensagem | None = None
    timestamp: datetime


def _verify_nino_key(x_nino_key: Annotated[str | None, Header()] = None):
    if x_nino_key != settings.NINO_WEBHOOK_KEY:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")


@router.post("/nino/mensagem")
async def nino_mensagem(
    payload: NinoWebhookPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(_verify_nino_key)],
):
    # Idempotency check
    existing = await db.execute(select(Mensagem).where(Mensagem.id == payload.mensagem_id))
    if existing.scalar_one_or_none():
        return {"status": "duplicate", "mensagem_id": str(payload.mensagem_id)}

    cliente, _ = await cliente_service.get_or_create_by_phone(db, payload.telefone)
    conversa = await conversa_service.get_or_create_active(db, cliente.id)

    now = payload.timestamp
    mensagem = Mensagem(
        id=payload.mensagem_id,
        conversa_id=conversa.id,
        conteudo=payload.conteudo,
        direcao=payload.direcao,
        sentimento=payload.sentimento,
        tema=payload.tema,
        classificado_em=now if payload.sentimento else None,
        enviada_em=now,
    )
    db.add(mensagem)
    await cliente_service.update_ultima_interacao(db, cliente)

    # Trigger async post-processing without blocking response
    asyncio.create_task(_post_process(payload.mensagem_id, cliente.id, payload.sentimento))

    return {"status": "ok", "mensagem_id": str(payload.mensagem_id)}


async def _post_process(mensagem_id: uuid.UUID, cliente_id: uuid.UUID, sentimento: SentimentoMensagem | None) -> None:
    from src.models.cliente import Cliente
    from src.events.bus import bus

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
            cliente = result.scalar_one_or_none()
            if cliente:
                evento = await evento_service.evaluate_and_emit(db, cliente, sentimento)
                await db.commit()
                await bus.publish("mensagem_recebida", {"cliente_id": cliente_id})
                if evento:
                    await bus.publish(evento.tipo.value, {"cliente_id": cliente_id, "tipo_evento": evento.tipo.value})
        except Exception:
            await db.rollback()
