"""functional clinical flow fields and statuses

Revision ID: 20260723_clinical_flow
Revises: 7420d6184b6a
Create Date: 2026-07-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260723_clinical_flow"
down_revision: Union[str, None] = "7420d6184b6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if _is_postgresql():
        op.execute("ALTER TYPE appointmentstatus ADD VALUE IF NOT EXISTS 'IN_PROGRESS'")
        op.execute("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'SENT'")
        op.execute(
            "DO $$ BEGIN CREATE TYPE invoicesyncstatus AS ENUM ('PENDING', 'SYNCED', 'FAILED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        )

    op.add_column("appointments", sa.Column("status_reason", sa.String(length=255), nullable=True))
    op.add_column("invoices", sa.Column("currency", sa.String(length=3), nullable=False, server_default="AOA"))
    op.add_column("invoices", sa.Column("external_reference", sa.String(length=255), nullable=True))
    sync_type = (
        postgresql.ENUM("PENDING", "SYNCED", "FAILED", name="invoicesyncstatus", create_type=False)
        if _is_postgresql()
        else sa.Enum("PENDING", "SYNCED", "FAILED", name="invoicesyncstatus")
    )
    op.add_column(
        "invoices",
        sa.Column(
            "sync_status",
            sync_type,
            nullable=False,
            server_default="PENDING",
        ),
    )
    op.create_index("uq_invoices_external_reference", "invoices", ["external_reference"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_invoices_external_reference", table_name="invoices")
    op.drop_column("invoices", "sync_status")
    op.drop_column("invoices", "external_reference")
    op.drop_column("invoices", "currency")
    op.drop_column("appointments", "status_reason")
