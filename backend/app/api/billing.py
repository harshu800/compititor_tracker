from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.models import Organization
from app.security.auth import AuthContext, require_org_role
from app.services.billing.billing_service import (
    create_upgrade_order, verify_payment, downgrade_to_free, BillingError,
)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


class CreateOrderRequest(BaseModel):
    plan: str = "pro"  # only "pro" is self-serve today; Business is contact-sales


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.get("/plan")
def get_current_plan(ctx: AuthContext = Depends(require_org_role("owner", "admin", "member")),
                      db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == ctx.organization_id).first()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    settings = get_settings()
    return {
        "plan": org.plan,
        "organization_id": str(org.id),
        "pro_plan_amount": settings.pro_plan_amount,
        "pro_plan_currency": settings.pro_plan_currency,
    }


@router.post("/create-order")
def create_order(
    payload: CreateOrderRequest,
    # Billing changes are an owner/admin action, not something any member can trigger.
    ctx: AuthContext = Depends(require_org_role("owner", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return create_upgrade_order(db, ctx.organization_id, payload.plan)
    except BillingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/downgrade")
def downgrade(
    ctx: AuthContext = Depends(require_org_role("owner", "admin")),
    db: Session = Depends(get_db),
):
    """Switch back to the Free plan. No payment involved, takes effect
    immediately — this intentionally does not touch Subscription/Razorpay
    at all, since there's nothing to charge or refund for moving to Free."""
    try:
        return downgrade_to_free(db, ctx.organization_id)
    except BillingError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify")
def verify(
    payload: VerifyPaymentRequest,
    ctx: AuthContext = Depends(require_org_role("owner", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return verify_payment(
            db, ctx.organization_id,
            payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature,
        )
    except BillingError as e:
        raise HTTPException(status_code=400, detail=str(e))
