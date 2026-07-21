"""add_indexes_on_foreign_keys

Revision ID: e030bf513d7f
Revises: 7a3e10b4c9d5
Create Date: 2026-07-21 03:32:33.399726

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'e030bf513d7f'
down_revision: Union[str, None] = '7a3e10b4c9d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEXES = [
    ("ix_appointments_clinic_id", "appointments", ["clinic_id"]),
    ("ix_appointments_owner_id", "appointments", ["owner_id"]),
    ("ix_appointments_pet_id", "appointments", ["pet_id"]),
    ("ix_appointments_scheduled_at", "appointments", ["scheduled_at"]),
    ("ix_appointments_vet_id", "appointments", ["vet_id"]),
    ("ix_audit_logs_action", "audit_logs", ["action"]),
    ("ix_audit_logs_clinic_id", "audit_logs", ["clinic_id"]),
    ("ix_audit_logs_created_at", "audit_logs", ["created_at"]),
    ("ix_audit_logs_resource", "audit_logs", ["resource"]),
    ("ix_audit_logs_user_id", "audit_logs", ["user_id"]),
    ("ix_invoices_appointment_id", "invoices", ["appointment_id"]),
    ("ix_invoices_clinic_id", "invoices", ["clinic_id"]),
    ("ix_invoices_owner_id", "invoices", ["owner_id"]),
    ("ix_owners_clinic_id", "owners", ["clinic_id"]),
    ("ix_pets_clinic_id", "pets", ["clinic_id"]),
    ("ix_pets_owner_id", "pets", ["owner_id"]),
    ("ix_treatments_appointment_id", "treatments", ["appointment_id"]),
    ("ix_treatments_clinic_id", "treatments", ["clinic_id"]),
    ("ix_users_clinic_id", "users", ["clinic_id"]),
]


def upgrade() -> None:
    for name, table, columns in INDEXES:
        op.create_index(op.f(name), table, columns, unique=False)


def downgrade() -> None:
    for name, table, columns in reversed(INDEXES):
        op.drop_index(op.f(name), table_name=table)
