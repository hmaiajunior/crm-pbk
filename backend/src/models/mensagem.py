import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class DirecaoMensagem(str, Enum):
    entrada = "entrada"
    saida = "saida"


class SentimentoMensagem(str, Enum):
    positivo = "positivo"
    neutro = "neutro"
    negativo = "negativo"


class TemaMensagem(str, Enum):
    preco = "preco"
    produto = "produto"
    atendimento = "atendimento"
    qualidade = "qualidade"
    outro = "outro"


class Mensagem(Base):
    __tablename__ = "mensagem"
    __table_args__ = {"schema": "crm"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversa_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crm.conversa.id"), nullable=False)
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    direcao: Mapped[DirecaoMensagem] = mapped_column(String(10), nullable=False)
    sentimento: Mapped[SentimentoMensagem | None] = mapped_column(String(20), nullable=True)
    tema: Mapped[TemaMensagem | None] = mapped_column(String(20), nullable=True)
    classificado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enviada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
