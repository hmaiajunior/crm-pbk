from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from src.config import settings

_engine = create_async_engine(settings.PLAYBEKIDS_DB_URL, echo=False, pool_pre_ping=True)


async def get_ultima_compra_by_phone(telefone: str) -> tuple[datetime | None, int]:
    """Return (ultima_compra_em, total_compras) for a given phone number.
    Returns (None, 0) if no purchases found or on any error.
    """
    query = text("""
        SELECT MAX(criado_em) AS ultima_compra_em, COUNT(*) AS total_compras
        FROM public.pedidos
        WHERE status = 'confirmado'
          AND telefone_cliente = :telefone
    """)
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(query, {"telefone": telefone})
            row = result.fetchone()
            if row and row.ultima_compra_em:
                return row.ultima_compra_em, int(row.total_compras)
    except Exception:
        # Fail gracefully — ultima_compra_em is nullable in the CRM schema
        pass
    return None, 0


async def get_purchases_by_phone(telefone: str) -> list[datetime]:
    """Return all confirmed purchase timestamps for a given phone, newest first.
    Returns empty list if none or on any error.
    """
    query = text("""
        SELECT criado_em
        FROM public.pedidos
        WHERE status = 'confirmado'
          AND telefone_cliente = :telefone
        ORDER BY criado_em DESC
    """)
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(query, {"telefone": telefone})
            return [r.criado_em for r in result.fetchall() if r.criado_em]
    except Exception:
        return []


async def get_all_purchases() -> list[dict]:
    """Return all confirmed purchases grouped by phone for bulk sync."""
    query = text("""
        SELECT telefone_cliente, MAX(criado_em) AS ultima_compra_em, COUNT(*) AS total_compras
        FROM public.pedidos
        WHERE status = 'confirmado'
        GROUP BY telefone_cliente
    """)
    try:
        async with _engine.connect() as conn:
            result = await conn.execute(query)
            return [{"telefone": r.telefone_cliente, "ultima_compra_em": r.ultima_compra_em, "total_compras": int(r.total_compras)} for r in result.fetchall()]
    except Exception:
        return []
