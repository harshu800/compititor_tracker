from sqlalchemy import Column, Boolean, ForeignKey
from app.models.column_types import GUID
from app.models.base import TimestampedBase


class NotificationSettings(TimestampedBase):
    __tablename__ = "notification_settings"
    organization_id = Column(GUID(), ForeignKey("organizations.id"), nullable=False, unique=True)
    critical_email = Column(Boolean, nullable=False, default=True)
    high_email = Column(Boolean, nullable=False, default=True)
    medium_email = Column(Boolean, nullable=False, default=False)
    low_email = Column(Boolean, nullable=False, default=False)
    weekly_digest = Column(Boolean, nullable=False, default=True)
