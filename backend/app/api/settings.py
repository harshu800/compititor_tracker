from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NotificationSettings
from app.security.auth import AuthContext, require_org_member

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class NotificationSettingsIn(BaseModel):
    critical_email: bool | None = None
    high_email: bool | None = None
    medium_email: bool | None = None
    low_email: bool | None = None
    weekly_digest: bool | None = None


def _get_or_create(db: Session, org_id: str) -> NotificationSettings:
    row = db.query(NotificationSettings).filter(NotificationSettings.organization_id == org_id).first()
    if row is None:
        row = NotificationSettings(organization_id=org_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/notifications")
def get_notification_settings(ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    row = _get_or_create(db, ctx.organization_id)
    return {
        "critical_email": row.critical_email, "high_email": row.high_email,
        "medium_email": row.medium_email, "low_email": row.low_email,
        "weekly_digest": row.weekly_digest,
    }


@router.patch("/notifications")
def update_notification_settings(
    payload: NotificationSettingsIn,
    ctx: AuthContext = Depends(require_org_member),
    db: Session = Depends(get_db),
):
    row = _get_or_create(db, ctx.organization_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"status": "updated"}
