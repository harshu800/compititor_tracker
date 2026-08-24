import logging
import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api import (
    organizations, competitors, pages, changes, dashboard, alerts, reports,
    settings as settings_api, demo, webhooks, billing, internal,
)

settings = get_settings()
logger = logging.getLogger(__name__)


def _validate_production_config() -> None:
    """Fail fast at boot rather than serving traffic with a broken/unsafe
    config. This is the startup half of the production auth guarantee —
    security/auth.py enforces the same rule per-request as defense in depth.

    SQLite is a supported production database for small/single-instance
    deployments — it's a soft warning here, not a hard failure, since
    single-writer file locking and no built-in replication are real but
    situational limitations, not universally disqualifying ones. Everything
    else on this list (auth, webhook signatures, CORS, secrets, blocking
    requests on live crawls) is a hard failure because it's either a
    security hole or breaks correctness outright, not a scaling tradeoff.
    """
    if settings.environment != "production":
        return
    problems = []
    if not settings.clerk_jwks_url or not settings.clerk_secret_key:
        problems.append("CLERK_JWKS_URL / CLERK_SECRET_KEY must be set in production (no dev auth fallback).")
    if not settings.clerk_webhook_secret:
        problems.append("CLERK_WEBHOOK_SECRET must be set in production for webhook verification.")
    if settings.celery_task_always_eager and not settings.cron_trigger_secret:
        problems.append(
            "CELERY_TASK_ALWAYS_EAGER is on with no CRON_TRIGGER_SECRET set — nothing will ever "
            "proactively check due pages (there's no real Celery beat, and no external scheduler "
            "standing in for it). Either set CRON_TRIGGER_SECRET and wire up an external cron "
            "(see .github/workflows/scheduled-checks.yml and the README's \"Free deployment\" "
            "section), or set up Redis + a real Celery worker/beat and set this to false."
        )
    if settings.frontend_origin in ("", "http://localhost:3000"):
        problems.append("FRONTEND_ORIGIN must be set to your real deployed frontend URL in production.")
    if settings.encryption_key in ("", "change-me") or settings.app_secret in ("", "change-me"):
        problems.append("ENCRYPTION_KEY / APP_SECRET must be set to real secrets in production.")
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        problems.append("RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET must be set in production for billing to work.")
    if not settings.razorpay_webhook_secret:
        problems.append("RAZORPAY_WEBHOOK_SECRET must be set in production for webhook verification.")
    if problems:
        raise RuntimeError(
            "Refusing to start with ENVIRONMENT=production due to unsafe configuration:\n- "
            + "\n- ".join(problems)
        )

    if settings.database_url.startswith("sqlite"):
        logger.warning(
            "ENVIRONMENT=production with a SQLite DATABASE_URL. This works for a single-instance "
            "deployment, but SQLite serializes writes (one writer at a time) and the API + Celery "
            "worker must share the same disk — it will NOT work correctly if they run on separate "
            "hosts/containers. If you're scaling beyond one machine or expect meaningful concurrent "
            "write load, switch to Postgres."
        )

    if settings.celery_task_always_eager:
        logger.warning(
            "ENVIRONMENT=production with CELERY_TASK_ALWAYS_EAGER=true (CRON_TRIGGER_SECRET is set, "
            "so an external scheduler is presumably standing in for celery beat — see "
            ".github/workflows/scheduled-checks.yml). This means crawls run inline within whatever "
            "request triggered them: fine for the scheduled cron-trigger requests, but it also means "
            "adding a new competitor's initial snapshot will block that request until the crawl "
            "finishes. If that request latency becomes a problem, or if you're not actually running "
            "the external scheduler, switch to a real Celery worker/beat + Redis instead."
        )


_validate_production_config()

app = FastAPI(title="CompetitorSignal API", version="1.0.0")

# --- Secure CORS: only the configured frontend origin, not "*" ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Organization-Id"],
)


# --- Security headers on every response ---
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


# --- Basic per-IP rate limiting (defense in depth; real deployments should
# also rate limit at the edge/gateway) ---
_request_log: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 120


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    _request_log[client_ip] = [t for t in _request_log[client_ip] if t > window_start]
    if len(_request_log[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    _request_log[client_ip].append(now)
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}


app.include_router(organizations.router)
app.include_router(competitors.router)
app.include_router(pages.router)
app.include_router(changes.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(settings_api.router)
app.include_router(demo.router)
app.include_router(webhooks.router)
app.include_router(billing.router)
app.include_router(internal.router)
