import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.campanha import Campanha, StatusCampanha
from src.models.operador import Operador
from src.models.segmento import Segmento
from src.services.auth_service import get_current_operador
from src.services import campanha_service
from src.agents import ads_agent

router = APIRouter(prefix="/campanhas", tags=["campanhas"])


class GerarCampanhaRequest(BaseModel):
    segmento_id: uuid.UUID | None = None
    instrucoes_adicionais: str | None = None


class EditCampanhaRequest(BaseModel):
    copy: str | None = None
    orcamento_sugerido: float | None = None


class RejeitarCampanhaRequest(BaseModel):
    motivo: str | None = None


def _serialize(campanha: Campanha, segmento: Segmento | None) -> dict:
    return {
        "id": str(campanha.id),
        "status": campanha.status,
        "copy": campanha.copy,
        "segmento": {"id": str(campanha.segmento_id), "nome": segmento.nome} if segmento else None,
        "publico_alvo": campanha.publico_alvo,
        "orcamento_sugerido": float(campanha.orcamento_sugerido) if campanha.orcamento_sugerido else None,
        "aprovada_por": str(campanha.aprovada_por) if campanha.aprovada_por else None,
        "aprovada_em": campanha.aprovada_em.isoformat() if campanha.aprovada_em else None,
        "criado_em": campanha.criado_em.isoformat(),
    }


@router.get("")
async def list_campanhas(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Operador, Depends(get_current_operador)],
    status: StatusCampanha | None = None,
    page: int = 1,
    limit: int = 20,
):
    q = select(Campanha).order_by(Campanha.criado_em.desc())
    if status:
        q = q.where(Campanha.status == status)
    q = q.offset((page - 1) * limit).limit(limit)

    result = await db.execute(q)
    campanhas = list(result.scalars().all())

    seg_ids = {c.segmento_id for c in campanhas if c.segmento_id}
    segmentos: dict[uuid.UUID, Segmento] = {}
    if seg_ids:
        s_result = await db.execute(select(Segmento).where(Segmento.id.in_(seg_ids)))
        segmentos = {s.id: s for s in s_result.scalars().all()}

    total = (await db.execute(select(func.count(Campanha.id)))).scalar_one()

    return {"total": total, "items": [_serialize(c, segmentos.get(c.segmento_id)) for c in campanhas]}


@router.post("/gerar", status_code=202)
async def gerar_campanha(
    body: GerarCampanhaRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Operador, Depends(get_current_operador)],
):
    campanha = await ads_agent.generate_campaign(db, body.segmento_id, body.instrucoes_adicionais)
    await db.commit()
    return {"campanha_id": str(campanha.id), "status": campanha.status}


@router.patch("/{campanha_id}")
async def edit_campanha(
    campanha_id: uuid.UUID,
    body: EditCampanhaRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        campanha = await campanha_service.edit(db, campanha_id, body.copy, body.orcamento_sugerido)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    seg = None
    if campanha.segmento_id:
        seg_result = await db.execute(select(Segmento).where(Segmento.id == campanha.segmento_id))
        seg = seg_result.scalar_one_or_none()
    return _serialize(campanha, seg)


@router.post("/{campanha_id}/aprovar")
async def aprovar_campanha(
    campanha_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    operador: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        campanha = await campanha_service.approve(db, campanha_id, operador)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {
        "status": campanha.status,
        "aprovada_por": str(campanha.aprovada_por),
        "aprovada_em": campanha.aprovada_em.isoformat() if campanha.aprovada_em else None,
    }


@router.post("/{campanha_id}/rejeitar")
async def rejeitar_campanha(
    campanha_id: uuid.UUID,
    body: RejeitarCampanhaRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        campanha = await campanha_service.reject(db, campanha_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": campanha.status}
