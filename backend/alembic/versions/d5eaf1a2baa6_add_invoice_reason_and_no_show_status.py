"""add_invoice_reason_and_no_show_status

Revision ID: d5eaf1a2baa6
Revises: e030bf513d7f
Create Date: 2026-07-21 03:45:48.208086

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Engine

revision: str = 'd5eaf1a2baa6'
down_revision: Union[str, None] = 'e030bf513d7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgresql() -> bool:
    bind = op.get_bind()
    if isinstance(bind, Engine):
        return bind.dialect.name == "postgresql"
    return False


def upgrade() -> None:
    # Add reason column to invoices (works on SQLite and Postgres)
    op.add_column('invoices', sa.Column('reason', sa.String(length=255), nullable=True))

    # Add 'no-show' to appointmentstatus enum (PostgreSQL only)
    if _is_postgresql():
        op.execute("ALTER TYPE appointmentstatus ADD VALUE IF NOT EXISTS 'no-show'")


def downgrade() -> None:
    op.drop_column('invoices', 'reason')
    # PostgreSQL doesn't support DROP VALUE from enum; skip in downgrade.