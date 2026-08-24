"""
Razorpay checkout flow for upgrading an organization to the Pro plan.

Two independent confirmations, by design:
  1. `verify_payment` — called by the frontend right after Razorpay
     Checkout's success callback. Verifies the HMAC signature Razorpay
     returns and upgrades the org immediately, for a snappy UI. This alone
     is NOT treated as fully trustworthy (a compromised or buggy client
     could skip it) — it's a UX optimization, not the authority.
  2. `handle_webhook_payment_captured` — the actual source of truth.
     Razorpay calls our webhook server-to-server on payment.captured,
     independent of whether the client's browser tab is even still open.
     Idempotent: a Subscription row can only move created -> paid once,
     keyed on razorpay_payment_id's uniqueness constraint.

Never trust plan/amount values from the client — the amount charged is
always looked up from settings.pro_plan_amount server-side when creating
the order, never accepted as a request parameter.
"""
import hmac
import hashlib
import logging

from razorpay.errors import SignatureVerificationError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Organization, Subscription
from app.services.billing.razorpay_client import get_razorpay_client

logger = logging.getLogger(__name__)
settings = get_settings()

SUPPORTED_UPGRADE_PLANS = {"pro"}  # Business is contact-sales only, not self-serve checkout


class BillingError(ValueError):
    pass


def downgrade_to_free(db: Session, organization_id: str) -> dict:
    """No payment involved — Free requires no Razorpay order at all, just
    an immediate plan change. Kept as its own explicit function (rather
    than overloading create_upgrade_order with plan="free") because the
    two have genuinely different flows: one creates a payable order and
    waits for confirmation, the other takes effect immediately."""
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if org is None:
        raise BillingError("Organization not found")
    if org.plan == "free":
        raise BillingError("Organization is already on the free plan")

    org.plan = "free"
    db.add(org)
    db.commit()

    return {"status": "downgraded", "plan": "free"}


def create_upgrade_order(db: Session, organization_id: str, plan: str) -> dict:
    if plan not in SUPPORTED_UPGRADE_PLANS:
        raise BillingError(f"Self-serve checkout only supports: {sorted(SUPPORTED_UPGRADE_PLANS)}")

    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if org is None:
        raise BillingError("Organization not found")
    if org.plan == plan:
        raise BillingError(f"Organization is already on the '{plan}' plan")

    amount = settings.pro_plan_amount
    currency = settings.pro_plan_currency

    client = get_razorpay_client()
    order = client.order.create({
        "amount": amount,
        "currency": currency,
        "receipt": f"org_{organization_id}_{plan}",
        "notes": {"organization_id": str(organization_id), "plan": plan},
    })

    subscription = Subscription(
        organization_id=organization_id, plan=plan, amount=amount, currency=currency,
        razorpay_order_id=order["id"], status="created",
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return {
        "order_id": order["id"],
        "amount": amount,
        "currency": currency,
        "key_id": settings.razorpay_key_id,
        "subscription_id": str(subscription.id),
    }


def verify_payment(
    db: Session, organization_id: str,
    razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str,
) -> dict:
    subscription = (
        db.query(Subscription)
        .filter(Subscription.razorpay_order_id == razorpay_order_id, Subscription.organization_id == organization_id)
        .first()
    )
    if subscription is None:
        raise BillingError("No matching checkout session found for this organization")
    if subscription.status == "paid":
        return {"status": "already_upgraded", "plan": subscription.plan}

    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
    except SignatureVerificationError:
        raise BillingError("Payment signature verification failed")

    subscription.razorpay_payment_id = razorpay_payment_id
    subscription.razorpay_signature = razorpay_signature
    subscription.status = "paid"
    db.add(subscription)

    org = db.query(Organization).filter(Organization.id == organization_id).first()
    org.plan = subscription.plan
    db.add(org)
    db.commit()

    return {"status": "upgraded", "plan": subscription.plan}


def verify_webhook_signature(body: bytes, signature_header: str) -> bool:
    if not settings.razorpay_webhook_secret:
        return False
    expected = hmac.new(
        settings.razorpay_webhook_secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


def handle_webhook_payment_captured(db: Session, payload: dict) -> dict:
    """Authoritative confirmation path, independent of the client. Safe to
    call multiple times for the same payment (Razorpay retries webhooks) —
    a Subscription already marked 'paid' is left untouched."""
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")

    if not order_id:
        return {"status": "ignored_no_order_id"}

    subscription = db.query(Subscription).filter(Subscription.razorpay_order_id == order_id).first()
    if subscription is None:
        logger.warning("Webhook payment.captured for unknown order_id=%s", order_id)
        return {"status": "unknown_order"}

    if subscription.status == "paid":
        return {"status": "already_processed"}

    subscription.razorpay_payment_id = payment_id
    subscription.status = "paid"
    db.add(subscription)

    org = db.query(Organization).filter(Organization.id == subscription.organization_id).first()
    if org:
        org.plan = subscription.plan
        db.add(org)

    db.commit()
    return {"status": "upgraded", "organization_id": str(subscription.organization_id), "plan": subscription.plan}
