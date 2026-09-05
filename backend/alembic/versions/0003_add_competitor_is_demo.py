"""add is_demo flag to competitors

Revision ID: 0003_is_demo
Revises: 0002_subscriptions
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_is_demo"
down_revision = "0002_subscriptions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "competitors",
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("competitors", "is_demo")
