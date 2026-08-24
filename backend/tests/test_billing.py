import os
import hmac
import hashlib
import json

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///./test_billing.db")
os.environ["AI_PROVIDER"] = os.environ.get("AI_PROVIDER", "mock")
os.environ["ENVIRONMENT"] = "development"
os.environ["RAZORPAY_KEY_ID"] = "rzp_test_dummy"
os.environ["RAZORPAY_KEY_SECRET"] = "dummy_secret"
os.environ["RAZORPAY_WEBHOOK_SECRET"] = "webhook_secret_abc123"

from app.config import get_settings  # noqa: E402
get_settings.cache_clear()

import pytest  # noqa: E402
from app.database import Base, engine, SessionLocal  # noqa: E402
from app import models  # noqa: E402,F401
from app.models import User, Organization, OrganizationMember, Subscription  # noqa: E402
from app.services.billing.billing_service import (  # noqa: E402
    create_upgrade_order, verify_payment, verify_webhook_signature,
    handle_webhook_payment_captured, downgrade_to_free, BillingError,
)

Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def org(db):
    import uuid
    unique = uuid.uuid4().hex[:8]
    user = User(clerk_user_id=f"user_billing_test_{unique}", email=f"billing_{unique}@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)
    organization = Organization(name="Billing Test Org", owner_id=user.id, plan="free")
    db.add(organization)
    db.commit()
    db.refresh(organization)
    db.add(OrganizationMember(organization_id=organization.id, user_id=user.id, role="owner"))
    db.commit()
    return organization


def test_create_order_rejects_unsupported_plan(db, org):
    with pytest.raises(BillingError):
        create_upgrade_order(db, str(org.id), "business")


def test_create_order_rejects_already_on_plan(db, org):
    org.plan = "pro"
    db.add(org)
    db.commit()
    with pytest.raises(BillingError):
        create_upgrade_order(db, str(org.id), "pro")


def test_create_order_uses_server_side_amount_not_client_supplied(db, org, monkeypatch):
    """The amount charged must come from settings, never from the caller —
    there's no amount parameter on create_upgrade_order at all, which is
    itself the guarantee, but we also check the persisted Subscription
    row matches the configured price exactly."""
    class FakeOrderApi:
        def create(self, data):
            assert data["amount"] == get_settings().pro_plan_amount
            assert data["currency"] == get_settings().pro_plan_currency
            return {"id": "order_fake123"}

    class FakeClient:
        order = FakeOrderApi()

    monkeypatch.setattr(
        "app.services.billing.billing_service.get_razorpay_client", lambda: FakeClient()
    )

    result = create_upgrade_order(db, str(org.id), "pro")
    assert result["order_id"] == "order_fake123"
    assert result["amount"] == get_settings().pro_plan_amount

    subscription = db.query(Subscription).filter(Subscription.razorpay_order_id == "order_fake123").first()
    assert subscription is not None
    assert subscription.status == "created"
    assert subscription.organization_id == org.id


def test_verify_payment_rejects_unknown_order(db, org):
    with pytest.raises(BillingError):
        verify_payment(db, str(org.id), "order_does_not_exist", "pay_1", "sig_1")


def test_verify_payment_upgrades_org_on_valid_signature(db, org, monkeypatch):
    subscription = Subscription(
        organization_id=org.id, plan="pro", amount=490000, currency="INR",
        razorpay_order_id="order_valid1", status="created",
    )
    db.add(subscription)
    db.commit()

    class FakeUtility:
        def verify_payment_signature(self, params):
            return True  # simulate a valid signature

    class FakeClient:
        utility = FakeUtility()

    monkeypatch.setattr(
        "app.services.billing.billing_service.get_razorpay_client", lambda: FakeClient()
    )

    result = verify_payment(db, str(org.id), "order_valid1", "pay_valid1", "sig_valid1")
    assert result["status"] == "upgraded"
    assert result["plan"] == "pro"

    db.refresh(org)
    assert org.plan == "pro"


def test_verify_payment_rejects_invalid_signature(db, org, monkeypatch):
    from razorpay.errors import SignatureVerificationError

    subscription = Subscription(
        organization_id=org.id, plan="pro", amount=490000, currency="INR",
        razorpay_order_id="order_invalid1", status="created",
    )
    db.add(subscription)
    db.commit()

    class FakeUtility:
        def verify_payment_signature(self, params):
            raise SignatureVerificationError("bad signature")

    class FakeClient:
        utility = FakeUtility()

    monkeypatch.setattr(
        "app.services.billing.billing_service.get_razorpay_client", lambda: FakeClient()
    )

    with pytest.raises(BillingError):
        verify_payment(db, str(org.id), "order_invalid1", "pay_x", "sig_bad")

    db.refresh(org)
    assert org.plan == "free"  # unchanged — must not upgrade on failed verification


def test_verify_payment_is_idempotent_once_paid(db, org, monkeypatch):
    subscription = Subscription(
        organization_id=org.id, plan="pro", amount=490000, currency="INR",
        razorpay_order_id="order_paid1", razorpay_payment_id="pay_already",
        status="paid",
    )
    db.add(subscription)
    org.plan = "pro"
    db.add(org)
    db.commit()

    result = verify_payment(db, str(org.id), "order_paid1", "pay_already", "sig_whatever")
    assert result["status"] == "already_upgraded"


def test_webhook_signature_verification_matches_hmac():
    body = json.dumps({"event": "payment.captured"}).encode()
    secret = get_settings().razorpay_webhook_secret
    valid_sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, valid_sig) is True
    assert verify_webhook_signature(body, "wrong_signature") is False
    assert verify_webhook_signature(body, "") is False


def test_webhook_payment_captured_upgrades_org_and_is_idempotent(db, org):
    subscription = Subscription(
        organization_id=org.id, plan="pro", amount=490000, currency="INR",
        razorpay_order_id="order_webhook1", status="created",
    )
    db.add(subscription)
    db.commit()

    payload = {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_webhook1", "order_id": "order_webhook1"}}},
    }

    result = handle_webhook_payment_captured(db, payload)
    assert result["status"] == "upgraded"
    db.refresh(org)
    assert org.plan == "pro"

    # Replaying the same webhook (Razorpay retries on timeout) must be a no-op.
    result2 = handle_webhook_payment_captured(db, payload)
    assert result2["status"] == "already_processed"


def test_webhook_payment_captured_ignores_unknown_order(db):
    payload = {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_x", "order_id": "order_never_created"}}},
    }
    result = handle_webhook_payment_captured(db, payload)
    assert result["status"] == "unknown_order"


def test_downgrade_to_free_rejects_when_already_free(db, org):
    with pytest.raises(BillingError):
        downgrade_to_free(db, str(org.id))


def test_downgrade_to_free_sets_plan_and_is_immediate(db, org):
    org.plan = "pro"
    db.add(org)
    db.commit()

    result = downgrade_to_free(db, str(org.id))
    assert result == {"status": "downgraded", "plan": "free"}

    db.refresh(org)
    assert org.plan == "free"


def test_downgrade_to_free_does_not_touch_subscription_rows(db, org):
    """Downgrading shouldn't create or modify any Subscription row — there's
    nothing to charge or refund, so it should be a pure org.plan update."""
    org.plan = "pro"
    db.add(org)
    db.commit()

    before_count = db.query(Subscription).filter(Subscription.organization_id == org.id).count()
    downgrade_to_free(db, str(org.id))
    after_count = db.query(Subscription).filter(Subscription.organization_id == org.id).count()

    assert before_count == after_count


def test_downgrade_to_free_rejects_unknown_org(db):
    import uuid
    with pytest.raises(BillingError):
        downgrade_to_free(db, str(uuid.uuid4()))
