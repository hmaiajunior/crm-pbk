"""Growth sync job.

Periodically reads the Playbekids site data (READ-ONLY) plus internal CRM data,
detects the three growth scenarios and produces suggested actions for operators:

  1. cadastro_sem_pedido   — registered on the site, no confirmed order  -> boas_vindas
  2. checkout_abandonado   — reached checkout, no confirmed order        -> recuperacao_checkout
  3. conversou_sem_acao    — talked to Nino, no order on the site        -> reengajamento

Every write happens only in the CRM schema. The Playbekids DB is never written to.
Actions are deduplicated per (cliente, tipo) via growth_agent.suggest_acao.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.agents import growth_agent
from src.integrations.playbekids_db import (
    get_all_purchases,
    get_cadastros_sem_pedido,
    get_checkouts_abandonados,
)
from src.models.acao_agente import TipoAcao
from src.models.cliente import Cliente
from src.models.conversa import Conversa
from src.models.evento import TipoEvento
from src.models.mensagem import Mensagem
from src.services import cliente_service, evento_service, segmentacao_service

logger = logging.getLogger(__name__)


async def run_growth_sync(db: AsyncSession) -> dict:
    """Run one full growth sync pass. Returns a stats dict."""
    now = datetime.now(timezone.utc)
    stats = {
        "pedidos_sync": 0,
        "cadastro_sem_pedido": 0,
        "checkout_abandonado": 0,
        "conversou_sem_acao": 0,
    }
    # Clients that already received an action in this run — avoids stacking a
    # reengajamento on top of a boas_vindas/recuperacao for the same person.
    acted: set = set()

    # 1. Refresh purchase data for existing clients (bulk, READ-ONLY).
    await _sync_pedidos(db, stats)

    # 2. Cadastro sem pedido -> boas_vindas
    since_cad = now - timedelta(days=settings.CADASTRO_LOOKBACK_DAYS)
    for row in await get_cadastros_sem_pedido(since_cad):
        cliente = await _upsert(db, row)
        if cliente is None:
            continue
        if await growth_agent.has_open_acao(db, cliente.id, TipoAcao.boas_vindas, settings.ACAO_DEDUP_DAYS):
            continue
        evento = await evento_service.emit(
            db, TipoEvento.cadastro_sem_pedido, cliente.id,
            {"cadastrado_em": _iso(row.get("cadastrado_em"))},
        )
        await growth_agent.suggest_acao(
            db, cliente, TipoAcao.boas_vindas, evento.id, settings.ACAO_DEDUP_DAYS
        )
        await segmentacao_service.evaluate_client(db, cliente)
        stats["cadastro_sem_pedido"] += 1
        acted.add(cliente.id)

    # 3. Checkout abandonado -> recuperacao_checkout
    since_chk = now - timedelta(days=settings.CHECKOUT_LOOKBACK_DAYS)
    for row in await get_checkouts_abandonados(since_chk):
        cliente = await _upsert(db, row)
        if cliente is None:
            continue
        if await growth_agent.has_open_acao(db, cliente.id, TipoAcao.recuperacao_checkout, settings.ACAO_DEDUP_DAYS):
            continue
        evento = await evento_service.emit(
            db, TipoEvento.checkout_abandonado, cliente.id,
            {"checkout_em": _iso(row.get("checkout_em")), "valor": row.get("valor")},
        )
        await growth_agent.suggest_acao(
            db, cliente, TipoAcao.recuperacao_checkout, evento.id, settings.ACAO_DEDUP_DAYS
        )
        await segmentacao_service.evaluate_client(db, cliente)
        stats["checkout_abandonado"] += 1
        acted.add(cliente.id)

    # 4. Conversou no Nino, sem compra no site -> reengajamento
    since_conv = now - timedelta(days=settings.CONVERSA_LOOKBACK_DAYS)
    for cliente in await _clientes_conversaram_sem_compra(db, since_conv):
        if cliente.id in acted:
            continue
        if await growth_agent.has_open_acao(db, cliente.id, TipoAcao.reengajamento, settings.ACAO_DEDUP_DAYS):
            continue
        evento = await evento_service.emit(
            db, TipoEvento.conversou_sem_acao, cliente.id, {}
        )
        await growth_agent.suggest_acao(
            db, cliente, TipoAcao.reengajamento, evento.id, settings.ACAO_DEDUP_DAYS
        )
        await segmentacao_service.evaluate_client(db, cliente)
        stats["conversou_sem_acao"] += 1

    await db.commit()
    logger.info("growth sync done: %s", stats)
    return stats


async def _sync_pedidos(db: AsyncSession, stats: dict) -> None:
    """Update ultima_compra_em/classification for clients with confirmed orders."""
    purchases = await get_all_purchases()
    by_phone = {p["telefone"]: p for p in purchases if p.get("telefone")}
    if not by_phone:
        return
    result = await db.execute(
        select(Cliente).where(Cliente.telefone.in_(list(by_phone.keys())))
    )
    for cliente in result.scalars():
        info = by_phone[cliente.telefone]
        if info.get("ultima_compra_em"):
            cliente.ultima_compra_em = info["ultima_compra_em"]
        await cliente_service.update_classification(db, cliente)
        await segmentacao_service.evaluate_client(db, cliente)
        stats["pedidos_sync"] += 1


async def _upsert(db: AsyncSession, row: dict) -> Cliente | None:
    cliente, _ = await cliente_service.upsert_from_site(
        db, row.get("telefone"), row.get("email"), row.get("nome")
    )
    return cliente


async def _clientes_conversaram_sem_compra(
    db: AsyncSession, since: datetime
) -> list[Cliente]:
    """Clients with a Nino message within the window and no confirmed purchase."""
    result = await db.execute(
        select(Cliente)
        .join(Conversa, Conversa.cliente_id == Cliente.id)
        .join(Mensagem, Mensagem.conversa_id == Conversa.id)
        .where(
            Mensagem.enviada_em >= since,
            Cliente.ultima_compra_em.is_(None),
        )
        .distinct()
    )
    return list(result.scalars())


def _iso(value) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None
