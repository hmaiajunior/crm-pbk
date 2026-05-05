import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class StatusCampanha(str, Enum):
    rascunho = "rascunho"
    aguardando_aprovacao = "aguardando_aprovacao"
    aprovada = "aprovada"
    publicada = "publicada"
    rejeitada = "rejeitada"


class Campanha(Base):
    __tablename__ = "campanha"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segmento_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.segmento.id"), nullable=True)
    copy: Mapped[str] = mapped_column(Text, nullable=False)
    publico_alvo: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    orcamento_sugerido: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[StatusCampanha] = mapped_column(String(30), nullable=False, default=StatusCampanha.rascunho)
    gerada_por: Mapped[str] = mapped_column(String(50), default="ads_agent", nullable=False)
    aprovada_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.operador.id"), nullable=True)
    aprovada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
