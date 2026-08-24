from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.models.column_types import GUID
from app.models.base import TimestampedBase

# Portable JSON type: real JSONB on Postgres (production), plain JSON on
# any other dialect (e.g. SQLite for a zero-install local trial).
PortableJSON = JSON().with_variant(JSONB(), "postgresql")


class PageSnapshot(TimestampedBase):
    __tablename__ = "page_snapshots"
    monitored_page_id = Column(GUID(), ForeignKey("monitored_pages.id"), nullable=False, index=True)
    content_hash = Column(String, nullable=False, index=True)
    text_content = Column(Text, nullable=False)          # normalized, meaningful text
    structured_content = Column(PortableJSON, nullable=True)     # extracted headings/prices/CTAs etc
    title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    snapshot_url = Column(String, nullable=True)  # the fetched URL (post-redirect)
    is_retained = Column(String, nullable=False, default="true")  # for retention policy

    __table_args__ = (
        Index("ix_snapshot_page_created", "monitored_page_id", "created_at"),
    )
