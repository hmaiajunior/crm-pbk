"""Ads Agent: generates campaign copy, audience and budget for a segment."""
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.campanha import Campanha, StatusCampanha
from src.models.segmento import ClienteSegmento, Segmento


async def generate_campaign(
    db: AsyncSession,
    segmento_id: uuid.UUID | None,
    instrucoes_adicionais: str | None = None,
) -> Campanha:
    segmento_nome = "Geral"
    total_clientes = 0

    if segmento_id:
        seg_result = await db.execute(select(Segmento).where(Segmento.id == segmento_id))
        segmento = seg_result.scalar_one_or_none()
        if segmento:
            segmento_nome = segmento.nome
            count_result = await db.execute(
                select(func.count(ClienteSegmento.cliente_id)).where(
                    ClienteSegmento.segmento_id == segmento_id
                )
            )
            total_clientes = count_result.scalar_one() or 0

    copy_text = _build_copy(segmento_nome, instrucoes_adicionais)
    orcamento = _estimate_budget(total_clientes)

    campanha = Campanha(
        segmento_id=segmento_id,
        copy=copy_text,
        publico_alvo={
            "segmento": segmento_nome,
            "total_clientes": total_clientes,
            "criterios": instrucoes_adicionais or "",
        },
        orcamento_sugerido=orcamento,
        status=StatusCampanha.aguardando_aprovacao,
        gerada_por="ads_agent",
    )
    db.add(campanha)
    await db.flush()
    return campanha


def _build_copy(segmento_nome: str, instrucoes: str | None) -> str:
    base = f"Campanha especial para {segmento_nome} da Playbekids!"
    if instrucoes:
        base += f" {instrucoes}"
    return (
        f"{base}\n\n"
        "Descubra nossa seleção exclusiva de produtos infantis com qualidade e carinho. "
        "Aproveite condições especiais preparadas para você! 🧸✨"
    )


def _estimate_budget(total_clientes: int) -> float:
    base = 50.0
    per_client = 0.5
    return round(base + per_client * total_clientes, 2)
