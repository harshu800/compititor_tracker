import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///./test_webhooks.db")
os.environ["AI_PROVIDER"] = os.environ.get("AI_PROVIDER", "mock")
os.environ["ENVIRONMENT"] = "development"

from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app import models  # noqa: E402,F401
import app.api.webhooks as webhooks_module  # noqa: E402

Base.metadata.create_all(bind=engine)
client = TestClient(app)

TEST_SECRET = "whsec_test_secret_dGVzdHNlY3JldA=="


@pytest.fixture(autouse=True)
def _with_webhook_secret():
    """Patch the already-imported webhooks module's live settings object
    directly, rather than relying on being the first test file in the
    pytest session to import app.main (whichever module gets there first
    determines what every later `settings = get_settings()` snapshot
    holds — see app/api/internal.py's tests for the same pattern, and the
    comment there for why this matters more than it might look like)."""
    original = webhooks_module.settings.clerk_webhook_secret
    webhooks_module.settings.clerk_webhook_secret = TEST_SECRET
    yield
    webhooks_module.settings.clerk_webhook_secret = original


def test_webhook_rejects_missing_signature_headers():
    resp = client.post("/api/v1/webhooks/clerk", json={"type": "user.created", "data": {"id": "user_1"}})
    assert resp.status_code == 401


def test_webhook_rejects_invalid_signature():
    resp = client.post(
        "/api/v1/webhooks/clerk",
        json={"type": "user.created", "data": {"id": "user_1"}},
        headers={"svix-id": "msg_1", "svix-timestamp": "1234567890", "svix-signature": "v1,bogus"},
    )
    assert resp.status_code == 401


def test_webhook_requires_secret_configured():
    webhooks_module.settings.clerk_webhook_secret = ""
    resp = client.post("/api/v1/webhooks/clerk", json={"type": "user.created", "data": {}})
    assert resp.status_code == 500
