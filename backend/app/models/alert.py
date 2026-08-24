from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from app.models.column_types import GUID
from app.models.base import TimestampedBase


class Alert(TimestampedBase):
    __tablename__ = "alerts"
    organization_id = Column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    change_id = Column(GUID(), ForeignKey("changes.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)  # email | in_app
    severity = Column(String, nullable=False)  # critical | high | medium | low
    sent = Column(Boolean, nullable=False, default=False)
    sent_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_alert_org_created", "organization_id", "created_at"),
    )
