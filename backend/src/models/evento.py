import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class TipoEvento(str, Enum):
    cliente_interessado = "cliente_interessado"
    cliente_inativo = "cliente_inativo"
    cliente_insatisfeito = "cliente_insatisfeito"
    cliente_pronto_compra = "cliente_pronto_compra"


class Evento(Base):
    __tablename__ = "evento"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoEvento] = mapped_column(String(40), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.cliente.id"), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    processado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
