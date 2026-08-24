"""robots.txt compliance. We check the specific path being monitored against
the target site's robots.txt before every fetch, and cache results briefly
to avoid re-fetching robots.txt on every check."""
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.config import get_settings

settings = get_settings()

_robots_cache: dict[str, tuple[float, RobotFileParser]] = {}
_CACHE_TTL_SECONDS = 3600


def _robots_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def is_allowed(url: str, user_agent: str | None = None) -> bool:
    """Returns True if crawling `url` is allowed by the site's robots.txt.
    Fails OPEN on robots.txt fetch errors (many sites don't have one) but
    fails CLOSED (disallow) if the file exists and explicitly disallows."""
    ua = user_agent or settings.crawler_user_agent
    robots_url = _robots_url(url)

    now = time.time()
    cached = _robots_cache.get(robots_url)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        parser = cached[1]
    else:
        parser = RobotFileParser()
        try:
            resp = httpx.get(robots_url, timeout=5, headers={"User-Agent": ua}, follow_redirects=True)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                # No robots.txt (404 etc) -> allow by default.
                parser.parse([])
        except Exception:
            parser.parse([])
        _robots_cache[robots_url] = (now, parser)

    try:
        return parser.can_fetch(ua, url)
    except Exception:
        return True
