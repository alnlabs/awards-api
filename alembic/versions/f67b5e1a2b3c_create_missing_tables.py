"""create missing tables

Revision ID: f67b5e1a2b3c
Revises: a08c43a46191
Create Date: 2026-03-10 13:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f67b5e1a2b3c'
down_revision = 'a08c43a46191'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 0. Create system_config table (without setup_complete, it will be added in next migration)
    op.create_table(
        'system_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('company_logo', sa.String(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 1. Create bulk_jobs table
    op.create_table(
        'bulk_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('total', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('processed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('error_file', sa.String(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('bulk_jobs')
    op.drop_table('system_config')
