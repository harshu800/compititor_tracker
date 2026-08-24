from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Change, MonitoredPage, Competitor
from app.security.auth import AuthContext, require_org_member
from app.api.changes import _org_change_query

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("")
def get_report(
    period_days: int = Query(default=30),
    ctx: AuthContext = Depends(require_org_member),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=period_days)
    base = _org_change_query(db, ctx.organization_id).filter(Change.created_at >= since)

    by_type = dict(
        base.with_entities(Change.change_type, func.count(Change.id)).group_by(Change.change_type).all()
    )
    by_importance = dict(
        base.with_entities(Change.importance, func.count(Change.id)).group_by(Change.importance).all()
    )
    by_competitor = (
        base.with_entities(Competitor.name, func.count(Change.id))
        .group_by(Competitor.name)
        .all()
    )
    over_time = (
        base.with_entities(func.date(Change.created_at), func.count(Change.id))
        .group_by(func.date(Change.created_at))
        .order_by(func.date(Change.created_at))
        .all()
    )

    return {
        "period_days": period_days,
        "changes_by_type": by_type,
        "changes_by_importance": by_importance,
        "changes_by_competitor": {name: count for name, count in by_competitor},
        "changes_over_time": [{"date": str(d), "count": c} for d, c in over_time],
    }
