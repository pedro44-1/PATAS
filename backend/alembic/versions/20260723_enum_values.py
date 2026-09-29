"""align PostgreSQL enum values with Python enum names

Revision ID: 20260723_enum_values
Revises: 20260723_clinical_flow
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260723_enum_values"
down_revision: Union[str, None] = "20260723_clinical_flow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE appointmentstatus ADD VALUE IF NOT EXISTS 'IN_PROGRESS'")
        op.execute("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'SENT'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely.
    pass
