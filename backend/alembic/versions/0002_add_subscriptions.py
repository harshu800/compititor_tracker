"""add subscriptions table (Razorpay billing audit trail)

Revision ID: 0002_subscriptions
Revises: 0001_initial
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_subscriptions"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("plan", sa.String(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="INR"),
        sa.Column("razorpay_order_id", sa.String(), nullable=False),
        sa.Column("razorpay_payment_id", sa.String(), nullable=True),
        sa.Column("razorpay_signature", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="created"),
    )
    op.create_index("ix_subscriptions_organization_id", "subscriptions", ["organization_id"])
    op.create_index("ix_subscriptions_razorpay_order_id", "subscriptions", ["razorpay_order_id"], unique=True)
    op.create_index("ix_subscriptions_razorpay_payment_id", "subscriptions", ["razorpay_payment_id"], unique=True)
    op.create_index("ix_subscription_org_created", "subscriptions", ["organization_id", "created_at"])


def downgrade():
    op.drop_table("subscriptions")
