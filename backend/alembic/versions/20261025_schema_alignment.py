"""align persisted schema with the ORM models

Revision ID: 20261025_schema_alignment
Revises: 20260929_widen_invoice_series
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261025_schema_alignment"
down_revision: Union[str, None] = "20260929_widen_invoice_series"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fail_on_treatment_conflicts() -> None:
    if op.get_context().as_sql:
        return
    bind = op.get_bind()
    orphans = bind.execute(
        sa.text("SELECT COUNT(*) FROM treatments WHERE appointment_id IS NULL")
    ).scalar_one()
    duplicates = bind.execute(sa.text(
        "SELECT appointment_id FROM treatments WHERE appointment_id IS NOT NULL "
        "GROUP BY appointment_id HAVING COUNT(*) > 1"
    )).scalars().all()
    if orphans or duplicates:
        raise RuntimeError(
            "Resolve treatments before upgrading: "
            f"{orphans} without appointment, duplicated appointments {list(duplicates)}"
        )


def upgrade() -> None:
    _fail_on_treatment_conflicts()
    op.drop_index("ix_treatments_appointment_id", table_name="treatments")
    with op.batch_alter_table("treatments") as batch_op:
        batch_op.alter_column(
            "appointment_id", existing_type=sa.Integer(), nullable=False,
        )
        batch_op.alter_column(
            "diagnosis", existing_type=sa.String(length=500),
            type_=sa.Text(), existing_nullable=True,
        )
    op.create_index(
        "ix_treatments_appointment_id", "treatments", ["appointment_id"], unique=True,
    )

    for table in ("owners", "clinics"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "address", existing_type=sa.String(length=255),
                type_=sa.String(length=500), existing_nullable=True,
            )

    with op.batch_alter_table("pets") as batch_op:
        batch_op.drop_column("age")


def downgrade() -> None:
    bind = op.get_bind()
    for table in ("owners", "clinics"):
        count = bind.execute(
            sa.text(f"SELECT COUNT(*) FROM {table} WHERE length(address) > 255")
        ).scalar_one()
        if count:
            raise RuntimeError(f"Cannot narrow {table}.address while values exceed 255 characters")
    count = bind.execute(
        sa.text("SELECT COUNT(*) FROM treatments WHERE length(diagnosis) > 500")
    ).scalar_one()
    if count:
        raise RuntimeError("Cannot narrow treatments.diagnosis while values exceed 500 characters")

    with op.batch_alter_table("pets") as batch_op:
        batch_op.add_column(sa.Column("age", sa.String(length=50), nullable=True))

    for table in ("owners", "clinics"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "address", existing_type=sa.String(length=500),
                type_=sa.String(length=255), existing_nullable=True,
            )

    op.drop_index("ix_treatments_appointment_id", table_name="treatments")
    with op.batch_alter_table("treatments") as batch_op:
        batch_op.alter_column(
            "diagnosis", existing_type=sa.Text(),
            type_=sa.String(length=500), existing_nullable=True,
        )
        batch_op.alter_column(
            "appointment_id", existing_type=sa.Integer(), nullable=True,
        )
    op.create_index(
        "ix_treatments_appointment_id", "treatments", ["appointment_id"], unique=False,
    )
