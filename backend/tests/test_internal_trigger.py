"""Tests for the cron-trigger endpoints that stand in for celery beat
when running without a real worker/beat process (CELERY_TASK_ALWAYS_EAGER,
see the "Free deployment" README section)."""
import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///./test_internal.db")
os.environ["AI_PROVIDER"] = os.environ.get("AI_PROVIDER", "mock")
os.environ["ENVIRONMENT"] = "development"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"

from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app import models  # noqa: E402,F401
import app.api.internal as internal_module  # noqa: E402

Base.metadata.create_all(bind=engine)
client = TestClient(app)

TEST_SECRET = "test-secret-abc123"


@pytest.fixture(autouse=True)
def _with_cron_secret():
    """Patch the already-imported module's live settings object directly —
    do not rely on being the first test file in the pytest session to
    import app.main and set CRON_TRIGGER_SECRET before that happens.
    Whichever test file gets there first determines what every later
    `settings = get_settings()` snapshot at other modules' import time
    holds, since Python caches modules in sys.modules and won't re-run
    their top-level code for a later import — see test_webhooks.py for
    the same pattern and a fuller explanation."""
    original = internal_module.settings.cron_trigger_secret
    internal_module.settings.cron_trigger_secret = TEST_SECRET
    yield
    internal_module.settings.cron_trigger_secret = original


def test_trigger_due_checks_rejects_missing_secret():
    resp = client.post("/api/v1/internal/trigger-due-checks")
    assert resp.status_code == 401


def test_trigger_due_checks_rejects_wrong_secret():
    resp = client.post("/api/v1/internal/trigger-due-checks", headers={"X-Cron-Secret": "wrong"})
    assert resp.status_code == 401


def test_trigger_due_checks_succeeds_with_correct_secret():
    resp = client.post("/api/v1/internal/trigger-due-checks", headers={"X-Cron-Secret": TEST_SECRET})
    assert resp.status_code == 200
    assert resp.json()["status"] == "triggered"


def test_trigger_weekly_digest_rejects_missing_secret():
    resp = client.post("/api/v1/internal/trigger-weekly-digest")
    assert resp.status_code == 401


def test_trigger_weekly_digest_succeeds_with_correct_secret():
    resp = client.post("/api/v1/internal/trigger-weekly-digest", headers={"X-Cron-Secret": TEST_SECRET})
    assert resp.status_code == 200
    assert resp.json()["status"] == "triggered"


def test_trigger_fails_closed_when_secret_not_configured():
    """If CRON_TRIGGER_SECRET is unset entirely, the endpoint must refuse
    every request — not silently accept an empty/no header as valid."""
    internal_module.settings.cron_trigger_secret = ""
    resp = client.post("/api/v1/internal/trigger-due-checks", headers={"X-Cron-Secret": ""})
    assert resp.status_code == 401
