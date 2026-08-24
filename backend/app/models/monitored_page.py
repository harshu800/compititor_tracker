from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Index
from app.models.column_types import GUID
from app.models.base import TimestampedBase


class MonitoredPage(TimestampedBase):
    __tablename__ = "monitored_pages"
    competitor_id = Column(GUID(), ForeignKey("competitors.id"), nullable=False, index=True)
    url = Column(String, nullable=False)
    page_type = Column(String, nullable=False, default="custom")
    # homepage | pricing | features | product | changelog | blog | custom
    name = Column(String, nullable=True)
    monitoring_enabled = Column(Boolean, nullable=False, default=True)
    check_frequency = Column(String, nullable=False, default="daily")  # daily | weekly
    last_checked_at = Column(DateTime, nullable=True)
    last_changed_at = Column(DateTime, nullable=True)
    last_status_code = Column(String, nullable=True)
    consecutive_failures = Column(String, nullable=True, default="0")

    __table_args__ = (
        Index("ix_monitored_page_competitor", "competitor_id"),
    )
