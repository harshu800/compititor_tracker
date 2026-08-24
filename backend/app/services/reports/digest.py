"""Weekly digest — built strictly from actual detected Change rows for the
week. Never manufactures trends: if there are 0 or 2 meaningful changes,
the digest says so plainly instead of padding with generic commentary."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Change, MonitoredPage, Competitor, User, OrganizationMember
from app.services.alerts.email_provider import get_email_provider


def build_weekly_digest(db: Session, organization_id: str) -> dict:
    since = datetime.utcnow() - timedelta(days=7)

    changes = (
        db.query(Change)
        .join(MonitoredPage, Change.monitored_page_id == MonitoredPage.id)
        .join(Competitor, MonitoredPage.competitor_id == Competitor.id)
        .filter(Competitor.organization_id == organization_id, Change.created_at >= since)
        .order_by(Change.impact_score.desc())
        .all()
    )

    by_importance = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for c in changes:
        by_importance[c.importance] = by_importance.get(c.importance, 0) + 1

    competitors_changed = {c.monitored_page_id for c in changes}  # proxy; refined below
    competitor_ids = set()
    for c in changes:
        page = db.query(MonitoredPage).filter(MonitoredPage.id == c.monitored_page_id).first()
        if page:
            competitor_ids.add(page.competitor_id)

    top_changes = changes[:5]

    return {
        "total_changes": len(changes),
        "competitors_changed": len(competitor_ids),
        "by_importance": by_importance,
        "top_changes": [
            {
                "id": str(c.id), "summary": c.summary, "importance": c.importance,
                "impact_score": c.impact_score, "change_type": c.change_type,
            }
            for c in top_changes
        ],
    }


def render_digest_email(digest: dict) -> tuple[str, str]:
    subject = f"Your Competitor Weekly Report — {digest['total_changes']} changes"
    if digest["total_changes"] == 0:
        body = "<p>No meaningful competitor changes were detected this week.</p>"
    else:
        items = "".join(
            f"<li>{c['summary']} ({c['importance']})</li>" for c in digest["top_changes"]
        )
        body = f"""
        <div style="font-family: sans-serif; max-width: 560px;">
          <h2>Your Competitor Weekly Report</h2>
          <p>{digest['competitors_changed']} competitor(s) changed this week.</p>
          <p>
            🔴 {digest['by_importance']['critical']} critical &nbsp;
            🟠 {digest['by_importance']['high']} high &nbsp;
            🟡 {digest['by_importance']['medium']} medium &nbsp;
            ⚪ {digest['by_importance']['low']} low
          </p>
          <h3>Most important:</h3>
          <ol>{items}</ol>
        </div>
        """
    return subject, body


def send_digest_email(db: Session, organization_id: str, digest: dict):
    member = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.organization_id == organization_id, OrganizationMember.role == "owner")
        .first()
    )
    if not member:
        return
    user = db.query(User).filter(User.id == member.user_id).first()
    if not user:
        return
    subject, html = render_digest_email(digest)
    get_email_provider().send(user.email, subject, html)
