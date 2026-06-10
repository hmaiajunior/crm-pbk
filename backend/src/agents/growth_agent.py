"""Growth Agent: suggests conversion actions based on client events."""
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
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


async def has_open_acao(
    db: AsyncSession,
    cliente_id: uuid.UUID,
    tipo: TipoAcao,
    dedup_days: int = 7,
) -> bool:
    """True if the client already has an equivalent action still open (suggested or
    approved) within the dedup window — used to avoid duplicate suggestions/events.
    """
    since = datetime.now(timezone.utc) - timedelta(days=dedup_days)
    existing = await db.execute(
        select(func.count(AcaoAgente.id)).where(
            AcaoAgente.cliente_id == cliente_id,
            AcaoAgente.tipo == tipo,
            AcaoAgente.status.in_([StatusAcao.sugerida, StatusAcao.aprovada]),
            AcaoAgente.criado_em >= since,
        )
    )
    return existing.scalar_one() > 0


async def suggest_acao(
    db: AsyncSession,
    cliente: Cliente,
    tipo: TipoAcao,
    evento_id: uuid.UUID | None = None,
    dedup_days: int = 7,
) -> AcaoAgente | None:
    """Create a suggested action for a client, skipping if an equivalent one is
    still open. Unlike ``process_event`` there is no 24h-conversation gate, so it
    works for clients that never messaged Nino (cadastro/checkout scenarios).

    Returns the created action, or ``None`` when deduplicated.
    """
    if await has_open_acao(db, cliente.id, tipo, dedup_days):
        return None

    acao = AcaoAgente(
        tipo=tipo,
        agente=AgenteOrigem.growth_agent,
        cliente_id=cliente.id,
        evento_id=evento_id,
        conteudo_sugerido=_build_conteudo(cliente, tipo),
        status=StatusAcao.sugerida,
    )
    db.add(acao)
    await db.flush()
    return acao


def _build_conteudo(cliente: Cliente, tipo: TipoAcao) -> str:
    nome = cliente.nome or "cliente"
    if tipo == TipoAcao.convite_vip:
        return f"Olá {nome}! Você tem interesse em fazer parte do nosso grupo VIP com ofertas exclusivas? 🌟"
    if tipo == TipoAcao.oferta:
        return f"Oi {nome}! Temos uma oferta especial para você hoje. Posso te contar mais? 🎁"
    if tipo == TipoAcao.boas_vindas:
        return f"Olá {nome}! Que bom ter você por aqui 💛 Vi que você acabou de se cadastrar — posso te ajudar a escolher a primeira peça?"
    if tipo == TipoAcao.recuperacao_checkout:
        return f"Oi {nome}! Notei que você deixou alguns itens no carrinho 🛒 Quer que eu reserve para você antes que acabe?"
    if tipo == TipoAcao.reengajamento:
        return f"Olá {nome}! Faz um tempinho que conversamos por aqui 😊 Posso te mostrar as novidades que chegaram na loja?"
    return f"Olá {nome}! Como posso te ajudar hoje?"
