"""Fast, cheap fetcher for the vast majority of pages (static/server-rendered
HTML). Used by default; only escalate to browser_crawler.py when a page is
known/detected to require JS rendering."""
import httpx

from app.config import get_settings
from app.security.ssrf import validate_and_resolve_url, SSRFValidationError
from app.services.crawler.base import BaseCrawler, FetchResult
from app.services.crawler.robots import is_allowed

settings = get_settings()


class HttpCrawler(BaseCrawler):
    def __init__(self):
        self.timeout = settings.crawler_timeout_seconds
        self.max_bytes = settings.crawler_max_response_bytes
        self.user_agent = settings.crawler_user_agent

    async def fetch(self, url: str) -> FetchResult:
        # 1. SSRF validation before we touch the network at all.
        try:
            validate_and_resolve_url(url)
        except SSRFValidationError as e:
            return FetchResult(url=url, status_code=None, html=None, error=f"blocked_url: {e}")

        # 2. robots.txt compliance.
        if not is_allowed(url, self.user_agent):
            return FetchResult(url=url, status_code=None, html=None, error="disallowed_by_robots_txt")

        headers = {"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"}

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=settings.crawler_max_redirects,
                headers=headers,
                verify=True,  # do not silently ignore SSL errors
            ) as client:
                async with client.stream("GET", url) as resp:
                    # Re-validate the FINAL URL post-redirect against SSRF rules —
                    # a redirect could otherwise be used to pivot to an internal address.
                    final_url = str(resp.url)
                    try:
                        validate_and_resolve_url(final_url)
                    except SSRFValidationError as e:
                        return FetchResult(url=final_url, status_code=resp.status_code, html=None,
                                            error=f"blocked_redirect_target: {e}")

                    content_type = resp.headers.get("content-type", "")
                    if "text/html" not in content_type and "application/xhtml" not in content_type and content_type:
                        return FetchResult(url=final_url, status_code=resp.status_code, html=None,
                                            error=f"unsupported_content_type: {content_type}")

                    chunks = []
                    total = 0
                    truncated = False
                    async for chunk in resp.aiter_bytes():
                        total += len(chunk)
                        if total > self.max_bytes:
                            truncated = True
                            break
                        chunks.append(chunk)

                    body = b"".join(chunks)
                    try:
                        html = body.decode(resp.encoding or "utf-8", errors="replace")
                    except Exception:
                        html = body.decode("utf-8", errors="replace")

                    return FetchResult(
                        url=final_url, status_code=resp.status_code, html=html,
                        truncated=truncated,
                    )
        except httpx.TimeoutException:
            return FetchResult(url=url, status_code=None, html=None, error="timeout")
        except httpx.ConnectError as e:
            return FetchResult(url=url, status_code=None, html=None, error=f"connect_error: {e}")
        except httpx.SSLError as e:
            return FetchResult(url=url, status_code=None, html=None, error=f"ssl_error: {e}")
        except httpx.HTTPError as e:
            return FetchResult(url=url, status_code=None, html=None, error=f"http_error: {e}")
        except Exception as e:
            return FetchResult(url=url, status_code=None, html=None, error=f"unexpected_error: {e}")
