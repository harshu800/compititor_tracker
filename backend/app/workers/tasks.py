import asyncio
import logging
import random
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import MonitoredPage, Competitor, Change
from app.services.monitoring.pipeline import check_page
from app.services.alerts.alert_service import process_alert_for_change
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

FREQUENCY_TO_TIMEDELTA = {
    "daily": timedelta(hours=24),
    "weekly": timedelta(days=7),
}

MAX_RETRIES = 3


def _is_due(page: MonitoredPage) -> bool:
    if not page.monitoring_enabled:
        return False
    if page.last_checked_at is None:
        return True
    interval = FREQUENCY_TO_TIMEDELTA.get(page.check_frequency, timedelta(hours=24))
    return datetime.utcnow() - page.last_checked_at >= interval


@celery_app.task(name="app.workers.tasks.check_all_due_pages")
def check_all_due_pages():
    """Scheduled every 15 min by Celery beat. Finds pages due for a check
    and enqueues each with random jitter so we don't hammer every
    competitor site at exactly the same second."""
    db = SessionLocal()
    try:
        pages = db.query(MonitoredPage).filter(MonitoredPage.monitoring_enabled == True).all()  # noqa: E712
        due = [p for p in pages if _is_due(p)]
        for page in due:
            jitter_seconds = random.randint(0, 600)  # up to 10 min spread
            check_monitored_page.apply_async(args=[str(page.id)], countdown=jitter_seconds)
        return {"queued": len(due)}
    finally:
        db.close()


@celery_app.task(
    name="app.workers.tasks.check_monitored_page",
    bind=True, max_retries=MAX_RETRIES, default_retry_delay=300,
)
def check_monitored_page(self, monitored_page_id: str):
    db = SessionLocal()
    try:
        page = db.query(MonitoredPage).filter(MonitoredPage.id == monitored_page_id).first()
        if page is None:
            return {"status": "page_not_found"}

        competitor = db.query(Competitor).filter(Competitor.id == page.competitor_id).first()

        try:
            result = asyncio.run(check_page(
                db, page, competitor.name if competitor else "Unknown",
                user_company_description="", user_product_category="",
            ))
        except Exception as exc:
            logger.exception("check_page failed for page %s", monitored_page_id)
            raise self.retry(exc=exc)

        if result.get("status") == "change_detected":
            change = db.query(Change).filter(Change.id == result["change_id"]).first()
            if change:
                process_alert_for_change(db, change)  # creates in_app + (maybe) pending email Alert rows
                send_pending_email_alerts.delay(str(change.id))

        return result
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.send_pending_email_alerts")
def send_pending_email_alerts(change_id: str):
    """Sends any unsent email Alert rows created for this change."""
    from app.models import Alert, MonitoredPage, Competitor, User, OrganizationMember
    from app.services.alerts.email_provider import get_email_provider
    from app.services.alerts.alert_service import render_change_email

    db = SessionLocal()
    try:
        change = db.query(Change).filter(Change.id == change_id).first()
        if not change:
            return {"status": "change_not_found"}

        page = db.query(MonitoredPage).filter(MonitoredPage.id == change.monitored_page_id).first()
        competitor = db.query(Competitor).filter(Competitor.id == page.competitor_id).first()

        pending = (
            db.query(Alert)
            .filter(Alert.change_id == change.id, Alert.channel == "email", Alert.sent == False)  # noqa: E712
            .all()
        )
        if not pending:
            return {"status": "no_pending_alerts"}

        member = (
            db.query(OrganizationMember)
            .filter(OrganizationMember.organization_id == competitor.organization_id,
                    OrganizationMember.role == "owner")
            .first()
        )
        recipient_user = db.query(User).filter(User.id == member.user_id).first() if member else None
        if not recipient_user:
            return {"status": "no_recipient"}

        subject, html = render_change_email(competitor.name, change)
        provider = get_email_provider()
        ok = provider.send(recipient_user.email, subject, html)

        for alert in pending:
            alert.sent = ok
            alert.sent_at = datetime.utcnow() if ok else None
            db.add(alert)
        db.commit()
        return {"status": "sent" if ok else "failed", "count": len(pending)}
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.generate_all_weekly_digests")
def generate_all_weekly_digests():
    from app.models import Organization
    db = SessionLocal()
    try:
        orgs = db.query(Organization).all()
        for org in orgs:
            generate_weekly_digest.delay(str(org.id))
        return {"queued_orgs": len(orgs)}
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.generate_weekly_digest")
def generate_weekly_digest(organization_id: str):
    from app.services.reports.digest import build_weekly_digest, send_digest_email
    db = SessionLocal()
    try:
        digest = build_weekly_digest(db, organization_id)
        if digest["total_changes"] == 0:
            return {"status": "no_changes_this_week"}
        send_digest_email(db, organization_id, digest)
        return {"status": "sent", "total_changes": digest["total_changes"]}
    finally:
        db.close()
