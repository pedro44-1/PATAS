"""store invoice amounts as exact decimals

Revision ID: 20261025_invoice_amount_numeric
Revises: 20261025_user_sessions
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261025_invoice_amount_numeric"
down_revision: Union[str, None] = "20261025_user_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.alter_column(
            "amount",
            existing_type=sa.Float(),
            type_=sa.Numeric(14, 2),
            existing_nullable=False,
            postgresql_using="round(amount::numeric, 2)",
        )


def downgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.alter_column(
            "amount",
            existing_type=sa.Numeric(14, 2),
            type_=sa.Float(),
            existing_nullable=False,
        )
