"""add configurable services, waiting room and structured clinical encounters"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20260909_clinical_waiting_room"
down_revision: Union[str, None] = "20260723_clinical_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SERVICE_TYPES = (
    ("Consulta", "consulta", 0),
    ("Banho e tosquia", "banho-tosquia", 1),
    ("Vacinação", "vacinacao", 2),
    ("Tratamento", "tratamento", 3),
    ("Acompanhamento", "acompanhamento", 4),
    ("Cirurgia", "cirurgia", 5),
)


def upgrade() -> None:
    op.create_table(
        "service_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("clinic_id", "slug", name="uq_service_types_clinic_slug"),
    )
    op.create_index("ix_service_types_id", "service_types", ["id"], unique=False)
    op.create_index("ix_service_types_clinic_id", "service_types", ["clinic_id"], unique=False)
    op.create_index("ix_service_types_clinic_active_order", "service_types", ["clinic_id", "active", "sort_order"], unique=False)

    with op.batch_alter_table("appointments") as batch_op:
        batch_op.add_column(sa.Column("service_type_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_appointments_service_type_id", "service_types", ["service_type_id"], ["id"])
    op.create_index("ix_appointments_service_type_id", "appointments", ["service_type_id"], unique=False)

    op.create_table(
        "waiting_room_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="waiting"),
        sa.Column("arrival_at", sa.DateTime(), nullable=False),
        sa.Column("called_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("room", sa.String(length=100), nullable=True),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.Column("status_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("clinic_id", "appointment_id", name="uq_waiting_room_clinic_appointment"),
    )
    op.create_index("ix_waiting_room_entries_id", "waiting_room_entries", ["id"], unique=False)
    op.create_index("ix_waiting_room_entries_clinic_id", "waiting_room_entries", ["clinic_id"], unique=False)
    op.create_index("ix_waiting_room_entries_appointment_id", "waiting_room_entries", ["appointment_id"], unique=False)
    op.create_index("ix_waiting_room_entries_status", "waiting_room_entries", ["status"], unique=False)
    op.create_index("ix_waiting_room_entries_arrival_at", "waiting_room_entries", ["arrival_at"], unique=False)
    op.create_index("ix_waiting_room_clinic_arrival", "waiting_room_entries", ["clinic_id", "arrival_at"], unique=False)

    op.create_table(
        "clinical_exam_systems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("clinic_id", "name", name="uq_exam_systems_clinic_name"),
    )
    op.create_index("ix_clinical_exam_systems_id", "clinical_exam_systems", ["id"], unique=False)
    op.create_index("ix_clinical_exam_systems_clinic_id", "clinical_exam_systems", ["clinic_id"], unique=False)
    op.create_index("ix_exam_systems_clinic_order", "clinical_exam_systems", ["clinic_id", "active", "sort_order"], unique=False)

    op.create_table(
        "clinical_exam_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("system_id", sa.Integer(), sa.ForeignKey("clinical_exam_systems.id"), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("system_id", "name", name="uq_exam_findings_system_name"),
    )
    op.create_index("ix_clinical_exam_findings_id", "clinical_exam_findings", ["id"], unique=False)
    op.create_index("ix_clinical_exam_findings_clinic_id", "clinical_exam_findings", ["clinic_id"], unique=False)
    op.create_index("ix_clinical_exam_findings_system_id", "clinical_exam_findings", ["system_id"], unique=False)
    op.create_index("ix_exam_findings_clinic_active", "clinical_exam_findings", ["clinic_id", "active"], unique=False)

    op.create_table(
        "clinical_exam_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id"), nullable=False),
        sa.Column("finding_id", sa.Integer(), sa.ForeignKey("clinical_exam_findings.id"), nullable=False),
        sa.Column("finding_name", sa.String(length=180), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="not-evaluated"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("appointment_id", "finding_id", name="uq_exam_observations_appointment_finding"),
    )
    op.create_index("ix_clinical_exam_observations_id", "clinical_exam_observations", ["id"], unique=False)
    op.create_index("ix_clinical_exam_observations_clinic_id", "clinical_exam_observations", ["clinic_id"], unique=False)
    op.create_index("ix_clinical_exam_observations_appointment_id", "clinical_exam_observations", ["appointment_id"], unique=False)
    op.create_index("ix_clinical_exam_observations_finding_id", "clinical_exam_observations", ["finding_id"], unique=False)
    op.create_index("ix_exam_observations_clinic_appointment", "clinical_exam_observations", ["clinic_id", "appointment_id"], unique=False)

    with op.batch_alter_table("treatments") as batch_op:
        batch_op.add_column(sa.Column("anamnesis", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("consultation_type", sa.String(length=50), nullable=False, server_default="normal"))
        batch_op.add_column(sa.Column("referring_vet_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key("fk_treatments_referring_vet_id", "users", ["referring_vet_id"], ["id"])
    op.create_index("ix_treatments_referring_vet_id", "treatments", ["referring_vet_id"], unique=False)

    for name, slug, sort_order in SERVICE_TYPES:
        op.execute(sa.text(
            "INSERT INTO service_types (clinic_id, name, slug, sort_order, active) "
            "SELECT id, :name, :slug, :sort_order, TRUE FROM clinics"
        ).bindparams(name=name, slug=slug, sort_order=sort_order))
    op.execute(sa.text(
        "UPDATE appointments SET service_type_id = ("
        "SELECT id FROM service_types WHERE service_types.clinic_id = appointments.clinic_id AND slug = 'consulta'"
        ") WHERE service_type_id IS NULL"
    ))


def downgrade() -> None:
    op.drop_index("ix_treatments_referring_vet_id", table_name="treatments")
    with op.batch_alter_table("treatments") as batch_op:
        batch_op.drop_constraint("fk_treatments_referring_vet_id", type_="foreignkey")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("referring_vet_id")
        batch_op.drop_column("consultation_type")
        batch_op.drop_column("anamnesis")

    op.drop_index("ix_exam_observations_clinic_appointment", table_name="clinical_exam_observations")
    op.drop_index("ix_clinical_exam_observations_finding_id", table_name="clinical_exam_observations")
    op.drop_index("ix_clinical_exam_observations_appointment_id", table_name="clinical_exam_observations")
    op.drop_index("ix_clinical_exam_observations_clinic_id", table_name="clinical_exam_observations")
    op.drop_index("ix_clinical_exam_observations_id", table_name="clinical_exam_observations")
    op.drop_table("clinical_exam_observations")

    op.drop_index("ix_exam_findings_clinic_active", table_name="clinical_exam_findings")
    op.drop_index("ix_clinical_exam_findings_system_id", table_name="clinical_exam_findings")
    op.drop_index("ix_clinical_exam_findings_clinic_id", table_name="clinical_exam_findings")
    op.drop_index("ix_clinical_exam_findings_id", table_name="clinical_exam_findings")
    op.drop_table("clinical_exam_findings")

    op.drop_index("ix_exam_systems_clinic_order", table_name="clinical_exam_systems")
    op.drop_index("ix_clinical_exam_systems_clinic_id", table_name="clinical_exam_systems")
    op.drop_index("ix_clinical_exam_systems_id", table_name="clinical_exam_systems")
    op.drop_table("clinical_exam_systems")

    op.drop_index("ix_waiting_room_clinic_arrival", table_name="waiting_room_entries")
    op.drop_index("ix_waiting_room_entries_arrival_at", table_name="waiting_room_entries")
    op.drop_index("ix_waiting_room_entries_status", table_name="waiting_room_entries")
    op.drop_index("ix_waiting_room_entries_appointment_id", table_name="waiting_room_entries")
    op.drop_index("ix_waiting_room_entries_clinic_id", table_name="waiting_room_entries")
    op.drop_index("ix_waiting_room_entries_id", table_name="waiting_room_entries")
    op.drop_table("waiting_room_entries")

    op.drop_index("ix_appointments_service_type_id", table_name="appointments")
    with op.batch_alter_table("appointments") as batch_op:
        batch_op.drop_constraint("fk_appointments_service_type_id", type_="foreignkey")
        batch_op.drop_column("service_type_id")

    op.drop_index("ix_service_types_clinic_active_order", table_name="service_types")
    op.drop_index("ix_service_types_clinic_id", table_name="service_types")
    op.drop_index("ix_service_types_id", table_name="service_types")
    op.drop_table("service_types")
