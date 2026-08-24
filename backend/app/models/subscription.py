from sqlalchemy import Column, String, Integer, ForeignKey, Index
from app.models.column_types import GUID
from app.models.base import TimestampedBase


class Subscription(TimestampedBase):
    """Payment audit trail for Razorpay checkout. One row per checkout
    attempt (not per active subscription — this is a simple pay-to-upgrade
    MVP model, not a recurring-subscription integration). The authoritative
    plan for an org always lives on Organization.plan; this table exists so
    every upgrade has a verifiable paper trail (order -> payment -> webhook
    confirmation) and so a webhook can be processed idempotently."""
    __tablename__ = "subscriptions"

    organization_id = Column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)
    plan = Column(String, nullable=False)  # the plan this checkout is for, e.g. "pro"
    amount = Column(Integer, nullable=False)  # smallest currency unit (paise for INR)
    currency = Column(String, nullable=False, default="INR")

    razorpay_order_id = Column(String, nullable=False, unique=True, index=True)
    razorpay_payment_id = Column(String, nullable=True, unique=True, index=True)
    razorpay_signature = Column(String, nullable=True)

    status = Column(String, nullable=False, default="created")  # created | paid | failed

    __table_args__ = (
        Index("ix_subscription_org_created", "organization_id", "created_at"),
    )
