"""add comment and updated_at to awards

Revision ID: b7f8c9d1e2f3
Revises: 5ec505e0cfce
Create Date: 2026-01-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7f8c9d1e2f3'
down_revision: Union[str, None] = '5ec505e0cfce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add comment column to awards table
    op.add_column('awards', sa.Column('comment', sa.String(length=1000), nullable=True))
    
    # Add updated_at column to awards table
    op.add_column('awards', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Set updated_at to created_at for existing records
    op.execute("""
        UPDATE awards 
        SET updated_at = created_at 
        WHERE updated_at IS NULL
    """)


def downgrade() -> None:
    # Remove updated_at column
    op.drop_column('awards', 'updated_at')
    
    # Remove comment column
    op.drop_column('awards', 'comment')

