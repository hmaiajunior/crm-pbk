"""READ-ONLY access to the Playbekids e-commerce database (Supabase / Prisma).

Source schema (public, camelCase quoted identifiers):
  - "User"          : site accounts. role ∈ (RETAIL, WHOLESALE, ADMIN),
                      phone (nullable), email, name, "createdAt".
  - "Order"         : orders. "paymentStatus" = 'APPROVED' means a paid purchase.
                      Linked to a user via "userId".
  - "AbandonedCart" : carts left at checkout. Linked via "userId"; has subtotal,
                      "createdAt".

Every query here is a pure SELECT — the CRM never writes to Playbekids.
A confirmed/paid purchase is defined as an Order with "paymentStatus" = 'APPROVED'.
"""
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from src.config import settings

_engine = create_async_engine(settings.PLAYBEKIDS_DB_URL, echo=False, pool_pre_ping=True)

# A purchase counts as confirmed only when the payment was approved.
_PAID = "o.\"paymentStatus\"::text = 'APPROVED'"


def _naive_utc(dt: datetime) -> datetime:
    """Playbekids columns are `timestamp without time zone` — bind params as naive UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _aware_utc(dt: datetime | None) -> datetime | None:
    """Tag naive Playbekids timestamps as UTC so CRM-side comparisons stay consistent."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def get_ultima_compra_by_phone(telefone: str) -> tuple[datetime | None, int]:
    """Return (ultima_compra_em, total_compras) for a given phone number.
    Returns (None, 0) if no purchases found or on any error.
    """
    query = text(f"""
        SELECT MAX(o."createdAt") AS ultima_compra_em, COUNT(*) AS total_compras
        FROM public."Order" o
        JOIN public."User" u ON u.id = o."userId"
        WHERE {_PAID} AND u.phone = :telefone
    """)
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(query, {"telefone": telefone})
            row = result.fetchone()
            if row and row.ultima_compra_em:
                return _aware_utc(row.ultima_compra_em), int(row.total_compras)
    except Exception:
        # Fail gracefully — ultima_compra_em is nullable in the CRM schema
        pass
    return None, 0


async def get_purchases_by_phone(telefone: str) -> list[datetime]:
    """Return all approved purchase timestamps for a given phone, newest first."""
    query = text(f"""
        SELECT o."createdAt" AS criado_em
        FROM public."Order" o
        JOIN public."User" u ON u.id = o."userId"
        WHERE {_PAID} AND u.phone = :telefone
        ORDER BY o."createdAt" DESC
    """)
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(query, {"telefone": telefone})
            return [_aware_utc(r.criado_em) for r in result.fetchall() if r.criado_em]
    except Exception:
        return []


async def get_cadastros_sem_pedido(since: datetime) -> list[dict]:
    """Wholesale (atacado) registrations created since `since` with NO approved
    order yet. READ-ONLY.

    Returns dicts: {telefone, email, nome, cadastrado_em}.
    """
    query = text(f"""
        SELECT u.phone AS telefone, u.email, u.name AS nome,
               u."createdAt" AS cadastrado_em
        FROM public."User" u
        WHERE u.role::text = 'WHOLESALE'
          AND u."createdAt" >= :since
          AND NOT EXISTS (
              SELECT 1 FROM public."Order" o
              WHERE o."userId" = u.id AND {_PAID}
          )
        ORDER BY u."createdAt"
    """)
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(query, {"since": _naive_utc(since)})
            return [
                {"telefone": r.telefone, "email": r.email, "nome": r.nome,
                 "cadastrado_em": _aware_utc(r.cadastrado_em)}
                for r in result.fetchall()
            ]
    except Exception:
        return []


async def get_checkouts_abandonados(since: datetime) -> list[dict]:
    """Abandoned carts created since `since` whose user has NO approved order
    placed at/after the cart (i.e. checkout reached, payment not completed).
    One row per user (most recent cart). READ-ONLY.

    Returns dicts: {telefone, email, nome, checkout_em, valor}.
    """
    query = text(f"""
        SELECT DISTINCT ON (u.id)
               u.phone AS telefone, u.email, u.name AS nome,
               ac."createdAt" AS checkout_em, ac.subtotal AS valor
        FROM public."AbandonedCart" ac
        JOIN public."User" u ON u.id = ac."userId"
        WHERE ac."createdAt" >= :since
          AND NOT EXISTS (
              SELECT 1 FROM public."Order" o
              WHERE o."userId" = u.id AND {_PAID}
                AND o."createdAt" >= ac."createdAt"
          )
        ORDER BY u.id, ac."createdAt" DESC
    """)
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(query, {"since": _naive_utc(since)})
            return [
                {"telefone": r.telefone, "email": r.email, "nome": r.nome,
                 "checkout_em": _aware_utc(r.checkout_em),
                 "valor": float(r.valor) if r.valor is not None else None}
                for r in result.fetchall()
            ]
    except Exception:
        return []


async def get_all_purchases() -> list[dict]:
    """Return all approved purchases grouped by phone for bulk sync."""
    query = text(f"""
        SELECT u.phone AS telefone,
               MAX(o."createdAt") AS ultima_compra_em,
               COUNT(*) AS total_compras
        FROM public."Order" o
        JOIN public."User" u ON u.id = o."userId"
        WHERE {_PAID} AND u.phone IS NOT NULL
        GROUP BY u.phone
    """)
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(query)
            return [
                {"telefone": r.telefone, "ultima_compra_em": _aware_utc(r.ultima_compra_em),
                 "total_compras": int(r.total_compras)}
                for r in result.fetchall()
            ]
    except Exception:
        return []
