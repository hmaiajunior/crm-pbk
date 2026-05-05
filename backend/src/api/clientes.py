import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.cliente import ClassificacaoCliente, Cliente
from src.models.conversa import Conversa
from src.models.mensagem import Mensagem
from src.models.segmento import ClienteSegmento
from src.services.auth_service import get_current_operador

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("")
async def list_clientes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _=Depends(get_current_operador),
    segmento_id: uuid.UUID | None = Query(default=None),
    classificacao: ClassificacaoCliente | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = select(Cliente)
    if segmento_id:
        query = query.join(ClienteSegmento, ClienteSegmento.cliente_id == Cliente.id).where(ClienteSegmento.segmento_id == segmento_id)
    if classificacao:
        query = query.where(Cliente.classificacao == classificacao)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    query = query.offset((page - 1) * limit).limit(limit).order_by(Cliente.ultima_interacao_em.desc())
    result = await db.execute(query)
    clientes = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": str(c.id),
                "telefone": c.telefone,
                "nome": c.nome,
                "classificacao": c.classificacao,
                "ultima_interacao_em": c.ultima_interacao_em.isoformat() if c.ultima_interacao_em else None,
            }
            for c in clientes
        ],
    }


@router.get("/{cliente_id}")
async def get_cliente(
    cliente_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _=Depends(get_current_operador),
):
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    cliente = result.scalar_one_or_none()
    if not cliente:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Assemble timeline: mensagens ordered by time
    conv_result = await db.execute(select(Conversa).where(Conversa.cliente_id == cliente_id))
    conversas = conv_result.scalars().all()
    conversa_ids = [c.id for c in conversas]

    timeline = []
    if conversa_ids:
        msg_result = await db.execute(
            select(Mensagem).where(Mensagem.conversa_id.in_(conversa_ids)).order_by(Mensagem.enviada_em)
        )
        for m in msg_result.scalars().all():
            timeline.append({
                "tipo": "mensagem",
                "timestamp": m.enviada_em.isoformat(),
                "dados": {"conteudo": m.conteudo, "direcao": m.direcao, "sentimento": m.sentimento, "tema": m.tema},
            })

    if cliente.ultima_compra_em:
        timeline.append({"tipo": "compra", "timestamp": cliente.ultima_compra_em.isoformat(), "dados": {}})

    timeline.sort(key=lambda x: x["timestamp"])

    return {
        "id": str(cliente.id),
        "telefone": cliente.telefone,
        "nome": cliente.nome,
        "classificacao": cliente.classificacao,
        "opt_in": cliente.opt_in,
        "primeira_interacao_em": cliente.primeira_interacao_em.isoformat(),
        "ultima_interacao_em": cliente.ultima_interacao_em.isoformat(),
        "ultima_compra_em": cliente.ultima_compra_em.isoformat() if cliente.ultima_compra_em else None,
        "timeline": timeline,
    }
