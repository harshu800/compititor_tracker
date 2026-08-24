"""Shared FastAPI dependencies: plan-limit enforcement helpers, kept here
(not hardcoded per-route) so limits stay configuration-driven."""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Organization, Competitor, MonitoredPage
from app.security.auth import AuthContext, require_org_member

settings = get_settings()

PLAN_LIMITS = {
    "free": {"max_competitors": settings.free_max_competitors, "max_pages": settings.free_max_pages},
    "pro": {"max_competitors": settings.pro_max_competitors, "max_pages": settings.pro_max_pages},
    "business": {"max_competitors": 9999, "max_pages": 99999},
}


def enforce_competitor_limit(db: Session, ctx: AuthContext):
    org = db.query(Organization).filter(Organization.id == ctx.organization_id).first()
    limits = PLAN_LIMITS.get(org.plan, PLAN_LIMITS["free"])
    current = db.query(Competitor).filter(
        Competitor.organization_id == ctx.organization_id, Competitor.status == "active"
    ).count()
    if current >= limits["max_competitors"]:
        raise HTTPException(
            status_code=402,
            detail=f"Plan limit reached: {limits['max_competitors']} competitors on the '{org.plan}' plan.",
        )


def enforce_page_limit(db: Session, ctx: AuthContext, competitor_id: str):
    org = db.query(Organization).filter(Organization.id == ctx.organization_id).first()
    limits = PLAN_LIMITS.get(org.plan, PLAN_LIMITS["free"])
    current = (
        db.query(MonitoredPage)
        .join(Competitor, MonitoredPage.competitor_id == Competitor.id)
        .filter(Competitor.organization_id == ctx.organization_id)
        .count()
    )
    if current >= limits["max_pages"]:
        raise HTTPException(
            status_code=402,
            detail=f"Plan limit reached: {limits['max_pages']} monitored pages on the '{org.plan}' plan.",
        )
