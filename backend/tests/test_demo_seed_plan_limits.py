"""
Covers a real product decision: demo/seeded data must never count against
an organization's plan limits. Without this, seeding the 8-competitor demo
dataset would immediately push a Free-plan org (5-competitor limit) over
its own stated limit, and block them from adding any real competitor.

Exercised through the actual HTTP API (not just the deps.py functions
directly) since the bug this guards against is specifically about the
end-to-end behavior of POST /api/v1/demo/seed followed by
POST /api/v1/competitors.
"""
import os

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///./test_demo_seed_plan_limits.db")
os.environ["AI_PROVIDER"] = os.environ.get("AI_PROVIDER", "mock")
os.environ["ENVIRONMENT"] = "development"
os.environ["CLERK_JWKS_URL"] = ""

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app import models  # noqa: E402,F401

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def _new_org(name: str):
    headers_base = {"Authorization": f"Bearer trial-user-{name}"}
    r = client.post("/api/v1/organizations", headers=headers_base, json={"name": name})
    assert r.status_code == 201, r.text
    org_id = r.json()["id"]
    return {**headers_base, "X-Organization-Id": org_id}


def test_demo_seed_creates_competitors_marked_is_demo():
    headers = _new_org("demo-flag-org")
    r = client.post("/api/v1/demo/seed", headers=headers)
    assert r.status_code == 200
    assert r.json()["competitors"] == 8

    from app.database import SessionLocal
    from app.models import Competitor
    db = SessionLocal()
    demo_competitors = db.query(Competitor).filter(Competitor.is_demo == True).all()  # noqa: E712
    assert len(demo_competitors) == 8
    for c in demo_competitors:
        assert "(Demo)" in c.name
    db.close()


def test_demo_data_does_not_count_against_free_plan_competitor_limit():
    headers = _new_org("demo-then-real-org")

    seed_resp = client.post("/api/v1/demo/seed", headers=headers)
    assert seed_resp.status_code == 200
    assert seed_resp.json()["competitors"] == 8  # more than the free plan's 5-competitor limit

    # A real competitor must still be addable — demo data must not have
    # consumed the org's real plan quota.
    add_resp = client.post(
        "/api/v1/competitors", headers=headers,
        json={"name": "Real Competitor", "website_url": "https://example.com"},
    )
    assert add_resp.status_code == 201, add_resp.text


def test_free_plan_limit_still_enforced_for_real_competitors():
    """The exemption must be specific to demo data — real usage still hits
    the real limit."""
    headers = _new_org("real-limit-org")
    real_domains = [
        "https://example.com", "https://example.org", "https://example.net",
        "https://iana.org", "https://wikipedia.org",
    ]
    for i, url in enumerate(real_domains):
        r = client.post("/api/v1/competitors", headers=headers, json={"name": f"Real {i}", "website_url": url})
        assert r.status_code == 201, r.text

    over_limit = client.post(
        "/api/v1/competitors", headers=headers,
        json={"name": "One too many", "website_url": "https://mozilla.org"},
    )
    assert over_limit.status_code == 402
    assert "5 competitors" in over_limit.json()["detail"]


def test_demo_seed_is_idempotent_and_stays_flagged():
    headers = _new_org("idempotent-org")
    first = client.post("/api/v1/demo/seed", headers=headers)
    assert first.json()["competitors"] == 8

    second = client.post("/api/v1/demo/seed", headers=headers)
    assert "already seeded" in second.json().get("note", "")
