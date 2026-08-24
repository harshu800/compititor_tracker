"""
The end-to-end monitoring pipeline for a single page check:

  fetch -> extract -> normalize -> snapshot -> diff -> (meaningful?) ->
  score -> classify -> persist Change -> queue alerts

This is called by the Celery task (workers/tasks.py), kept here as plain
functions so it's independently unit-testable without Celery/DB running.
"""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import MonitoredPage, PageSnapshot, Change
from app.services.crawler.http_crawler import HttpCrawler
from app.services.crawler.browser_crawler import BrowserCrawler
from app.services.crawler.extractor import extract_content
from app.services.crawler.normalizer import normalize_text, build_structured_content, calculate_hash
from app.services.diff.change_detector import detect_change
from app.services.scoring.impact_scoring import calculate_impact_score
from app.services.ai.classifier import classify_change

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_FAILURES_BEFORE_WARNING = 3

# Pages we've seen render near-empty via plain HTTP get escalated to the
# browser crawler on the NEXT check — we never use Playwright by default.
MIN_WORD_COUNT_BEFORE_JS_ESCALATION = 40


async def check_page(db: Session, page: MonitoredPage, competitor_name: str,
                      user_company_description: str = "", user_product_category: str = "") -> dict:
    """Runs one full check cycle for a monitored page. Returns a summary dict
    for logging/testing. Never raises for expected failure modes (timeouts,
    4xx/5xx, SSRF-blocked, etc) — those are recorded, not thrown."""
    crawler = HttpCrawler()
    result = await crawler.fetch(page.url)

    if result.error or result.html is None:
        # If HTTP fetch failed for a content-shape reason (not blocked/SSRF),
        # do NOT auto-escalate to Playwright for every failure — only retry
        # policy handles transient errors (see workers/tasks.py retry logic).
        page.last_checked_at = datetime.utcnow()
        page.last_status_code = str(result.status_code) if result.status_code else "error"
        page.consecutive_failures = str(int(page.consecutive_failures or "0") + 1)
        db.add(page)
        db.commit()
        return {"status": "failed", "error": result.error}

    extracted = extract_content(result.html, url=result.url)

    # Escalate to browser crawler only when content looks suspiciously thin
    # AND this page hasn't already been flagged (avoids re-triggering
    # Playwright every single check for a genuinely thin static page).
    if len(extracted.body_text.split()) < MIN_WORD_COUNT_BEFORE_JS_ESCALATION:
        browser_result = await BrowserCrawler().fetch(page.url)
        if browser_result.html and not browser_result.error:
            extracted = extract_content(browser_result.html, url=browser_result.url)
            result = browser_result

    normalized_text = normalize_text(extracted.body_text)
    structured = build_structured_content(extracted)
    content_hash = calculate_hash(normalized_text, structured)

    previous_snapshot = (
        db.query(PageSnapshot)
        .filter(PageSnapshot.monitored_page_id == page.id)
        .order_by(PageSnapshot.created_at.desc())
        .first()
    )

    new_snapshot = PageSnapshot(
        monitored_page_id=page.id,
        content_hash=content_hash,
        text_content=normalized_text,
        structured_content=structured,
        title=extracted.title,
        meta_description=extracted.meta_description,
        status_code=result.status_code,
        word_count=len(normalized_text.split()),
        snapshot_url=result.url,
    )
    db.add(new_snapshot)

    page.last_checked_at = datetime.utcnow()
    page.last_status_code = str(result.status_code)
    page.consecutive_failures = "0"
    db.add(page)
    db.commit()
    db.refresh(new_snapshot)

    if previous_snapshot is None:
        # First-ever snapshot: baseline only, never a "change".
        return {"status": "baseline_created", "snapshot_id": str(new_snapshot.id)}

    if previous_snapshot.content_hash == content_hash:
        return {"status": "unchanged"}

    diff = detect_change(
        previous_snapshot.text_content, normalized_text,
        previous_snapshot.structured_content, structured,
    )

    if not diff.meaningful:
        logger.info("Change on page %s was below meaningful threshold (score=%s); ignored as noise",
                    page.id, diff.change_score)
        return {"status": "noise_ignored", "change_score": diff.change_score}

    diff_json = {
        "added": diff.added,
        "removed": diff.removed,
        "modified": diff.modified,
        "structured_changes": diff.structured_changes,
        "change_score": diff.change_score,
    }

    classification = await classify_change(
        competitor_name=competitor_name,
        page_type=page.page_type,
        diff=diff_json,
        user_company_description=user_company_description,
        user_product_category=user_product_category,
    )

    impact_score, importance = calculate_impact_score(
        classification.change_type, page.page_type, diff
    )

    change = Change(
        monitored_page_id=page.id,
        old_snapshot_id=previous_snapshot.id,
        new_snapshot_id=new_snapshot.id,
        change_type=classification.change_type,
        importance=importance,               # backend-computed, authoritative
        impact_score=impact_score,             # backend-computed, authoritative
        summary=classification.summary,
        what_changed=classification.what_changed,
        why_it_matters=classification.why_it_matters,
        recommended_action=classification.recommended_action,
        ai_confidence=classification.confidence,
        diff_json=diff_json,
        review_status="unread",
    )
    db.add(change)

    page.last_changed_at = datetime.utcnow()
    db.add(page)
    db.commit()
    db.refresh(change)

    return {"status": "change_detected", "change_id": str(change.id), "importance": importance,
            "impact_score": impact_score}
