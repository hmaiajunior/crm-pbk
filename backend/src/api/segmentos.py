from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.segmento import ClienteSegmento, Segmento
from src.services.auth_service import get_current_operador

router = APIRouter(prefix="/segmentos", tags=["segmentos"])


@router.get("")
async def list_segmentos(
    db: Annotated[AsyncSession, Depends(get_db)],
    _=Depends(get_current_operador),
):
    result = await db.execute(
        select(
            Segmento.id,
            Segmento.nome,
            Segmento.descricao,
            func.count(ClienteSegmento.cliente_id).label("total_clientes"),
        )
        .outerjoin(ClienteSegmento, ClienteSegmento.segmento_id == Segmento.id)
        .group_by(Segmento.id)
        .order_by(Segmento.nome)
    )
    rows = result.all()
    return [
        {
            "id": str(r.id),
            "nome": r.nome,
            "descricao": r.descricao,
            "total_clientes": r.total_clientes,
        }
        for r in rows
    ]
