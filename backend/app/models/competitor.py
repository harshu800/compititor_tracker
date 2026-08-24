from sqlalchemy import Column, String, Text, ForeignKey, Index
from app.models.column_types import GUID
from app.models.base import TimestampedBase


class Competitor(TimestampedBase):
    __tablename__ = "competitors"
    organization_id = Column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    website_url = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    industry = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")  # active | archived

    __table_args__ = (
        Index("ix_competitor_org_status", "organization_id", "status"),
    )
