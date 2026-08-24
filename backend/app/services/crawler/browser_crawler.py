"""Playwright-backed fetcher, used ONLY when a page is known to require
JS rendering (detected upstream — e.g. http_crawler returned near-empty
body on a page flagged as JS-heavy, or the user marked it explicitly).
Never used as the default path — Playwright is expensive and each browser
context is thrown away after one page, with network/security hardening."""
from app.config import get_settings
from app.security.ssrf import validate_and_resolve_url, SSRFValidationError
from app.services.crawler.base import BaseCrawler, FetchResult
from app.services.crawler.robots import is_allowed

settings = get_settings()

_PRIVATE_HOST_FRAGMENTS = ("localhost", "127.0.0.1", "169.254.", "10.", "192.168.")


class BrowserCrawler(BaseCrawler):
    """Requires `playwright install chromium` to have been run in the
    deployment image. Import is deferred so environments that only need
    the HTTP crawler don't need the Playwright binary installed."""

    async def fetch(self, url: str) -> FetchResult:
        try:
            validate_and_resolve_url(url)
        except SSRFValidationError as e:
            return FetchResult(url=url, status_code=None, html=None, error=f"blocked_url: {e}")

        if not is_allowed(url, settings.crawler_user_agent):
            return FetchResult(url=url, status_code=None, html=None, error="disallowed_by_robots_txt")

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return FetchResult(url=url, status_code=None, html=None,
                                error="playwright_not_installed")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
                )
                # Fresh, isolated, non-persistent context per fetch — no
                # cookies/credentials carried across sites or sessions.
                context = await browser.new_context(
                    user_agent=settings.crawler_user_agent,
                    java_script_enabled=True,
                    ignore_https_errors=False,
                    viewport={"width": 1280, "height": 900},
                )

                # Block obvious internal-network navigation attempts (defence in
                # depth on top of the SSRF check already done above/on redirects).
                async def _block_private(route):
                    req_url = route.request.url
                    if any(frag in req_url for frag in _PRIVATE_HOST_FRAGMENTS):
                        await route.abort()
                    else:
                        await route.continue_()

                await context.route("**/*", _block_private)

                page = await context.new_page()
                page.set_default_timeout(settings.crawler_timeout_seconds * 1000)

                try:
                    resp = await page.goto(url, wait_until="networkidle",
                                            timeout=settings.crawler_timeout_seconds * 1000)
                    html = await page.content()
                    status_code = resp.status if resp else None
                    final_url = page.url
                finally:
                    await context.close()
                    await browser.close()

            if len(html.encode("utf-8")) > settings.crawler_max_response_bytes:
                html = html[: settings.crawler_max_response_bytes]

            return FetchResult(url=final_url, status_code=status_code, html=html)
        except Exception as e:
            return FetchResult(url=url, status_code=None, html=None, error=f"playwright_error: {e}")
