from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "competitor_tracker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=120,   # hard kill a stuck crawl after 2 minutes
    task_soft_time_limit=90,
    # Local trial mode (no Redis/worker process running): tasks execute
    # synchronously, in the same process that called .delay(). This makes
    # "add competitor" -> initial snapshot happen inline instead of silently
    # doing nothing because no worker is running to pick it up.
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_always_eager,
)

celery_app.conf.beat_schedule = {
    "check-all-due-pages-every-15-min": {
        "task": "app.workers.tasks.check_all_due_pages",
        "schedule": crontab(minute="*/15"),
    },
    "weekly-digest-monday-9am": {
        "task": "app.workers.tasks.generate_all_weekly_digests",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
}
