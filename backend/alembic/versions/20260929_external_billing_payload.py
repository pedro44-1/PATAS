"""add external billing payload and invoice lines

Revision ID: 20260929_external_billing
Revises: 20260928_mvp_pilot
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260929_external_billing"
down_revision: Union[str, None] = "20260928_mvp_pilot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clinics", sa.Column("nif", sa.String(length=30), nullable=True))
    op.add_column("clinics", sa.Column("billing_store_external_id", sa.String(length=100), nullable=True))
    op.add_column("owners", sa.Column("nif", sa.String(length=30), nullable=True))
    invoice_columns = (
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("document_type", sa.String(length=2), nullable=False, server_default="FT"),
        sa.Column("series", sa.String(length=20), nullable=True),
        sa.Column("document_number", sa.String(length=50), nullable=True),
        sa.Column("document_url", sa.String(length=1000), nullable=True),
        sa.Column("billing_external_id", sa.String(length=150), nullable=True),
        sa.Column("idempotency_key", sa.String(length=36), nullable=True),
        sa.Column("quote_id", sa.String(length=36), nullable=True),
        sa.Column("quote_expires_at", sa.DateTime(), nullable=True),
        sa.Column("quote_vat_configuration_version", sa.String(length=100), nullable=True),
        sa.Column("quote_calculation_digest", sa.String(length=255), nullable=True),
        sa.Column("quote_payable", sa.Numeric(14, 2), nullable=True),
        sa.Column("quote_snapshot", sa.Text(), nullable=True),
        sa.Column("provider_status", sa.String(length=50), nullable=True),
        sa.Column("provider_mode", sa.String(length=30), nullable=True),
        sa.Column("sync_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_sync_error", sa.String(length=500), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("payment_method", sa.String(length=30), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("issuer_name", sa.String(length=255), nullable=True),
        sa.Column("issuer_nif", sa.String(length=30), nullable=True),
        sa.Column("issuer_address", sa.String(length=500), nullable=True),
        sa.Column("issuer_phone", sa.String(length=50), nullable=True),
        sa.Column("issuer_store_external_id", sa.String(length=100), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_nif", sa.String(length=30), nullable=True),
        sa.Column("customer_address", sa.String(length=500), nullable=True),
        sa.Column("customer_phone", sa.String(length=50), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
    )
    with op.batch_alter_table("invoices") as batch_op:
        for column in invoice_columns:
            batch_op.add_column(column)
        batch_op.create_unique_constraint(
            "uq_invoices_clinic_document_number", ["clinic_id", "document_number"]
        )
        batch_op.create_unique_constraint("uq_invoices_billing_external_id", ["billing_external_id"])
        batch_op.create_unique_constraint("uq_invoices_idempotency_key", ["idempotency_key"])
        batch_op.create_unique_constraint("uq_invoices_quote_id", ["quote_id"])
    op.create_table(
        "invoice_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("vat_profile_code", sa.String(length=80), nullable=True),
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="SERVICE"),
        sa.Column("unit", sa.String(length=12), nullable=False, server_default="UN"),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total", sa.Numeric(14, 2), nullable=False),
    )
    op.create_index("ix_invoice_lines_invoice_id", "invoice_lines", ["invoice_id"])
    op.create_index("ix_invoice_lines_clinic_id", "invoice_lines", ["clinic_id"])
    op.execute("UPDATE invoices SET subtotal = amount, tax_total = 0")
    op.execute(
        "INSERT INTO invoice_lines (invoice_id, clinic_id, description, quantity, unit_price, tax_rate, subtotal, tax_amount, total) "
        "SELECT id, clinic_id, COALESCE(description, 'Serviços veterinários'), 1, amount, 0, amount, 0, amount FROM invoices"
    )
    op.execute(
        "UPDATE invoices SET "
        "issuer_name = (SELECT name FROM clinics WHERE clinics.id = invoices.clinic_id), "
        "issuer_nif = (SELECT nif FROM clinics WHERE clinics.id = invoices.clinic_id), "
        "issuer_address = (SELECT address FROM clinics WHERE clinics.id = invoices.clinic_id), "
        "issuer_phone = (SELECT phone FROM clinics WHERE clinics.id = invoices.clinic_id), "
        "issuer_store_external_id = (SELECT billing_store_external_id FROM clinics WHERE clinics.id = invoices.clinic_id), "
        "customer_name = (SELECT name FROM owners WHERE owners.id = invoices.owner_id), "
        "customer_nif = (SELECT nif FROM owners WHERE owners.id = invoices.owner_id), "
        "customer_address = (SELECT address FROM owners WHERE owners.id = invoices.owner_id), "
        "customer_phone = (SELECT phone FROM owners WHERE owners.id = invoices.owner_id), "
        "customer_email = (SELECT email FROM owners WHERE owners.id = invoices.owner_id)"
    )


def downgrade() -> None:
    op.drop_index("ix_invoice_lines_clinic_id", table_name="invoice_lines")
    op.drop_index("ix_invoice_lines_invoice_id", table_name="invoice_lines")
    op.drop_table("invoice_lines")
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_constraint("uq_invoices_idempotency_key", type_="unique")
        batch_op.drop_constraint("uq_invoices_quote_id", type_="unique")
        batch_op.drop_constraint("uq_invoices_billing_external_id", type_="unique")
        batch_op.drop_constraint("uq_invoices_clinic_document_number", type_="unique")
        for column in (
            "customer_email", "customer_phone", "customer_address", "customer_nif", "customer_name",
            "issuer_store_external_id", "issuer_phone", "issuer_address", "issuer_nif", "issuer_name",
            "paid_at", "due_at", "issued_at", "payment_method", "document_url",
            "last_sync_at", "last_sync_error", "sync_attempts", "provider_mode", "provider_status",
            "quote_snapshot", "quote_payable", "quote_calculation_digest",
            "quote_vat_configuration_version", "quote_expires_at", "quote_id",
            "idempotency_key", "billing_external_id", "document_number", "series", "document_type",
            "tax_total", "subtotal",
        ):
            batch_op.drop_column(column)
    op.drop_column("owners", "nif")
    op.drop_column("clinics", "billing_store_external_id")
    op.drop_column("clinics", "nif")
