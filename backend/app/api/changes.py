from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Change, MonitoredPage, Competitor
from app.schemas.change import ChangeOut, ChangeReviewUpdate
from app.security.auth import AuthContext, require_org_member

router = APIRouter(prefix="/api/v1/changes", tags=["changes"])

VALID_REVIEW_STATUSES = {"unread", "reviewed", "important", "ignored"}


def _org_change_query(db: Session, org_id: str):
    return (
        db.query(Change)
        .join(MonitoredPage, Change.monitored_page_id == MonitoredPage.id)
        .join(Competitor, MonitoredPage.competitor_id == Competitor.id)
        .filter(Competitor.organization_id == org_id)
    )


@router.get("", response_model=list[ChangeOut])
def list_changes(
    competitor_id: UUID | None = None,
    change_type: str | None = None,
    importance: str | None = None,
    review_status: str | None = None,
    days: int | None = Query(default=None, description="Filter to last N days"),
    search: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    ctx: AuthContext = Depends(require_org_member),
    db: Session = Depends(get_db),
):
    q = _org_change_query(db, ctx.organization_id)
    if competitor_id:
        q = q.filter(Competitor.id == competitor_id)
    if change_type:
        q = q.filter(Change.change_type == change_type)
    if importance:
        q = q.filter(Change.importance == importance)
    if review_status:
        q = q.filter(Change.review_status == review_status)
    if days:
        q = q.filter(Change.created_at >= datetime.utcnow() - timedelta(days=days))
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Change.summary.ilike(like), Change.what_changed.ilike(like),
                          Competitor.name.ilike(like)))

    return (
        q.order_by(Change.created_at.desc())
        .offset(offset).limit(limit)
        .all()
    )


@router.get("/{change_id}", response_model=ChangeOut)
def get_change(change_id: UUID, ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    change = _org_change_query(db, ctx.organization_id).filter(Change.id == change_id).first()
    if change is None:
        raise HTTPException(status_code=404, detail="Change not found")
    return change


@router.patch("/{change_id}/review", response_model=ChangeOut)
def update_review_status(
    change_id: UUID, payload: ChangeReviewUpdate,
    ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db),
):
    if payload.review_status not in VALID_REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail=f"review_status must be one of {sorted(VALID_REVIEW_STATUSES)}")
    change = _org_change_query(db, ctx.organization_id).filter(Change.id == change_id).first()
    if change is None:
        raise HTTPException(status_code=404, detail="Change not found")
    change.review_status = payload.review_status
    db.add(change)
    db.commit()
    db.refresh(change)
    return change


@router.get("/export/csv")
def export_changes_csv(
    days: int = 30,
    ctx: AuthContext = Depends(require_org_member),
    db: Session = Depends(get_db),
):
    import csv
    import io
    from fastapi.responses import StreamingResponse

    changes = (
        _org_change_query(db, ctx.organization_id)
        .filter(Change.created_at >= datetime.utcnow() - timedelta(days=days))
        .order_by(Change.created_at.desc())
        .all()
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["competitor", "page", "change_type", "importance", "impact_score",
                      "summary", "detected_at", "url"])
    for c in changes:
        page = db.query(MonitoredPage).filter(MonitoredPage.id == c.monitored_page_id).first()
        competitor = db.query(Competitor).filter(Competitor.id == page.competitor_id).first() if page else None
        writer.writerow([
            competitor.name if competitor else "", page.page_type if page else "",
            c.change_type, c.importance, c.impact_score, c.summary,
            c.created_at.isoformat(), page.url if page else "",
        ])
    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv",
                              headers={"Content-Disposition": "attachment; filename=changes.csv"})
