"""Make cliente.telefone nullable (site leads may have only email)

Revision ID: 003
Revises: 002
Create Date: 2026-06-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "cliente", "telefone",
        existing_type=sa.String(20),
        nullable=True,
        schema="crm",
    )


def downgrade() -> None:
    op.alter_column(
        "cliente", "telefone",
        existing_type=sa.String(20),
        nullable=False,
        schema="crm",
    )
