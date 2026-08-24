"""Decides whether a detected Change should trigger an alert, per the
organization's notification_settings, and renders the email. Never emails
for every tiny copy edit — only changes that are already `meaningful`
(passed the diff engine's threshold) AND meet the org's minimum severity
preference for email."""
from sqlalchemy.orm import Session

from app.models import Change, Alert, NotificationSettings, MonitoredPage, Competitor
from app.services.alerts.email_provider import get_email_provider

SEVERITY_SETTING_FIELD = {
    "critical": "critical_email",
    "high": "high_email",
    "medium": "medium_email",
    "low": "low_email",
}


def _should_email(settings_row: NotificationSettings | None, importance: str) -> bool:
    if settings_row is None:
        # Sensible default: email critical/high only, matches spec section 26 default.
        return importance in ("critical", "high")
    field = SEVERITY_SETTING_FIELD.get(importance)
    return bool(getattr(settings_row, field, False)) if field else False


def render_change_email(competitor_name: str, change: Change) -> tuple[str, str]:
    subject = f"[{change.importance.upper()}] {competitor_name} changed {change.change_type}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 560px;">
      <h2>Competitor Change Detected</h2>
      <p><strong>Competitor:</strong> {competitor_name}</p>
      <p><strong>Change type:</strong> {change.change_type}</p>
      <p><strong>Impact:</strong> {change.importance.capitalize()}</p>
      <p><strong>What changed:</strong> {change.what_changed}</p>
      <p><strong>Why it matters:</strong> {change.why_it_matters}</p>
      <p><strong>Recommended action:</strong> {change.recommended_action}</p>
      <p><a href="#">View change</a></p>
    </div>
    """
    return subject, html


def process_alert_for_change(db: Session, change: Change) -> list[Alert]:
    page = db.query(MonitoredPage).filter(MonitoredPage.id == change.monitored_page_id).first()
    competitor = db.query(Competitor).filter(Competitor.id == page.competitor_id).first()
    settings_row = (
        db.query(NotificationSettings)
        .filter(NotificationSettings.organization_id == competitor.organization_id)
        .first()
    )

    alerts_created = []

    # In-app alert: always created for every meaningful change (dashboard feed).
    in_app = Alert(organization_id=competitor.organization_id, change_id=change.id,
                    channel="in_app", severity=change.importance, sent=True)
    db.add(in_app)
    alerts_created.append(in_app)

    if _should_email(settings_row, change.importance):
        email_alert = Alert(organization_id=competitor.organization_id, change_id=change.id,
                             channel="email", severity=change.importance, sent=False)
        db.add(email_alert)
        db.flush()

        # In production this recipient list would come from org members'
        # emails; simplified here to the org owner for MVP scope.
        # (Left as a TODO hook — see workers/tasks.py send_email_alert.)
        alerts_created.append(email_alert)

    db.commit()
    return alerts_created
