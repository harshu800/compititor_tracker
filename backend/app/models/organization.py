import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, UniqueConstraint, Index
from app.models.column_types import GUID
from datetime import datetime
from app.models.base import TimestampedBase
from app.database import Base


class Organization(TimestampedBase):
    __tablename__ = "organizations"
    name = Column(String, nullable=False)
    owner_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    plan = Column(String, nullable=False, default="free")  # free | pro | business


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False, default="member")  # owner | admin | member
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
        Index("ix_org_member_org_user", "organization_id", "user_id"),
    )
