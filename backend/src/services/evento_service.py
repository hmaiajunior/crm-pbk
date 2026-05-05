import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.evento import Evento, TipoEvento
from src.models.mensagem import SentimentoMensagem
from src.models.cliente import Cliente


async def evaluate_and_emit(db: AsyncSession, cliente: Cliente, sentimento: SentimentoMensagem | None) -> Evento | None:
    """Generate an internal event based on message sentiment. Returns the created event or None."""
    if sentimento is None:
        return None

    tipo: TipoEvento | None = None
    if sentimento == SentimentoMensagem.negativo:
        tipo = TipoEvento.cliente_insatisfeito
    elif sentimento == SentimentoMensagem.positivo:
        tipo = TipoEvento.cliente_interessado

    if not tipo:
        return None

    evento = Evento(tipo=tipo, cliente_id=cliente.id, payload={"sentimento": sentimento})
    db.add(evento)
    await db.flush()
    return evento


async def emit(db: AsyncSession, tipo: TipoEvento, cliente_id: uuid.UUID, payload: dict | None = None) -> Evento:
    evento = Evento(tipo=tipo, cliente_id=cliente_id, payload=payload or {})
    db.add(evento)
    await db.flush()
    return evento
