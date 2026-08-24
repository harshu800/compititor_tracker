"""Suggests likely pricing/features/changelog/blog URLs by fetching ONLY
the homepage and scanning its own links for common patterns — never
crawls beyond that single page. The user must still approve suggestions
before any of them become monitored_pages (see spec section 25)."""
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.services.crawler.http_crawler import HttpCrawler

PAGE_TYPE_HINTS = {
    "pricing": ["pricing", "plans", "price"],
    "features": ["features", "product", "platform"],
    "changelog": ["changelog", "updates", "releases", "whats-new", "release-notes"],
    "blog": ["blog", "resources/blog", "news"],
}


async def discover_candidate_pages(homepage_url: str) -> dict:
    crawler = HttpCrawler()
    result = await crawler.fetch(homepage_url)
    if result.error or not result.html:
        return {"homepage_reachable": False, "suggestions": []}

    soup = BeautifulSoup(result.html, "lxml")
    base_netloc = urlparse(result.url).netloc

    seen = set()
    suggestions = []

    for page_type, hints in PAGE_TYPE_HINTS.items():
        match = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(result.url, href)
            parsed = urlparse(full_url)
            if parsed.netloc != base_netloc:
                continue  # never suggest external/off-site links
            path_lower = parsed.path.lower()
            if any(hint in path_lower for hint in hints) and full_url not in seen:
                match = full_url
                break
        if match:
            seen.add(match)
            suggestions.append({"page_type": page_type, "url": match, "exists": True})

    suggestions.append({"page_type": "homepage", "url": result.url, "exists": True})
    return {"homepage_reachable": True, "suggestions": suggestions}
