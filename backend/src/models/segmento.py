import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, PrimaryKeyConstraint, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class Segmento(Base):
    __tablename__ = "segmento"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterios: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ClienteSegmento(Base):
    __tablename__ = "cliente_segmento"
    __table_args__ = (
        PrimaryKeyConstraint("cliente_id", "segmento_id"),
        {"schema": "crm"},
    )

    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.cliente.id"), nullable=False)
    segmento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.segmento.id"), nullable=False)
    atribuido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
