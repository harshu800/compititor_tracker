"""Produces a STABLE representation of a page's meaningful content so that
re-fetching the same, unchanged page always yields the same hash — even
though raw HTML changes on every request due to timestamps, tracking IDs,
nonces, and rotating ad/session tokens."""
import hashlib
import re

from app.services.crawler.extractor import ExtractedContent

# Patterns that are dynamic noise, not real content, if they slip into body text.
_DYNAMIC_NOISE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\S*"),   # ISO timestamps
    re.compile(r"\b(19|20)\d{2}\b(?=[^\d]*(all rights reserved|copyright|©))", re.IGNORECASE),  # copyright years
    re.compile(r"\b[a-f0-9]{16,}\b"),                            # long hex/session/nonce tokens
    re.compile(r"\butm_[a-z]+=\S+"),                              # tracking params leaking into text
    re.compile(r"\bcsrf[_-]?token\S*", re.IGNORECASE),
]


def normalize_text(raw_text: str) -> str:
    text = raw_text
    for pattern in _DYNAMIC_NOISE_PATTERNS:
        text = pattern.sub("", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def build_structured_content(extracted: ExtractedContent) -> dict:
    """A stable, comparison-friendly structured view — this is what the
    diff engine compares field-by-field (not just the raw text blob)."""
    return {
        "title": extracted.title.strip(),
        "meta_description": extracted.meta_description.strip(),
        "headings": [h.strip() for h in extracted.headings],
        "ctas": extracted.ctas,
        "prices": sorted(extracted.prices, key=lambda p: (p["currency"], p["amount"])),
        "plan_names": sorted(extracted.plan_names),
    }


def calculate_hash(normalized_text: str, structured_content: dict) -> str:
    import json
    payload = normalized_text + json.dumps(structured_content, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
