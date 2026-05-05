"""Create CRM schema and all tables

Revision ID: 001
Revises:
Create Date: 2026-05-04
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS crm")

    op.create_table(
        "operador",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm",
    )

    op.create_table(
        "cliente",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("telefone", sa.String(20), nullable=False, unique=True),
        sa.Column("nome", sa.String(255), nullable=True),
        sa.Column("classificacao", sa.String(30), nullable=False, server_default="lead"),
        sa.Column("opt_in", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("opt_in_registrado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("primeira_interacao_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ultima_interacao_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ultima_compra_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm",
    )
    op.create_index("ix_crm_cliente_telefone", "cliente", ["telefone"], schema="crm")
    op.create_index("ix_crm_cliente_classificacao", "cliente", ["classificacao"], schema="crm")

    op.create_table(
        "conversa",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("cliente_id", UUID(as_uuid=True), sa.ForeignKey("crm.cliente.id"), nullable=False),
        sa.Column("canal", sa.String(20), nullable=False, server_default="whatsapp"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ativa"),
        sa.Column("operador_id", UUID(as_uuid=True), sa.ForeignKey("crm.operador.id"), nullable=True),
        sa.Column("handoff_iniciado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("iniciada_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("encerrada_em", sa.DateTime(timezone=True), nullable=True),
        schema="crm",
    )
    op.create_index("ix_crm_conversa_cliente_id", "conversa", ["cliente_id"], schema="crm")
    op.create_index("ix_crm_conversa_status", "conversa", ["status"], schema="crm")

    op.create_table(
        "mensagem",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conversa_id", UUID(as_uuid=True), sa.ForeignKey("crm.conversa.id"), nullable=False),
        sa.Column("conteudo", sa.Text, nullable=False),
        sa.Column("direcao", sa.String(10), nullable=False),
        sa.Column("sentimento", sa.String(20), nullable=True),
        sa.Column("tema", sa.String(20), nullable=True),
        sa.Column("classificado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enviada_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="crm",
    )
    op.create_index("ix_crm_mensagem_conversa_id", "mensagem", ["conversa_id"], schema="crm")

    op.create_table(
        "segmento",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(100), nullable=False, unique=True),
        sa.Column("descricao", sa.Text, nullable=True),
        sa.Column("criterios", JSONB, nullable=False, server_default="{}"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
        schema="crm",
    )

    op.create_table(
        "cliente_segmento",
        sa.Column("cliente_id", UUID(as_uuid=True), sa.ForeignKey("crm.cliente.id"), nullable=False),
        sa.Column("segmento_id", UUID(as_uuid=True), sa.ForeignKey("crm.segmento.id"), nullable=False),
        sa.Column("atribuido_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("cliente_id", "segmento_id"),
        schema="crm",
    )

    op.create_table(
        "evento",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("cliente_id", UUID(as_uuid=True), sa.ForeignKey("crm.cliente.id"), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("processado", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm",
    )
    op.create_index("ix_crm_evento_tipo", "evento", ["tipo"], schema="crm")
    op.create_index("ix_crm_evento_cliente_id", "evento", ["cliente_id"], schema="crm")

    op.create_table(
        "campanha",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("segmento_id", UUID(as_uuid=True), sa.ForeignKey("crm.segmento.id"), nullable=True),
        sa.Column("copy", sa.Text, nullable=False),
        sa.Column("publico_alvo", JSONB, nullable=False, server_default="{}"),
        sa.Column("orcamento_sugerido", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="rascunho"),
        sa.Column("gerada_por", sa.String(50), nullable=False, server_default="ads_agent"),
        sa.Column("aprovada_por", UUID(as_uuid=True), sa.ForeignKey("crm.operador.id"), nullable=True),
        sa.Column("aprovada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="crm",
    )

    op.create_table(
        "acao_agente",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("agente", sa.String(20), nullable=False),
        sa.Column("cliente_id", UUID(as_uuid=True), sa.ForeignKey("crm.cliente.id"), nullable=False),
        sa.Column("evento_id", UUID(as_uuid=True), sa.ForeignKey("crm.evento.id"), nullable=True),
        sa.Column("conteudo_sugerido", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="sugerida"),
        sa.Column("aprovada_por", UUID(as_uuid=True), sa.ForeignKey("crm.operador.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("executada_em", sa.DateTime(timezone=True), nullable=True),
        schema="crm",
    )


def downgrade() -> None:
    for table in ["acao_agente", "campanha", "evento", "cliente_segmento", "segmento", "mensagem", "conversa", "cliente", "operador"]:
        op.drop_table(table, schema="crm")
    op.execute("DROP SCHEMA IF EXISTS crm")
