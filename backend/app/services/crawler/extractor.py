"""Turns raw HTML into structured, meaningful content: title, meta
description, headings, pricing-looking blocks, CTAs, and body text —
stripping scripts, styles, nav/footer noise, and cookie banners."""
import re
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Comment

# Tags that never carry meaningful competitor content when computing body
# text. Note: "meta" and "link" are deliberately NOT in this list — they
# carry no text() output anyway, and we still need to read <meta name=
# "description"> before any stripping happens.
NOISE_TAGS = ["script", "style", "noscript", "svg", "iframe"]

# Class/id substrings commonly used for cookie banners / consent widgets.
COOKIE_BANNER_HINTS = [
    "cookie", "consent", "gdpr", "cc-banner", "cc-window", "onetrust", "osano",
]

# Common nav/footer/header landmark tags — kept out of "content" text but
# their CTA links are still scanned separately.
STRUCTURAL_TAGS = ["nav", "header", "footer"]

CTA_KEYWORDS = [
    "start free trial", "book a demo", "get started", "sign up", "try free",
    "request demo", "contact sales", "buy now", "subscribe",
]

PRICE_PATTERN = re.compile(
    r"(?P<currency>[$€£])\s?(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s?"
    r"(?:/\s?(?P<period>mo|month|yr|year|user|seat))?",
    re.IGNORECASE,
)


@dataclass
class ExtractedContent:
    title: str = ""
    meta_description: str = ""
    headings: list[str] = field(default_factory=list)
    body_text: str = ""
    ctas: list[str] = field(default_factory=list)
    prices: list[dict] = field(default_factory=list)
    plan_names: list[str] = field(default_factory=list)


def _looks_like_cookie_banner(tag) -> bool:
    classes = tag.get("class") or []
    tag_id = tag.get("id") or ""
    attrs = (" ".join(classes) + " " + tag_id).lower()
    return any(hint in attrs for hint in COOKIE_BANNER_HINTS)


def extract_content(html: str, url: str = "") -> ExtractedContent:
    soup = BeautifulSoup(html or "", "lxml")

    for tag_name in NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Drop cookie-consent widgets wherever they appear in the DOM.
    # Snapshot the list first since decompose() mutates the tree (and can
    # invalidate already-decomposed descendants encountered later in the loop).
    for tag in list(soup.find_all(True)):
        if tag.attrs is None or tag.parent is None:
            continue  # already removed as a descendant of an earlier match
        if _looks_like_cookie_banner(tag):
            tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    headings = [
        h.get_text(strip=True)
        for h in soup.find_all(["h1", "h2", "h3"])
        if h.get_text(strip=True)
    ]

    # Extract CTAs from buttons/links by keyword match (kept separate from
    # nav/footer body-text stripping since CTAs often live in a header).
    ctas = []
    for el in soup.find_all(["a", "button"]):
        text = el.get_text(strip=True)
        if text and any(kw in text.lower() for kw in CTA_KEYWORDS):
            ctas.append(text)

    # Strip nav/header/footer for the main body text — these change
    # constantly (menus, copyright years, social links) without reflecting
    # any real competitor decision.
    for tag_name in STRUCTURAL_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    body_text = soup.get_text(separator=" ", strip=True)
    body_text = re.sub(r"\s+", " ", body_text).strip()

    prices = []
    for m in PRICE_PATTERN.finditer(body_text):
        prices.append({
            "currency": m.group("currency"),
            "amount": float(m.group("amount").replace(",", "")),
            "period": (m.group("period") or "").lower() or None,
            "raw": m.group(0).strip(),
        })

    plan_names = _guess_plan_names(body_text)

    return ExtractedContent(
        title=title,
        meta_description=meta_description,
        headings=headings,
        body_text=body_text,
        ctas=sorted(set(ctas)),
        prices=prices,
        plan_names=plan_names,
    )


_COMMON_PLAN_WORDS = {"free", "starter", "basic", "pro", "professional", "team",
                       "business", "growth", "enterprise", "premium", "plus"}


def _guess_plan_names(body_text: str) -> list[str]:
    """Heuristic only — used as a hint for the pricing extractor / AI
    classifier, never presented as ground truth on its own."""
    found = []
    lower = body_text.lower()
    for word in _COMMON_PLAN_WORDS:
        if re.search(rf"\b{word}\b", lower):
            found.append(word.capitalize())
    return found
