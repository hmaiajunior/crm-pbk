import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.acao_agente import AcaoAgente, StatusAcao
from src.models.cliente import Cliente
from src.models.operador import Operador
from src.services.auth_service import get_current_operador
from src.services import acao_agente_service

router = APIRouter(prefix="/acoes", tags=["acoes"])


def _serialize(acao: AcaoAgente, cliente: Cliente | None) -> dict:
    return {
        "id": str(acao.id),
        "tipo": acao.tipo,
        "agente": acao.agente,
        "cliente": {"id": str(acao.cliente_id), "nome": cliente.nome if cliente else None},
        "conteudo_sugerido": acao.conteudo_sugerido,
        "status": acao.status,
        "criado_em": acao.criado_em.isoformat(),
    }


@router.get("")
async def list_acoes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Operador, Depends(get_current_operador)],
    status: StatusAcao = StatusAcao.sugerida,
    page: int = 1,
    limit: int = 20,
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(AcaoAgente)
        .where(AcaoAgente.status == status)
        .order_by(AcaoAgente.criado_em.desc())
        .offset(offset)
        .limit(limit)
    )
    acoes = list(result.scalars().all())

    cliente_ids = {a.cliente_id for a in acoes}
    clientes: dict[uuid.UUID, Cliente] = {}
    if cliente_ids:
        c_result = await db.execute(select(Cliente).where(Cliente.id.in_(cliente_ids)))
        clientes = {c.id: c for c in c_result.scalars().all()}

    return {"items": [_serialize(a, clientes.get(a.cliente_id)) for a in acoes]}


@router.post("/{acao_id}/aprovar")
async def aprovar_acao(
    acao_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    operador: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        acao = await acao_agente_service.approve(db, acao_id, operador)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": acao.status, "executada_em": acao.executada_em.isoformat() if acao.executada_em else None}


@router.post("/{acao_id}/rejeitar")
async def rejeitar_acao(
    acao_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    operador: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        acao = await acao_agente_service.reject(db, acao_id, operador)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": acao.status}
