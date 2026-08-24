from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Competitor, Change, MonitoredPage
from app.security.auth import AuthContext, require_org_member
from app.api.changes import _org_change_query

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    competitors_count = (
        db.query(Competitor)
        .filter(Competitor.organization_id == ctx.organization_id, Competitor.status == "active")
        .count()
    )

    week_ago = datetime.utcnow() - timedelta(days=7)
    changes_this_week = _org_change_query(db, ctx.organization_id).filter(Change.created_at >= week_ago).count()
    important_changes = (
        _org_change_query(db, ctx.organization_id)
        .filter(Change.created_at >= week_ago, Change.importance.in_(["critical", "high"]))
        .count()
    )
    unreviewed = (
        _org_change_query(db, ctx.organization_id)
        .filter(Change.review_status == "unread")
        .count()
    )

    recent_important = (
        _org_change_query(db, ctx.organization_id)
        .filter(Change.importance.in_(["critical", "high"]))
        .order_by(Change.created_at.desc())
        .limit(10)
        .all()
    )

    recent_out = []
    for c in recent_important:
        page = db.query(MonitoredPage).filter(MonitoredPage.id == c.monitored_page_id).first()
        competitor = db.query(Competitor).filter(Competitor.id == page.competitor_id).first() if page else None
        recent_out.append({
            "change_id": str(c.id),
            "competitor_name": competitor.name if competitor else "Unknown",
            "change_type": c.change_type,
            "importance": c.importance,
            "summary": c.summary,
            "created_at": c.created_at.isoformat(),
        })

    return {
        "competitors": competitors_count,
        "changes_this_week": changes_this_week,
        "important_changes": important_changes,
        "unreviewed": unreviewed,
        "recent_important_changes": recent_out,
    }
