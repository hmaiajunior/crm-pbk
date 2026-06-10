import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.cliente import ClassificacaoCliente, Cliente
from src.integrations.playbekids_db import get_ultima_compra_by_phone


async def get_or_create_by_phone(
    db: AsyncSession,
    telefone: str,
    email: str | None = None,
    nome: str | None = None,
) -> tuple[Cliente, bool]:
    """Return (cliente, created). Creates a new client if phone is not registered.

    When email/nome are provided (e.g. from a site cadastro), they backfill the
    record if currently empty — existing values are never overwritten.
    """
    result = await db.execute(select(Cliente).where(Cliente.telefone == telefone))
    cliente = result.scalar_one_or_none()
    if cliente:
        if email and not cliente.email:
            cliente.email = email
        if nome and not cliente.nome:
            cliente.nome = nome
        return cliente, False

    now = datetime.now(timezone.utc)
    cliente = Cliente(
        telefone=telefone,
        email=email,
        nome=nome,
        classificacao=ClassificacaoCliente.lead,
        opt_in=True,
        opt_in_registrado_em=now,
        primeira_interacao_em=now,
        ultima_interacao_em=now,
    )
    db.add(cliente)
    await db.flush()
    return cliente, True


async def upsert_from_site(
    db: AsyncSession,
    telefone: str | None,
    email: str | None = None,
    nome: str | None = None,
) -> tuple[Cliente | None, bool]:
    """Upsert a client coming from a Playbekids site source (cadastro/checkout).

    Match priority: telefone (the CRM unique key), then email as fallback.
    Since ``cliente.telefone`` is required, a brand-new client can only be created
    when a phone is present — site rows with email only and no existing match are
    skipped (returns (None, False)).
    """
    if telefone:
        return await get_or_create_by_phone(db, telefone, email=email, nome=nome)

    if email:
        result = await db.execute(select(Cliente).where(Cliente.email == email))
        cliente = result.scalar_one_or_none()
        if cliente:
            if nome and not cliente.nome:
                cliente.nome = nome
            return cliente, False

        now = datetime.now(timezone.utc)
        cliente = Cliente(
            telefone=None,
            email=email,
            nome=nome,
            classificacao=ClassificacaoCliente.lead,
            opt_in=True,
            opt_in_registrado_em=now,
            primeira_interacao_em=now,
            ultima_interacao_em=now,
        )
        db.add(cliente)
        await db.flush()
        return cliente, True

    # Neither phone nor email → cannot represent this lead.
    return None, False


async def update_ultima_interacao(db: AsyncSession, cliente: Cliente) -> None:
    cliente.ultima_interacao_em = datetime.now(timezone.utc)
    await db.flush()


async def update_classification(db: AsyncSession, cliente: Cliente) -> None:
    """Recalculate client classification based on purchase count and last interaction."""
    now = datetime.now(timezone.utc)
    threshold_inativo = now - timedelta(days=30)

    # Inactivity takes precedence
    last_activity = max(
        filter(None, [cliente.ultima_interacao_em, cliente.ultima_compra_em]),
        default=cliente.primeira_interacao_em,
    )
    if last_activity < threshold_inativo:
        cliente.classificacao = ClassificacaoCliente.inativo
        return

    _, total_compras = await get_ultima_compra_by_phone(cliente.telefone)
    if total_compras >= 2:
        cliente.classificacao = ClassificacaoCliente.cliente_recorrente
    elif total_compras == 1:
        cliente.classificacao = ClassificacaoCliente.cliente
    else:
        cliente.classificacao = ClassificacaoCliente.lead

    await db.flush()


async def sync_from_playbekids(db: AsyncSession, cliente: Cliente) -> None:
    """Update ultima_compra_em from Playbekids DB and recalculate classification."""
    ultima_compra_em, _ = await get_ultima_compra_by_phone(cliente.telefone)
    if ultima_compra_em:
        cliente.ultima_compra_em = ultima_compra_em
    await update_classification(db, cliente)


async def get_by_id(db: AsyncSession, cliente_id: uuid.UUID) -> Cliente | None:
    result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    return result.scalar_one_or_none()
