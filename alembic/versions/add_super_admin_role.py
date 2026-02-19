"""add SUPER_ADMIN to userrole enum

Revision ID: add_super_admin
Revises: 1fd39bb8ccf7
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op


revision: str = "add_super_admin"
down_revision: Union[str, None] = "1fd39bb8ccf7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add SUPER_ADMIN to the existing PostgreSQL enum type 'userrole'
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; leave as no-op
    pass
