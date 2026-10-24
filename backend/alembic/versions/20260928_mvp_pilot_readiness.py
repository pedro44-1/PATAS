"""add pilot identity, archive, and scheduling safeguards

Revision ID: 20260928_mvp_pilot
Revises: 20260909_clinical_waiting_room
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260928_mvp_pilot"
down_revision: Union[str, None] = "20260909_clinical_waiting_room"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("UPDATE appointments SET duration_min = 30 WHERE duration_min IS NULL")
    with op.batch_alter_table("appointments") as batch_op:
        batch_op.alter_column("duration_min", existing_type=sa.Integer(), nullable=False)

    for table_name in ("owners", "pets"):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column("archived_at", sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column("archived_by_user_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                f"fk_{table_name}_archived_by_user_id",
                "users",
                ["archived_by_user_id"],
                ["id"],
                ondelete="SET NULL",
            )
        op.create_index(f"ix_{table_name}_archived_at", table_name, ["archived_at"], unique=False)

    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) USING lower(role::text)")
        op.execute(
            "ALTER TABLE appointments ALTER COLUMN status TYPE VARCHAR(30) "
            "USING lower(replace(status::text, '_', '-'))"
        )
        op.execute("ALTER TABLE invoices ALTER COLUMN status TYPE VARCHAR(20) USING lower(status::text)")
        op.execute("DROP TYPE IF EXISTS userrole")
        op.execute("DROP TYPE IF EXISTS appointmentstatus")
        op.execute("DROP TYPE IF EXISTS invoicestatus")
        op.create_check_constraint(
            "ck_users_role",
            "users",
            "role IN ('admin', 'vet', 'receptionist')",
        )
        op.create_check_constraint(
            "ck_appointments_status",
            "appointments",
            "status IN ('scheduled', 'in-progress', 'completed', 'cancelled', 'no-show')",
        )
        op.create_check_constraint(
            "ck_invoices_status",
            "invoices",
            "status IN ('draft', 'sent', 'paid', 'cancelled')",
        )
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        op.execute(
            "ALTER TABLE appointments ADD CONSTRAINT ex_appointments_active_vet_overlap "
            "EXCLUDE USING gist ("
            "clinic_id WITH =, vet_id WITH =, "
            "tsrange(scheduled_at, scheduled_at + (duration_min * interval '1 minute'), '[)') WITH &&"
            ") WHERE (status IN ('scheduled', 'in-progress'))"
        )
    else:
        op.execute("UPDATE users SET role = lower(role)")
        op.execute("UPDATE appointments SET status = lower(replace(status, '_', '-'))")
        op.execute("UPDATE invoices SET status = lower(status)")


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS ex_appointments_active_vet_overlap")
        op.drop_constraint("ck_invoices_status", "invoices", type_="check")
        op.drop_constraint("ck_appointments_status", "appointments", type_="check")
        op.drop_constraint("ck_users_role", "users", type_="check")
        op.execute("CREATE TYPE userrole AS ENUM ('admin', 'vet', 'receptionist')")
        op.execute(
            "CREATE TYPE appointmentstatus AS ENUM "
            "('scheduled', 'completed', 'cancelled', 'no-show', 'IN_PROGRESS')"
        )
        op.execute("CREATE TYPE invoicestatus AS ENUM ('draft', 'paid', 'cancelled', 'SENT')")
        op.execute(
            "ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole"
        )
        op.execute(
            "ALTER TABLE appointments ALTER COLUMN status TYPE appointmentstatus "
            "USING (CASE WHEN status = 'in-progress' THEN 'IN_PROGRESS' ELSE status END)::appointmentstatus"
        )
        op.execute(
            "ALTER TABLE invoices ALTER COLUMN status TYPE invoicestatus "
            "USING (CASE WHEN status = 'sent' THEN 'SENT' ELSE status END)::invoicestatus"
        )

    with op.batch_alter_table("appointments") as batch_op:
        batch_op.alter_column("duration_min", existing_type=sa.Integer(), nullable=True)

    for table_name in ("pets", "owners"):
        op.drop_index(f"ix_{table_name}_archived_at", table_name=table_name)
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(f"fk_{table_name}_archived_by_user_id", type_="foreignkey")
            batch_op.drop_column("archived_by_user_id")
            batch_op.drop_column("archived_at")

    op.drop_column("users", "must_change_password")
