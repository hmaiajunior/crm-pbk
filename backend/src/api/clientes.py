import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.integrations import playbekids_db
from src.models.acao_agente import AcaoAgente, StatusAcao
from src.models.cliente import ClassificacaoCliente, Cliente
from src.models.conversa import Conversa
from src.models.mensagem import DirecaoMensagem, Mensagem
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


def _days_since(ts: datetime | None) -> int | None:
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - ts
    return max(delta.days, 0)


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

    conv_result = await db.execute(select(Conversa).where(Conversa.cliente_id == cliente_id))
    conversas = conv_result.scalars().all()
    conversa_ids = [c.id for c in conversas]

    mensagens: list[Mensagem] = []
    if conversa_ids:
        msg_result = await db.execute(
            select(Mensagem).where(Mensagem.conversa_id.in_(conversa_ids)).order_by(Mensagem.enviada_em)
        )
        mensagens = list(msg_result.scalars().all())

    timeline: list[dict] = [
        {
            "tipo": "mensagem",
            "timestamp": m.enviada_em.isoformat(),
            "dados": {"conteudo": m.conteudo, "direcao": m.direcao, "sentimento": m.sentimento, "tema": m.tema},
        }
        for m in mensagens
    ]

    compras = await playbekids_db.get_purchases_by_phone(cliente.telefone)
    for c in compras:
        timeline.append({"tipo": "compra", "timestamp": c.isoformat(), "dados": {}})

    timeline.sort(key=lambda x: x["timestamp"])

    acoes_result = await db.execute(
        select(AcaoAgente)
        .where(AcaoAgente.cliente_id == cliente_id, AcaoAgente.status == StatusAcao.sugerida)
        .order_by(AcaoAgente.criado_em.desc())
    )
    acoes_pendentes = list(acoes_result.scalars().all())

    sentimento_counter: Counter[str] = Counter()
    tema_counter: Counter[str] = Counter()
    mensagens_entrada = 0
    mensagens_saida = 0
    for m in mensagens:
        if m.direcao == DirecaoMensagem.entrada.value:
            mensagens_entrada += 1
        elif m.direcao == DirecaoMensagem.saida.value:
            mensagens_saida += 1
        if m.sentimento:
            sentimento_counter[m.sentimento] += 1
        if m.tema:
            tema_counter[m.tema] += 1

    tema_dominante = tema_counter.most_common(1)[0][0] if tema_counter else None

    insights = {
        "total_mensagens": len(mensagens),
        "mensagens_entrada": mensagens_entrada,
        "mensagens_saida": mensagens_saida,
        "sentimento_distribuicao": {
            "positivo": sentimento_counter.get("positivo", 0),
            "neutro": sentimento_counter.get("neutro", 0),
            "negativo": sentimento_counter.get("negativo", 0),
        },
        "tema_dominante": tema_dominante,
        "dias_desde_ultima_interacao": _days_since(cliente.ultima_interacao_em),
        "dias_desde_ultima_compra": _days_since(cliente.ultima_compra_em),
        "total_compras": len(compras),
        "total_acoes_pendentes": len(acoes_pendentes),
    }

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
        "insights": insights,
        "acoes_pendentes": [
            {
                "id": str(a.id),
                "tipo": a.tipo,
                "agente": a.agente,
                "conteudo_sugerido": a.conteudo_sugerido,
                "status": a.status,
                "criado_em": a.criado_em.isoformat(),
            }
            for a in acoes_pendentes
        ],
    }
