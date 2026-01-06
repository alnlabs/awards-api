"""add award_type_id to cycles

Revision ID: c8d9e0f1a2b3
Revises: b7f8c9d1e2f3
Create Date: 2026-01-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, None] = 'b7f8c9d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add award_type_id column to cycles table
    op.add_column('cycles', sa.Column('award_type_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_cycles_award_type_id',
        'cycles',
        'award_types',
        ['award_type_id'],
        ['id']
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_cycles_award_type_id', 'cycles', type_='foreignkey')
    
    # Remove award_type_id column
    op.drop_column('cycles', 'award_type_id')

