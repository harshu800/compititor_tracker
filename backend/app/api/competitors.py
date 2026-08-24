import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Competitor
from app.schemas.competitor import CompetitorCreate, CompetitorUpdate, CompetitorOut
from app.security.auth import AuthContext, require_org_member
from app.security.ssrf import is_safe_url_verbose
from app.api.deps import enforce_competitor_limit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/competitors", tags=["competitors"])


@router.get("", response_model=list[CompetitorOut])
def list_competitors(
    status: str | None = None,
    ctx: AuthContext = Depends(require_org_member),
    db: Session = Depends(get_db),
):
    q = db.query(Competitor).filter(Competitor.organization_id == ctx.organization_id)
    if status:
        q = q.filter(Competitor.status == status)
    return q.order_by(Competitor.created_at.desc()).all()


@router.post("", response_model=CompetitorOut, status_code=201)
def create_competitor(
    payload: CompetitorCreate,
    ctx: AuthContext = Depends(require_org_member),
    db: Session = Depends(get_db),
):
    enforce_competitor_limit(db, ctx)

    url_str = str(payload.website_url)
    safe, reason = is_safe_url_verbose(url_str)
    if not safe:
        logger.warning("Rejected competitor website_url=%r: %s", url_str, reason)
        raise HTTPException(status_code=400, detail="This URL cannot be monitored (blocked or unreachable target).")

    competitor = Competitor(
        organization_id=ctx.organization_id,
        name=payload.name,
        website_url=url_str,
        description=payload.description,
        industry=payload.industry,
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


def _get_owned_competitor(db: Session, ctx: AuthContext, competitor_id: UUID) -> Competitor:
    competitor = (
        db.query(Competitor)
        .filter(Competitor.id == competitor_id, Competitor.organization_id == ctx.organization_id)
        .first()
    )
    if competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@router.get("/{competitor_id}", response_model=CompetitorOut)
def get_competitor(competitor_id: UUID, ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    return _get_owned_competitor(db, ctx, competitor_id)


@router.patch("/{competitor_id}", response_model=CompetitorOut)
def update_competitor(
    competitor_id: UUID, payload: CompetitorUpdate,
    ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db),
):
    competitor = _get_owned_competitor(db, ctx, competitor_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(competitor, field, value)
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@router.delete("/{competitor_id}", status_code=204)
def delete_competitor(competitor_id: UUID, ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    competitor = _get_owned_competitor(db, ctx, competitor_id)
    db.delete(competitor)
    db.commit()
    return None
