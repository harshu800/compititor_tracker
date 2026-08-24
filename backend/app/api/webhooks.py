"""
Clerk webhook receiver. Keeps app.User rows in sync with Clerk as the
source of truth for identity, rather than relying solely on lazy
create-on-first-request in security/auth.py (which still works as a
fallback, but webhooks give us prompt sync, email-change propagation,
and cleanup on account deletion — the production-correct pattern).

Every request is verified with Svix (Clerk's webhook signing provider)
using CLERK_WEBHOOK_SECRET. Requests that fail verification are rejected
before any DB write — this endpoint is unauthenticated by Clerk-session
standards (it's called BY Clerk, not by a logged-in user), so signature
verification is the only thing standing between this route and forgery.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from svix.webhooks import Webhook, WebhookVerificationError

from app.config import get_settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


def _verify(request: Request, body: bytes) -> dict:
    if not settings.clerk_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook not configured (CLERK_WEBHOOK_SECRET missing)")

    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }
    try:
        wh = Webhook(settings.clerk_webhook_secret)
        return wh.verify(body, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


@router.post("/clerk")
async def clerk_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    event = _verify(request, body)

    event_type = event.get("type", "")
    data = event.get("data", {})
    clerk_user_id = data.get("id")

    if event_type == "user.created" or event_type == "user.updated":
        emails = data.get("email_addresses", [])
        primary_email_id = data.get("primary_email_address_id")
        email = next((e["email_address"] for e in emails if e.get("id") == primary_email_id), None)
        if not email and emails:
            email = emails[0].get("email_address")

        name_parts = [data.get("first_name"), data.get("last_name")]
        name = " ".join(p for p in name_parts if p) or None

        user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
        if user is None:
            if not email:
                logger.warning("Clerk user.created webhook for %s had no email; skipping", clerk_user_id)
                return {"status": "skipped_no_email"}
            user = User(clerk_user_id=clerk_user_id, email=email, name=name)
            db.add(user)
        else:
            if email:
                user.email = email
            user.name = name
            db.add(user)
        db.commit()
        return {"status": "synced"}

    if event_type == "user.deleted":
        user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
        if user:
            # Keep the row (changes/competitors reference org membership, not
            # the user directly, in most places) but scrub identifying info.
            # A harder delete is a product decision left to the operator.
            user.email = f"deleted-{user.id}@deleted.local"
            user.name = None
            db.add(user)
            db.commit()
        return {"status": "scrubbed"}

    return {"status": "ignored", "type": event_type}


@router.post("/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Server-to-server confirmation from Razorpay — the authoritative
    source of truth for plan upgrades (see billing_service.py docstring).
    Verified with a raw HMAC-SHA256 signature over the exact request body,
    per Razorpay's webhook spec — not the Svix scheme used for Clerk above."""
    from app.services.billing.billing_service import verify_webhook_signature, handle_webhook_payment_captured

    body = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")

    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_type = payload.get("event", "")

    if event_type == "payment.captured":
        return handle_webhook_payment_captured(db, payload)

    return {"status": "ignored", "type": event_type}
