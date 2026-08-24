from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert
from app.security.auth import AuthContext, require_org_member

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("")
def list_alerts(limit: int = 50, ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    alerts = (
        db.query(Alert)
        .filter(Alert.organization_id == ctx.organization_id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"id": str(a.id), "change_id": str(a.change_id), "channel": a.channel,
         "severity": a.severity, "sent": a.sent, "created_at": a.created_at.isoformat()}
        for a in alerts
    ]
