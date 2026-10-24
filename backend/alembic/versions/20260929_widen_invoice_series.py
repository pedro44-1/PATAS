"""allow external billing provider series identifiers

Revision ID: 20260929_widen_invoice_series
Revises: 20260929_external_billing
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260929_widen_invoice_series"
down_revision: Union[str, None] = "20260929_external_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.alter_column(
            "series", existing_type=sa.String(length=20),
            type_=sa.String(length=64), existing_nullable=True,
        )


def downgrade() -> None:
    count = op.get_bind().execute(
        sa.text("SELECT COUNT(*) FROM invoices WHERE length(series) > 20")
    ).scalar_one()
    if count:
        raise RuntimeError("Cannot narrow invoice series while external identifiers exceed 20 characters")
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.alter_column(
            "series", existing_type=sa.String(length=64),
            type_=sa.String(length=20), existing_nullable=True,
        )
