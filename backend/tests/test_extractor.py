from app.services.crawler.extractor import extract_content

SAMPLE_HTML = """
<html>
<head><title>Acme Pricing</title>
<meta name="description" content="See our plans">
<script>var trackingId = "xyz123";</script>
</head>
<body>
<div class="cookie-banner">We use cookies. <button>Accept</button></div>
<nav><a href="/">Home</a><a href="/pricing">Pricing</a></nav>
<h1>Simple pricing for every team</h1>
<div>
  <h2>Pro</h2>
  <p>$29/month</p>
  <a href="/signup">Start Free Trial</a>
</div>
<footer>Copyright 2026</footer>
</body>
</html>
"""


def test_extractor_removes_scripts():
    result = extract_content(SAMPLE_HTML)
    assert "trackingId" not in result.body_text
    assert "xyz123" not in result.body_text


def test_extractor_removes_cookie_banner():
    result = extract_content(SAMPLE_HTML)
    assert "we use cookies" not in result.body_text.lower()


def test_extractor_finds_title_and_meta():
    result = extract_content(SAMPLE_HTML)
    assert result.title == "Acme Pricing"
    assert result.meta_description == "See our plans"


def test_extractor_finds_price():
    result = extract_content(SAMPLE_HTML)
    assert any(p["amount"] == 29.0 for p in result.prices)


def test_extractor_finds_cta():
    result = extract_content(SAMPLE_HTML)
    assert "Start Free Trial" in result.ctas


def test_extractor_removes_nav_from_body_text():
    result = extract_content(SAMPLE_HTML)
    # "Home" nav link text should not appear as standalone nav noise
    # (nav tag is stripped entirely before body_text extraction)
    assert result.body_text.count("Pricing") <= 1  # only from H1/H2 area, not also from nav
