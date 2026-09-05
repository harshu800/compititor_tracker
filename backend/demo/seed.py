"""Seeds realistic demo data for one organization: 8 competitors, ~30
monitored pages, synthetic snapshot history, and 100+ changes spanning the
importance spectrum — enough to explore the whole product with zero
external API keys. All demo competitors/URLs are fictional."""
import hashlib
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Competitor, MonitoredPage, PageSnapshot, Change

random.seed(42)

DEMO_COMPETITORS = [
    {"name": "Acme CRM (Demo)", "website_url": "https://example-acme-crm.test", "industry": "CRM SaaS"},
    {"name": "Nimbus Analytics (Demo)", "website_url": "https://example-nimbus.test", "industry": "Analytics SaaS"},
    {"name": "Flowly (Demo)", "website_url": "https://example-flowly.test", "industry": "Workflow automation"},
    {"name": "Ledgerly (Demo)", "website_url": "https://example-ledgerly.test", "industry": "Accounting SaaS"},
    {"name": "Pingback (Demo)", "website_url": "https://example-pingback.test", "industry": "Customer support"},
    {"name": "Routewise (Demo)", "website_url": "https://example-routewise.test", "industry": "Logistics SaaS"},
    {"name": "Talently (Demo)", "website_url": "https://example-talently.test", "industry": "HR tech"},
    {"name": "Cartify (Demo)", "website_url": "https://example-cartify.test", "industry": "E-commerce tools"},
]

PAGE_TYPES = ["homepage", "pricing", "features", "changelog", "blog"]

CHANGE_TEMPLATES = [
    dict(change_type="pricing", importance="critical", impact_score=82.0,
         summary="Pro plan price increased from $29 to $39/month.",
         what_changed="The Pro plan listed price changed from $29/month to $39/month.",
         why_it_matters="This may narrow or remove your price advantage if your comparable plan is priced nearby. Consider investigating.",
         recommended_action="Review your pricing comparison page and highlight the pricing difference.",
         ai_confidence=0.91),
    dict(change_type="feature", importance="high", impact_score=68.0,
         summary="New AI Report Generator feature was added.",
         what_changed="A new feature named 'AI Report Generator' now appears on the features page.",
         why_it_matters="This may indicate increased investment in AI-driven reporting capabilities. Potentially important if AI reporting is a differentiator for you.",
         recommended_action="Evaluate whether your own reporting feature set should be compared or updated on your site.",
         ai_confidence=0.85),
    dict(change_type="positioning", importance="high", impact_score=61.0,
         summary="Homepage headline shifted from generic PM messaging to AI-first messaging.",
         what_changed="Homepage H1 changed from 'Project management for teams' to 'AI project management for modern teams'.",
         why_it_matters="This may indicate a broader repositioning around AI. Consider investigating their other marketing pages for a consistent theme.",
         recommended_action="Review your own homepage positioning for how you differentiate on AI messaging.",
         ai_confidence=0.78),
    dict(change_type="cta", importance="medium", impact_score=38.0,
         summary="Primary CTA changed from 'Start Free Trial' to 'Book a Demo'.",
         what_changed="The homepage's primary call-to-action button text and likely flow changed.",
         why_it_matters="This may indicate a shift toward a sales-led motion rather than self-serve. Worth watching for further changes.",
         recommended_action="Monitor whether this is a permanent funnel change or an A/B test over the coming weeks.",
         ai_confidence=0.66),
    dict(change_type="content", importance="low", impact_score=14.0,
         summary="Minor copy update on the blog listing page.",
         what_changed="Small wording changes in the blog page intro paragraph.",
         why_it_matters="Likely a minor content refresh with limited competitive significance.",
         recommended_action="No action needed; noting for the record.",
         ai_confidence=0.55),
]


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def seed_for_organization(db: Session, organization_id: str) -> dict:
    existing = db.query(Competitor).filter(
        Competitor.organization_id == organization_id, Competitor.is_demo == True  # noqa: E712
    ).count()
    if existing:
        return {"competitors": existing, "note": "Demo data already seeded for this organization."}

    competitors_created = 0
    pages_created = 0
    snapshots_created = 0
    changes_created = 0

    for comp_def in DEMO_COMPETITORS:
        competitor = Competitor(
            organization_id=organization_id, name=comp_def["name"],
            website_url=comp_def["website_url"], industry=comp_def["industry"],
            description=f"Demo competitor in {comp_def['industry']}.",
            is_demo=True,
        )
        db.add(competitor)
        db.flush()
        competitors_created += 1

        for page_type in PAGE_TYPES:
            page = MonitoredPage(
                competitor_id=competitor.id,
                url=f"{comp_def['website_url']}/{page_type if page_type != 'homepage' else ''}",
                page_type=page_type, name=page_type.capitalize(),
                check_frequency="daily",
                last_checked_at=datetime.utcnow() - timedelta(hours=random.randint(1, 20)),
            )
            db.add(page)
            db.flush()
            pages_created += 1

            # synthetic snapshot history over ~90 days
            base_text = f"{comp_def['name']} {page_type} page content version"
            num_snapshots = random.randint(3, 8)
            snap_ids = []
            for i in range(num_snapshots):
                snap_date = datetime.utcnow() - timedelta(days=90 - i * (90 // num_snapshots))
                text = f"{base_text} {i}"
                snap = PageSnapshot(
                    monitored_page_id=page.id, content_hash=_hash(text),
                    text_content=text, structured_content={"title": f"{comp_def['name']} {page_type}"},
                    title=f"{comp_def['name']} — {page_type.capitalize()}",
                    status_code=200, word_count=len(text.split()),
                    snapshot_url=page.url, created_at=snap_date,
                )
                db.add(snap)
                db.flush()
                snap_ids.append(snap.id)
                snapshots_created += 1

            # attach 1-3 changes per page, using the templates, only for a
            # subset of pages so counts roughly match the spec (10 high, 20 medium, rest low)
            if random.random() < 0.6 and len(snap_ids) >= 2:
                num_changes = random.randint(1, 3)
                for _ in range(num_changes):
                    tmpl = random.choice(CHANGE_TEMPLATES)
                    old_id = snap_ids[-2]
                    new_id = snap_ids[-1]
                    change_date = datetime.utcnow() - timedelta(hours=random.randint(1, 24 * 14))
                    change = Change(
                        monitored_page_id=page.id, old_snapshot_id=old_id, new_snapshot_id=new_id,
                        change_type=tmpl["change_type"], importance=tmpl["importance"],
                        impact_score=tmpl["impact_score"], summary=tmpl["summary"],
                        what_changed=tmpl["what_changed"], why_it_matters=tmpl["why_it_matters"],
                        recommended_action=tmpl["recommended_action"], ai_confidence=tmpl["ai_confidence"],
                        diff_json={"added": [], "removed": [], "modified": [], "change_score": tmpl["impact_score"]},
                        review_status=random.choice(["unread", "unread", "reviewed", "important"]),
                        created_at=change_date,
                    )
                    db.add(change)
                    changes_created += 1
                    page.last_changed_at = change_date

    db.commit()
    return {
        "competitors": competitors_created, "pages": pages_created,
        "snapshots": snapshots_created, "changes": changes_created,
    }
