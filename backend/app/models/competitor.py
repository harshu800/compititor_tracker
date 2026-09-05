from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index
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
    # Seeded by /api/v1/demo/seed for onboarding/exploration. Excluded from
    # plan-limit counts (see app/api/deps.py) so a real user's demo data
    # can never block or inflate their actual usage against their plan.
    is_demo = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_competitor_org_status", "organization_id", "status"),
    )
