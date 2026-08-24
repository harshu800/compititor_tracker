"""
Endpoints for an external scheduler to trigger the same jobs `celery beat`
would normally run on its own schedule. Only relevant if you're running
with CELERY_TASK_ALWAYS_EAGER=true (no real worker/beat process) — see
README "Free deployment" section for the GitHub Actions workflow that
calls these on a cron schedule.

Deliberately NOT part of the normal Clerk/org-scoped auth model: these
operate across every organization (exactly what celery beat itself does),
so there's no single organization to scope the request to. Protected
instead by a single shared secret compared with constant-time comparison,
checked against a header — same pattern as the Clerk/Razorpay webhook
signature checks elsewhere in this file's sibling module, just simpler
since there's no HMAC-over-body requirement here (no request body at all).
"""
import hmac

from fastapi import APIRouter, Header, HTTPException

from app.config import get_settings
from app.workers.tasks import check_all_due_pages, generate_all_weekly_digests

settings = get_settings()

router = APIRouter(prefix="/api/v1/internal", tags=["internal"])


def _verify_secret(provided: str | None) -> None:
    if not settings.cron_trigger_secret:
        raise HTTPException(status_code=401, detail="Trigger endpoint not configured (CRON_TRIGGER_SECRET missing)")
    if not provided or not hmac.compare_digest(provided, settings.cron_trigger_secret):
        raise HTTPException(status_code=401, detail="Invalid or missing trigger secret")


@router.post("/trigger-due-checks")
def trigger_due_checks(x_cron_secret: str | None = Header(default=None)):
    """Stands in for celery beat's every-15-minutes `check_all_due_pages`
    schedule. Safe to call more often than needed — pages that aren't due
    yet are simply skipped, same as the real beat schedule would do."""
    _verify_secret(x_cron_secret)
    result = check_all_due_pages.delay()
    return {"status": "triggered", "result": result.get() if settings.celery_task_always_eager else None}


@router.post("/trigger-weekly-digest")
def trigger_weekly_digest(x_cron_secret: str | None = Header(default=None)):
    """Stands in for celery beat's Monday-9am `generate_all_weekly_digests`
    schedule. Idempotent-ish in effect: an org with zero changes that week
    simply doesn't get an email (see services/reports/digest.py)."""
    _verify_secret(x_cron_secret)
    result = generate_all_weekly_digests.delay()
    return {"status": "triggered", "result": result.get() if settings.celery_task_always_eager else None}
