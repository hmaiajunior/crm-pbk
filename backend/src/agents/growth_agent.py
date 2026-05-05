"""Growth Agent: suggests conversion actions based on client events."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.acao_agente import AcaoAgente, TipoAcao, AgenteOrigem, StatusAcao
from src.models.cliente import Cliente
from src.models.conversa import Conversa, StatusConversa


async def process_event(db: AsyncSession, cliente: Cliente, tipo_evento: str) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_24h = now - timedelta(hours=24)

    last_conv_result = await db.execute(
        select(Conversa)
        .where(
            Conversa.cliente_id == cliente.id,
            Conversa.status != StatusConversa.encerrada,
        )
        .order_by(Conversa.iniciada_em.desc())
        .limit(1)
    )
    last_conv = last_conv_result.scalar_one_or_none()

    if not last_conv or last_conv.iniciada_em < window_24h:
        return

    tipo_map = {
        "cliente_interessado": TipoAcao.convite_vip,
        "cliente_pronto_compra": TipoAcao.oferta,
    }
    tipo_acao = tipo_map.get(tipo_evento, TipoAcao.follow_up)

    conteudo = _build_conteudo(cliente, tipo_acao)

    acao = AcaoAgente(
        tipo=tipo_acao,
        agente=AgenteOrigem.growth_agent,
        cliente_id=cliente.id,
        conteudo_sugerido=conteudo,
        status=StatusAcao.sugerida,
    )
    db.add(acao)


def _build_conteudo(cliente: Cliente, tipo: TipoAcao) -> str:
    nome = cliente.nome or "cliente"
    if tipo == TipoAcao.convite_vip:
        return f"Olá {nome}! Você tem interesse em fazer parte do nosso grupo VIP com ofertas exclusivas? 🌟"
    if tipo == TipoAcao.oferta:
        return f"Oi {nome}! Temos uma oferta especial para você hoje. Posso te contar mais? 🎁"
    return f"Olá {nome}! Como posso te ajudar hoje?"
