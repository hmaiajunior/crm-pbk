from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.cliente import Cliente, ClassificacaoCliente
from src.models.mensagem import SentimentoMensagem
from src.models.segmento import ClienteSegmento, Segmento


async def _get_segmento_by_nome(db: AsyncSession, nome: str) -> Segmento | None:
    result = await db.execute(select(Segmento).where(Segmento.nome == nome))
    return result.scalar_one_or_none()


async def evaluate_client(db: AsyncSession, cliente: Cliente) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff_inativo = now - timedelta(days=30)

    await db.execute(delete(ClienteSegmento).where(ClienteSegmento.cliente_id == cliente.id))

    seg_names: list[str] = []

    if cliente.classificacao == ClassificacaoCliente.lead and cliente.primeira_interacao_em >= (now - timedelta(days=7)):
        seg_names.append("Clientes Novos")

    if cliente.ultima_interacao_em and cliente.ultima_interacao_em >= cutoff_inativo:
        seg_names.append("Clientes Ativos")

    if cliente.ultima_interacao_em and cliente.ultima_interacao_em < cutoff_inativo:
        seg_names.append("Clientes Inativos")

    if cliente.opt_in and not cliente.ultima_compra_em:
        seg_names.append("Engajados sem Compra")

    from sqlalchemy import func
    from src.models.mensagem import Mensagem
    from src.models.conversa import Conversa

    neg_count_result = await db.execute(
        select(func.count(Mensagem.id))
        .join(Conversa, Conversa.id == Mensagem.conversa_id)
        .where(
            Conversa.cliente_id == cliente.id,
            Mensagem.sentimento == SentimentoMensagem.negativo,
        )
    )
    neg_count = neg_count_result.scalar_one()
    if neg_count >= 3:
        seg_names.append("Sentimento Negativo Recorrente")

    if cliente.classificacao == ClassificacaoCliente.lead and cliente.opt_in:
        seg_names.append("Lead Quente")

    for nome in seg_names:
        segmento = await _get_segmento_by_nome(db, nome)
        if segmento:
            db.add(ClienteSegmento(cliente_id=cliente.id, segmento_id=segmento.id))
