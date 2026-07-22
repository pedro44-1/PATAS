"""add_weight_to_appointments

Revision ID: 7420d6184b6a
Revises: 20260721_add_pet_birth_date
Create Date: 2026-07-21 12:25:51.493609

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '7420d6184b6a'
down_revision: Union[str, None] = '20260721_add_pet_birth_date'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('appointments', sa.Column('weight', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('appointments', 'weight')
