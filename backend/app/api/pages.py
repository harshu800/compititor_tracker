import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MonitoredPage, Competitor
from app.schemas.page import MonitoredPageCreate, MonitoredPageUpdate, MonitoredPageOut
from app.security.auth import AuthContext, require_org_member
from app.security.ssrf import is_safe_url_verbose
from app.api.deps import enforce_page_limit
from app.api.competitors import _get_owned_competitor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["pages"])

VALID_PAGE_TYPES = {"homepage", "pricing", "features", "product", "changelog", "blog", "custom"}
VALID_FREQUENCIES = {"daily", "weekly"}


@router.get("/competitors/{competitor_id}/pages", response_model=list[MonitoredPageOut])
def list_pages(competitor_id: UUID, ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    _get_owned_competitor(db, ctx, competitor_id)
    return db.query(MonitoredPage).filter(MonitoredPage.competitor_id == competitor_id).all()


@router.post("/competitors/{competitor_id}/pages", response_model=MonitoredPageOut, status_code=201)
def add_page(
    competitor_id: UUID, payload: MonitoredPageCreate,
    ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db),
):
    _get_owned_competitor(db, ctx, competitor_id)
    enforce_page_limit(db, ctx, str(competitor_id))

    if payload.page_type not in VALID_PAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"page_type must be one of {sorted(VALID_PAGE_TYPES)}")
    if payload.check_frequency not in VALID_FREQUENCIES:
        raise HTTPException(status_code=400, detail=f"check_frequency must be one of {sorted(VALID_FREQUENCIES)}")

    url_str = str(payload.url)
    safe, reason = is_safe_url_verbose(url_str)
    if not safe:
        logger.warning("Rejected monitored page url=%r: %s", url_str, reason)
        raise HTTPException(status_code=400, detail="This URL cannot be monitored (blocked or unreachable target).")

    page = MonitoredPage(
        competitor_id=competitor_id, url=url_str, page_type=payload.page_type,
        name=payload.name, check_frequency=payload.check_frequency,
    )
    db.add(page)
    db.commit()
    db.refresh(page)

    # Kick off the initial snapshot asynchronously — API never blocks on crawling.
    try:
        from app.workers.tasks import check_monitored_page
        check_monitored_page.delay(str(page.id))
    except Exception:
        pass  # Celery/Redis may not be running in this environment (e.g. local demo without broker)

    return page


def _get_owned_page(db: Session, ctx: AuthContext, page_id: UUID) -> MonitoredPage:
    page = (
        db.query(MonitoredPage)
        .join(Competitor, MonitoredPage.competitor_id == Competitor.id)
        .filter(MonitoredPage.id == page_id, Competitor.organization_id == ctx.organization_id)
        .first()
    )
    if page is None:
        raise HTTPException(status_code=404, detail="Monitored page not found")
    return page


@router.patch("/pages/{page_id}", response_model=MonitoredPageOut)
def update_page(page_id: UUID, payload: MonitoredPageUpdate,
                 ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    page = _get_owned_page(db, ctx, page_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(page, field, value)
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.delete("/pages/{page_id}", status_code=204)
def delete_page(page_id: UUID, ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    page = _get_owned_page(db, ctx, page_id)
    db.delete(page)
    db.commit()
    return None


@router.post("/pages/discover")
def discover_pages(website_url: str, ctx: AuthContext = Depends(require_org_member)):
    """Suggests common page URLs (pricing/features/changelog/blog) for a
    homepage by inspecting its own links — never crawls the whole site,
    and the caller must still approve which suggestions to actually add."""
    from app.services.crawler.url_discovery import discover_candidate_pages
    safe, reason = is_safe_url_verbose(website_url)
    if not safe:
        logger.warning("Rejected discover website_url=%r: %s", website_url, reason)
        raise HTTPException(status_code=400, detail="URL cannot be inspected (blocked or unreachable).")
    import asyncio
    return asyncio.run(discover_candidate_pages(website_url))
