import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.campanha import Campanha, StatusCampanha
from src.models.operador import Operador

_EDITAVEIS = {StatusCampanha.rascunho, StatusCampanha.aguardando_aprovacao}


async def get_or_raise(db: AsyncSession, campanha_id: uuid.UUID) -> Campanha:
    result = await db.execute(select(Campanha).where(Campanha.id == campanha_id))
    campanha = result.scalar_one_or_none()
    if not campanha:
        raise KeyError(f"Campanha {campanha_id} não encontrada")
    return campanha


async def edit(db: AsyncSession, campanha_id: uuid.UUID, copy: str | None, orcamento_sugerido: float | None) -> Campanha:
    campanha = await get_or_raise(db, campanha_id)
    if campanha.status not in _EDITAVEIS:
        raise ValueError(f"Campanha não pode ser editada no status atual ({campanha.status})")
    if copy is not None:
        campanha.copy = copy
    if orcamento_sugerido is not None:
        campanha.orcamento_sugerido = orcamento_sugerido
    await db.commit()
    await db.refresh(campanha)
    return campanha


async def approve(db: AsyncSession, campanha_id: uuid.UUID, operador: Operador) -> Campanha:
    campanha = await get_or_raise(db, campanha_id)
    if campanha.status != StatusCampanha.aguardando_aprovacao:
        raise ValueError("Campanha não está aguardando aprovação")
    campanha.status = StatusCampanha.aprovada
    campanha.aprovada_por = operador.id
    campanha.aprovada_em = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(campanha)
    return campanha


async def reject(db: AsyncSession, campanha_id: uuid.UUID) -> Campanha:
    campanha = await get_or_raise(db, campanha_id)
    if campanha.status not in {StatusCampanha.rascunho, StatusCampanha.aguardando_aprovacao}:
        raise ValueError("Campanha não pode ser rejeitada no status atual")
    campanha.status = StatusCampanha.rejeitada
    await db.commit()
    await db.refresh(campanha)
    return campanha
