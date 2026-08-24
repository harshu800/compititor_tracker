"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("clerk_user_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
    )
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("owner_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan", sa.String(), nullable=False, server_default="free"),
    )

    op.create_table(
        "organization_members",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
    )
    op.create_index("ix_org_member_org_user", "organization_members", ["organization_id", "user_id"])

    op.create_table(
        "competitors",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("website_url", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
    )
    op.create_index("ix_competitors_organization_id", "competitors", ["organization_id"])
    op.create_index("ix_competitor_org_status", "competitors", ["organization_id", "status"])

    op.create_table(
        "monitored_pages",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("competitor_id", sa.Uuid(as_uuid=True), sa.ForeignKey("competitors.id"), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("page_type", sa.String(), nullable=False, server_default="custom"),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("monitoring_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("check_frequency", sa.String(), nullable=False, server_default="daily"),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("last_changed_at", sa.DateTime(), nullable=True),
        sa.Column("last_status_code", sa.String(), nullable=True),
        sa.Column("consecutive_failures", sa.String(), nullable=True, server_default="0"),
    )
    op.create_index("ix_monitored_pages_competitor_id", "monitored_pages", ["competitor_id"])

    op.create_table(
        "page_snapshots",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("monitored_page_id", sa.Uuid(as_uuid=True), sa.ForeignKey("monitored_pages.id"), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("structured_content", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("snapshot_url", sa.String(), nullable=True),
        sa.Column("is_retained", sa.String(), nullable=False, server_default="true"),
    )
    op.create_index("ix_page_snapshots_monitored_page_id", "page_snapshots", ["monitored_page_id"])
    op.create_index("ix_page_snapshots_content_hash", "page_snapshots", ["content_hash"])
    op.create_index("ix_snapshot_page_created", "page_snapshots", ["monitored_page_id", "created_at"])

    op.create_table(
        "changes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("monitored_page_id", sa.Uuid(as_uuid=True), sa.ForeignKey("monitored_pages.id"), nullable=False),
        sa.Column("old_snapshot_id", sa.Uuid(as_uuid=True), sa.ForeignKey("page_snapshots.id"), nullable=True),
        sa.Column("new_snapshot_id", sa.Uuid(as_uuid=True), sa.ForeignKey("page_snapshots.id"), nullable=False),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("importance", sa.String(), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("what_changed", sa.Text(), nullable=True),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("diff_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("review_status", sa.String(), nullable=False, server_default="unread"),
    )
    op.create_index("ix_changes_monitored_page_id", "changes", ["monitored_page_id"])
    op.create_index("ix_changes_change_type", "changes", ["change_type"])
    op.create_index("ix_changes_importance", "changes", ["importance"])
    op.create_index("ix_changes_review_status", "changes", ["review_status"])
    op.create_index("ix_change_page_created", "changes", ["monitored_page_id", "created_at"])
    op.create_index("ix_change_importance_created", "changes", ["importance", "created_at"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("change_id", sa.Uuid(as_uuid=True), sa.ForeignKey("changes.id"), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_alerts_organization_id", "alerts", ["organization_id"])
    op.create_index("ix_alerts_change_id", "alerts", ["change_id"])
    op.create_index("ix_alert_org_created", "alerts", ["organization_id", "created_at"])

    op.create_table(
        "notification_settings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False, unique=True),
        sa.Column("critical_email", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("high_email", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("medium_email", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("low_email", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("weekly_digest", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade():
    op.drop_table("notification_settings")
    op.drop_table("alerts")
    op.drop_table("changes")
    op.drop_table("page_snapshots")
    op.drop_table("monitored_pages")
    op.drop_table("competitors")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    op.drop_table("users")
