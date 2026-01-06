"""create award_types table

Revision ID: 5ec505e0cfce
Revises: a6316695cf39
Create Date: 2026-01-06 10:06:34.214643

"""
"""create award_types table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5ec505e0cfce"
down_revision = "a6316695cf39"  # keep this as your previous migration id
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "award_types",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("code", name="uq_award_types_code"),
    )


def downgrade() -> None:
    op.drop_table("award_types")