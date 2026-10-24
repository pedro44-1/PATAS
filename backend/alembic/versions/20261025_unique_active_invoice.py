"""allow a single active invoice per appointment

Revision ID: 20261025_unique_active_invoice
Revises: 20261025_schema_alignment
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261025_unique_active_invoice"
down_revision: Union[str, None] = "20261025_schema_alignment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACTIVE_APPOINTMENT_INVOICE = "appointment_id IS NOT NULL AND status <> 'cancelled'"


def upgrade() -> None:
    if not op.get_context().as_sql:
        duplicates = op.get_bind().execute(sa.text(
            f"SELECT appointment_id FROM invoices WHERE {ACTIVE_APPOINTMENT_INVOICE} "
            "GROUP BY appointment_id HAVING COUNT(*) > 1"
        )).scalars().all()
        if duplicates:
            raise RuntimeError(
                "Cancel duplicated active invoices before upgrading; appointments "
                f"{list(duplicates)} have more than one"
            )
    op.create_index(
        "uq_invoices_active_appointment",
        "invoices",
        ["appointment_id"],
        unique=True,
        postgresql_where=sa.text(ACTIVE_APPOINTMENT_INVOICE),
        sqlite_where=sa.text(ACTIVE_APPOINTMENT_INVOICE),
    )


def downgrade() -> None:
    op.drop_index("uq_invoices_active_appointment", table_name="invoices")
