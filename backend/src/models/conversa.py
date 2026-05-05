import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class CanalConversa(str, Enum):
    whatsapp = "whatsapp"


class StatusConversa(str, Enum):
    ativa = "ativa"
    em_handoff = "em_handoff"
    encerrada = "encerrada"


class Conversa(Base):
    __tablename__ = "conversa"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.cliente.id"), nullable=False)
    canal: Mapped[CanalConversa] = mapped_column(String(20), nullable=False, default=CanalConversa.whatsapp)
    status: Mapped[StatusConversa] = mapped_column(String(20), nullable=False, default=StatusConversa.ativa)
    operador_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.operador.id"), nullable=True)
    handoff_iniciado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    iniciada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    encerrada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
