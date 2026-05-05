import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class TipoAcao(str, Enum):
    convite_vip = "convite_vip"
    oferta = "oferta"
    follow_up = "follow_up"


class AgenteOrigem(str, Enum):
    growth_agent = "growth_agent"
    ads_agent = "ads_agent"


class StatusAcao(str, Enum):
    sugerida = "sugerida"
    aprovada = "aprovada"
    executada = "executada"
    rejeitada = "rejeitada"


class AcaoAgente(Base):
    __tablename__ = "acao_agente"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo: Mapped[TipoAcao] = mapped_column(String(20), nullable=False)
    agente: Mapped[AgenteOrigem] = mapped_column(String(20), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.cliente.id"), nullable=False)
    evento_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.evento.id"), nullable=True)
    conteudo_sugerido: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[StatusAcao] = mapped_column(String(20), nullable=False, default=StatusAcao.sugerida)
    aprovada_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.operador.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    executada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
