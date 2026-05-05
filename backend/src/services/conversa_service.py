import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.conversa import Conversa, StatusConversa
from src.models.operador import Operador


async def get_or_create_active(db: AsyncSession, cliente_id: uuid.UUID) -> Conversa:
    """Return the active conversation for a client, or create a new one."""
    result = await db.execute(
        select(Conversa).where(
            Conversa.cliente_id == cliente_id,
            Conversa.status == StatusConversa.ativa,
        )
    )
    conversa = result.scalar_one_or_none()
    if conversa:
        return conversa

    conversa = Conversa(cliente_id=cliente_id, status=StatusConversa.ativa)
    db.add(conversa)
    await db.flush()
    return conversa


async def start_handoff(db: AsyncSession, conversa_id: uuid.UUID, operador: Operador) -> Conversa:
    """Lock conversation to operator. Raises ValueError if already in handoff."""
    result = await db.execute(select(Conversa).where(Conversa.id == conversa_id))
    conversa = result.scalar_one_or_none()
    if not conversa:
        raise KeyError("Conversa não encontrada")
    if conversa.status == StatusConversa.em_handoff:
        raise ValueError(f"Conversa já em handoff por operador {conversa.operador_id}")

    conversa.status = StatusConversa.em_handoff
    conversa.operador_id = operador.id
    conversa.handoff_iniciado_em = datetime.now(timezone.utc)
    await db.flush()
    return conversa


async def end_handoff(db: AsyncSession, conversa_id: uuid.UUID, operador: Operador) -> Conversa:
    """Release conversation back to Nino."""
    result = await db.execute(select(Conversa).where(Conversa.id == conversa_id))
    conversa = result.scalar_one_or_none()
    if not conversa:
        raise KeyError("Conversa não encontrada")
    if conversa.operador_id != operador.id:
        raise PermissionError("Você não é o operador ativo desta conversa")

    conversa.status = StatusConversa.ativa
    conversa.operador_id = None
    conversa.handoff_iniciado_em = None
    await db.flush()
    return conversa


async def get_by_id(db: AsyncSession, conversa_id: uuid.UUID) -> Conversa | None:
    result = await db.execute(select(Conversa).where(Conversa.id == conversa_id))
    return result.scalar_one_or_none()
