"""
Covers app/main.py::_validate_production_config() — the fail-fast startup
check that gates ENVIRONMENT=production.

Each scenario reimports app.main fresh in a subprocess-like isolated way
(via importlib) since the validation runs once at module import time and
Settings is cached — these tests exercise the validation function directly
against constructed Settings-like objects rather than actually importing
app.main repeatedly in-process, which would only run the check once per
process.
"""
import pytest
from types import SimpleNamespace

from app.main import _validate_production_config


def _settings(**overrides) -> SimpleNamespace:
    defaults = dict(
        environment="production",
        clerk_jwks_url="https://example.clerk.accounts.dev/.well-known/jwks.json",
        clerk_secret_key="sk_live_dummy",
        clerk_webhook_secret="whsec_dummy",
        celery_task_always_eager=False,
        cron_trigger_secret="",
        frontend_origin="https://app.example.com",
        encryption_key="real-secret-key-abc123",
        app_secret="real-app-secret-xyz789",
        razorpay_key_id="rzp_live_dummy",
        razorpay_key_secret="dummy_secret",
        razorpay_webhook_secret="rzp_whsec_dummy",
        database_url="postgresql://user:pass@host/db",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_fully_safe_config_passes(monkeypatch):
    monkeypatch.setattr("app.main.settings", _settings())
    _validate_production_config()  # should not raise


def test_development_environment_skips_all_checks(monkeypatch):
    monkeypatch.setattr("app.main.settings", _settings(environment="development", clerk_jwks_url=""))
    _validate_production_config()  # should not raise — not production


def test_missing_clerk_keys_fails(monkeypatch):
    monkeypatch.setattr("app.main.settings", _settings(clerk_jwks_url="", clerk_secret_key=""))
    with pytest.raises(RuntimeError, match="CLERK_JWKS_URL"):
        _validate_production_config()


def test_eager_mode_without_cron_secret_fails(monkeypatch):
    """This is the free-tier deployment path's failure mode: eager mode
    with nothing external ever triggering due-page checks."""
    monkeypatch.setattr("app.main.settings", _settings(celery_task_always_eager=True, cron_trigger_secret=""))
    with pytest.raises(RuntimeError, match="CELERY_TASK_ALWAYS_EAGER"):
        _validate_production_config()


def test_eager_mode_with_cron_secret_passes(monkeypatch):
    """The intentional free-tier path: eager mode + an external scheduler
    (GitHub Actions cron) standing in for celery beat via CRON_TRIGGER_SECRET.
    This must NOT be rejected — it's a legitimate, documented deployment
    path (.github/workflows/scheduled-checks.yml), not a misconfiguration."""
    monkeypatch.setattr(
        "app.main.settings",
        _settings(celery_task_always_eager=True, cron_trigger_secret="a_real_secret"),
    )
    _validate_production_config()  # should not raise


def test_non_eager_mode_passes_regardless_of_cron_secret(monkeypatch):
    monkeypatch.setattr(
        "app.main.settings",
        _settings(celery_task_always_eager=False, cron_trigger_secret=""),
    )
    _validate_production_config()  # should not raise — real worker/beat path


def test_sqlite_in_production_warns_but_does_not_raise(monkeypatch, caplog):
    monkeypatch.setattr("app.main.settings", _settings(database_url="sqlite:///./app.db"))
    _validate_production_config()  # should not raise
    assert any("SQLite" in record.message for record in caplog.records)


def test_missing_razorpay_keys_fails(monkeypatch):
    monkeypatch.setattr("app.main.settings", _settings(razorpay_key_id="", razorpay_key_secret=""))
    with pytest.raises(RuntimeError, match="RAZORPAY_KEY_ID"):
        _validate_production_config()


def test_default_frontend_origin_fails(monkeypatch):
    monkeypatch.setattr("app.main.settings", _settings(frontend_origin="http://localhost:3000"))
    with pytest.raises(RuntimeError, match="FRONTEND_ORIGIN"):
        _validate_production_config()


def test_placeholder_secrets_fail(monkeypatch):
    monkeypatch.setattr("app.main.settings", _settings(encryption_key="change-me"))
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        _validate_production_config()
