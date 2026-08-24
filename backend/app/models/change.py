from sqlalchemy import Column, String, Text, Float, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.models.column_types import GUID
from app.models.base import TimestampedBase

PortableJSON = JSON().with_variant(JSONB(), "postgresql")


class Change(TimestampedBase):
    __tablename__ = "changes"
    monitored_page_id = Column(GUID(), ForeignKey("monitored_pages.id"), nullable=False, index=True)
    old_snapshot_id = Column(GUID(), ForeignKey("page_snapshots.id"), nullable=True)
    new_snapshot_id = Column(GUID(), ForeignKey("page_snapshots.id"), nullable=False)

    change_type = Column(String, nullable=False, index=True)
    # pricing | feature | positioning | product | offer | cta | content | messaging | legal | design | other
    importance = Column(String, nullable=False, index=True)  # critical | high | medium | low
    impact_score = Column(Float, nullable=False, default=0.0)  # 0-100, backend-owned

    summary = Column(Text, nullable=True)
    what_changed = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)

    diff_json = Column(PortableJSON, nullable=True)  # added/removed/modified

    review_status = Column(String, nullable=False, default="unread", index=True)
    # unread | reviewed | important | ignored

    __table_args__ = (
        Index("ix_change_page_created", "monitored_page_id", "created_at"),
        Index("ix_change_importance_created", "importance", "created_at"),
    )
