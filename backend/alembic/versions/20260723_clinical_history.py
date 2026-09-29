"""add structured vaccination and medication history

Revision ID: 20260723_clinical_history
Revises: 20260723_enum_values
"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260723_clinical_history"
down_revision: Union[str, None] = "20260723_enum_values"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = None if context.is_offline_mode() else sa.inspect(bind)
    # The application bootstrap historically used create_all. If it already
    # created these tables, the migration only needs to advance the revision.
    if inspector and inspector.has_table("vaccinations") and inspector.has_table("medications"):
        return
    if bind.dialect.name == "postgresql":
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE vaccinationstatus AS ENUM ('ADMINISTERED', 'VOIDED');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE medicationstatus AS ENUM ('ACTIVE', 'COMPLETED', 'CANCELLED', 'VOIDED');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """)

    vaccination_status = (
        postgresql.ENUM("ADMINISTERED", "VOIDED", name="vaccinationstatus", create_type=False)
        if bind.dialect.name == "postgresql"
        else sa.Enum("ADMINISTERED", "VOIDED", name="vaccinationstatus")
    )
    medication_status = (
        postgresql.ENUM("ACTIVE", "COMPLETED", "CANCELLED", "VOIDED", name="medicationstatus", create_type=False)
        if bind.dialect.name == "postgresql"
        else sa.Enum("ACTIVE", "COMPLETED", "CANCELLED", "VOIDED", name="medicationstatus")
    )

    op.create_table(
        "vaccinations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("pet_id", sa.Integer(), sa.ForeignKey("pets.id"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id"), nullable=True),
        sa.Column("vet_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("administered_at", sa.DateTime(), nullable=False),
        sa.Column("dose", sa.String(length=100), nullable=False),
        sa.Column("lot_number", sa.String(length=100), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("next_due_at", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            vaccination_status,
            nullable=False,
            server_default="ADMINISTERED",
        ),
        sa.Column("void_reason", sa.String(length=1000), nullable=True),
        sa.Column("voided_at", sa.DateTime(), nullable=True),
        sa.Column("voided_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_vaccinations_id", "vaccinations", ["id"], unique=False)
    op.create_index("ix_vaccinations_clinic_id", "vaccinations", ["clinic_id"], unique=False)
    op.create_index("ix_vaccinations_pet_id", "vaccinations", ["pet_id"], unique=False)
    op.create_index("ix_vaccinations_appointment_id", "vaccinations", ["appointment_id"], unique=False)
    op.create_index("ix_vaccinations_vet_id", "vaccinations", ["vet_id"], unique=False)
    op.create_index("ix_vaccinations_administered_at", "vaccinations", ["administered_at"], unique=False)
    op.create_index(
        "ix_vaccinations_clinic_pet_date",
        "vaccinations",
        ["clinic_id", "pet_id", "administered_at"],
        unique=False,
    )

    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("pet_id", sa.Integer(), sa.ForeignKey("pets.id"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id"), nullable=True),
        sa.Column("vet_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("dosage", sa.String(length=255), nullable=False),
        sa.Column("frequency", sa.String(length=255), nullable=False),
        sa.Column("route", sa.String(length=100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            medication_status,
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("void_reason", sa.String(length=1000), nullable=True),
        sa.Column("voided_at", sa.DateTime(), nullable=True),
        sa.Column("voided_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_medications_id", "medications", ["id"], unique=False)
    op.create_index("ix_medications_clinic_id", "medications", ["clinic_id"], unique=False)
    op.create_index("ix_medications_pet_id", "medications", ["pet_id"], unique=False)
    op.create_index("ix_medications_appointment_id", "medications", ["appointment_id"], unique=False)
    op.create_index("ix_medications_vet_id", "medications", ["vet_id"], unique=False)
    op.create_index("ix_medications_start_date", "medications", ["start_date"], unique=False)
    op.create_index(
        "ix_medications_clinic_pet_date",
        "medications",
        ["clinic_id", "pet_id", "start_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_medications_clinic_pet_date", table_name="medications")
    op.drop_index("ix_medications_start_date", table_name="medications")
    op.drop_index("ix_medications_vet_id", table_name="medications")
    op.drop_index("ix_medications_appointment_id", table_name="medications")
    op.drop_index("ix_medications_pet_id", table_name="medications")
    op.drop_index("ix_medications_clinic_id", table_name="medications")
    op.drop_index("ix_medications_id", table_name="medications")
    op.drop_table("medications")

    op.drop_index("ix_vaccinations_clinic_pet_date", table_name="vaccinations")
    op.drop_index("ix_vaccinations_administered_at", table_name="vaccinations")
    op.drop_index("ix_vaccinations_vet_id", table_name="vaccinations")
    op.drop_index("ix_vaccinations_appointment_id", table_name="vaccinations")
    op.drop_index("ix_vaccinations_pet_id", table_name="vaccinations")
    op.drop_index("ix_vaccinations_clinic_id", table_name="vaccinations")
    op.drop_index("ix_vaccinations_id", table_name="vaccinations")
    op.drop_table("vaccinations")

    # PostgreSQL keeps named enum types after dropping their tables.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS medicationstatus")
        op.execute("DROP TYPE IF EXISTS vaccinationstatus")
