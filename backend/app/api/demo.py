"""Demo mode — seeds realistic, clearly-labeled demo data for the caller's
organization so the product can be explored with zero external API keys
(uses the MockProvider AI classifier and console email provider)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.auth import AuthContext, require_org_member

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.post("/seed")
def seed_demo_data(ctx: AuthContext = Depends(require_org_member), db: Session = Depends(get_db)):
    from demo.seed import seed_for_organization
    result = seed_for_organization(db, ctx.organization_id)
    return {"status": "seeded", **result}
