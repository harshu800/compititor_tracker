from app.services.crawler.normalizer import normalize_text, calculate_hash


def test_normalize_strips_timestamps():
    text = "Updated at 2026-08-12T10:00:00Z with new content"
    normalized = normalize_text(text)
    assert "2026-08-12t10:00:00z" not in normalized


def test_normalize_is_stable_hash_for_same_content():
    t1 = normalize_text("Our pricing page content")
    t2 = normalize_text("Our pricing page content")
    h1 = calculate_hash(t1, {"title": "Pricing"})
    h2 = calculate_hash(t2, {"title": "Pricing"})
    assert h1 == h2


def test_normalize_hash_differs_on_real_change():
    h1 = calculate_hash(normalize_text("pro plan 29 dollars"), {"title": "Pricing"})
    h2 = calculate_hash(normalize_text("pro plan 39 dollars"), {"title": "Pricing"})
    assert h1 != h2


def test_normalize_strips_session_tokens():
    text = "session id a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6 was created for this visit"
    normalized = normalize_text(text)
    assert "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6" not in normalized
