from src.events.bus import bus
from src.database import AsyncSessionLocal
from sqlalchemy import select


async def _handle_segmentacao(payload: dict) -> None:
    from src.models.cliente import Cliente
    from src.services.segmentacao_service import evaluate_client

    cliente_id = payload.get("cliente_id")
    if not cliente_id:
        return
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
            cliente = result.scalar_one_or_none()
            if cliente:
                await evaluate_client(db, cliente)
                await db.commit()
        except Exception:
            await db.rollback()


async def _handle_growth(payload: dict) -> None:
    from src.models.cliente import Cliente
    from src.agents.growth_agent import process_event

    cliente_id = payload.get("cliente_id")
    tipo_evento = payload.get("tipo_evento")
    if not cliente_id or not tipo_evento:
        return
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
            cliente = result.scalar_one_or_none()
            if cliente:
                await process_event(db, cliente, tipo_evento)
                await db.commit()
        except Exception:
            await db.rollback()


def subscribe_all() -> None:
    bus.subscribe("mensagem_recebida", _handle_segmentacao)
    bus.subscribe("cliente_insatisfeito", _handle_segmentacao)
    bus.subscribe("cliente_interessado", _handle_segmentacao)
    bus.subscribe("cliente_interessado", _handle_growth)
    bus.subscribe("cliente_pronto_compra", _handle_growth)
