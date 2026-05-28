import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.cliente import Cliente
from src.models.conversa import Conversa, StatusConversa
from src.models.operador import Operador
from src.services import conversa_service
from src.services.auth_service import get_current_operador

router = APIRouter(prefix="/conversas", tags=["conversas"])


@router.get("")
async def list_conversas(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Operador, Depends(get_current_operador)],
    status: StatusConversa | None = Query(default=None),
):
    query = select(Conversa).where(Conversa.status != StatusConversa.encerrada)
    if status:
        query = query.where(Conversa.status == status)
    query = query.order_by(Conversa.iniciada_em.desc())

    result = await db.execute(query)
    conversas = list(result.scalars().all())

    cliente_ids = {c.cliente_id for c in conversas}
    operador_ids = {c.operador_id for c in conversas if c.operador_id}

    clientes: dict[uuid.UUID, Cliente] = {}
    if cliente_ids:
        cr = await db.execute(select(Cliente).where(Cliente.id.in_(cliente_ids)))
        clientes = {c.id: c for c in cr.scalars().all()}

    operadores: dict[uuid.UUID, Operador] = {}
    if operador_ids:
        orr = await db.execute(select(Operador).where(Operador.id.in_(operador_ids)))
        operadores = {o.id: o for o in orr.scalars().all()}

    return [
        {
            "id": str(c.id),
            "cliente_id": str(c.cliente_id),
            "cliente_nome": clientes[c.cliente_id].nome if c.cliente_id in clientes else None,
            "cliente_telefone": clientes[c.cliente_id].telefone if c.cliente_id in clientes else "",
            "status": c.status,
            "operador_nome": operadores[c.operador_id].nome if c.operador_id and c.operador_id in operadores else None,
        }
        for c in conversas
    ]


@router.post("/{conversa_id}/handoff")
async def assume_conversa(
    conversa_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    operador: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        conversa = await conversa_service.start_handoff(db, conversa_id, operador)
        return {"status": conversa.status, "operador_id": str(conversa.operador_id)}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{conversa_id}/handoff")
async def release_conversa(
    conversa_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    operador: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        conversa = await conversa_service.end_handoff(db, conversa_id, operador)
        return {"status": conversa.status}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
