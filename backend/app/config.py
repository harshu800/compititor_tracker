"""Central application configuration. All tunables come from env vars —
nothing plan-related or security-related should be hardcoded elsewhere."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    # SQLite by default — zero setup, a single file, no separate DB server
    # to run. Swap to a Postgres URL for concurrent-write-heavy production
    # use if you need it (see README) — both are fully supported via the
    # portable GUID/JSON column types in app/models/.
    database_url: str = "sqlite:///./app.db"

    # Auth
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""

    # AI
    ai_provider: str = "mock"  # openai | anthropic | mock
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_model: str = "gpt-4o-mini"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Email
    email_provider: str = "console"  # resend | console
    resend_api_key: str = ""
    email_from: str = "alerts@yourdomain.com"

    # Security
    encryption_key: str = "change-me"
    app_secret: str = "change-me"

    # Crawler
    crawler_user_agent: str = "CompetitorSignalBot/1.0 (+https://competitorsignal.com/bot)"
    crawler_timeout_seconds: int = 15
    crawler_max_response_bytes: int = 3_000_000
    crawler_max_redirects: int = 5

    # Plan limits (defaults — org-level overrides can live in DB later)
    free_max_competitors: int = 5
    free_max_pages: int = 20
    pro_max_competitors: int = 50
    pro_max_pages: int = 500

    # Change detection
    min_change_score_threshold: float = 8.0  # 0-100 normalized diff magnitude
    alert_min_importance: str = "medium"  # only medium+ ever emails, per settings

    # Local trial mode: run Celery tasks synchronously in-process instead of
    # dispatching to a Redis broker/worker. Lets the whole product run with
    # just `pip install` + `uvicorn` — no Postgres/Redis/Docker required.
    # Set to false for any real deployment (crawling should never block a request).
    # On by default: tasks (crawling, classification, alerting) run
    # synchronously in the same process that triggered them, so `uvicorn
    # app.main:app` alone is a fully working app — no Redis, no separate
    # worker/beat process required. Set to false once you want real
    # background scheduling (Celery beat picking up due pages on its own
    # schedule) and non-blocking API responses during a crawl — then run
    # Redis + `celery worker` + `celery beat` alongside the API.
    celery_task_always_eager: bool = True

    # Shared secret for POST /api/v1/internal/trigger-* — lets an external
    # scheduler (e.g. a free GitHub Actions cron workflow) stand in for
    # `celery beat` when you're not running a real worker/beat process
    # (see CELERY_TASK_ALWAYS_EAGER above). Endpoint refuses every request
    # (401) if this is left empty — fails closed, not open, by default.
    cron_trigger_secret: str = ""

    # Misc
    demo_mode: bool = False
    frontend_origin: str = "http://localhost:3000"

    # Environment gate. In production this hard-disables the dev auth
    # fallback (see security/auth.py) even if CLERK_JWKS_URL were somehow
    # left unset, and turns on stricter security headers / cookie flags.
    environment: str = "development"  # development | production

    # Clerk webhook (Svix) signing secret — verifies that /api/v1/webhooks/clerk
    # calls genuinely came from Clerk, not a spoofed request.
    clerk_webhook_secret: str = ""

    # --- Razorpay ---
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    # Self-serve checkout only covers the Pro plan (Business is "contact
    # sales" per the pricing page). Amount is in the smallest currency unit
    # (cents for USD) — adjust to your real pricing before going live.
    pro_plan_amount: int = 2900  # $29.00
    pro_plan_currency: str = "USD"


@lru_cache
def get_settings() -> Settings:
    return Settings()
