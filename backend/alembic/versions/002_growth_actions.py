"""Add cliente.email and widen acao_agente.tipo for growth scenarios

Revision ID: 002
Revises: 001
Create Date: 2026-06-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cliente",
        sa.Column("email", sa.String(255), nullable=True),
        schema="crm",
    )
    op.create_index("ix_crm_cliente_email", "cliente", ["email"], schema="crm")
    op.alter_column(
        "acao_agente",
        "tipo",
        type_=sa.String(40),
        existing_type=sa.String(20),
        existing_nullable=False,
        schema="crm",
    )


def downgrade() -> None:
    op.alter_column(
        "acao_agente",
        "tipo",
        type_=sa.String(20),
        existing_type=sa.String(40),
        existing_nullable=False,
        schema="crm",
    )
    op.drop_index("ix_crm_cliente_email", table_name="cliente", schema="crm")
    op.drop_column("cliente", "email", schema="crm")
