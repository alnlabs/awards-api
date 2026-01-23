"""rename_cycle_status_open_to_active

Revision ID: f026b2e93b53
Revises: c8d9e0f1a2b3
Create Date: 2026-01-23 07:18:12.566717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f026b2e93b53'
down_revision: Union[str, None] = 'c8d9e0f1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep both OPEN and ACTIVE enum values for backward compatibility
    # Check if ACTIVE already exists, if not add it
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'ACTIVE' AND enumtypid = 'cyclestatus'::regtype) THEN
                ALTER TYPE cyclestatus ADD VALUE 'ACTIVE';
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    # Cannot remove enum values in PostgreSQL, so this is a no-op
    pass
