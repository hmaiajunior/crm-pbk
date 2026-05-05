import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class ClassificacaoCliente(str, Enum):
    lead = "lead"
    cliente = "cliente"
    cliente_recorrente = "cliente_recorrente"
    inativo = "inativo"


class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telefone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    classificacao: Mapped[ClassificacaoCliente] = mapped_column(String(30), nullable=False, default=ClassificacaoCliente.lead)
    opt_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    opt_in_registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    primeira_interacao_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    ultima_interacao_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    ultima_compra_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
