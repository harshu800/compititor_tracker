"""
Clerk authentication + organization authorization.

CRITICAL RULE: the organization_id used for every DB query comes from
this module (derived server-side from the authenticated user's membership),
NEVER from a request body/query param. Route handlers must call
`require_org_member` (or `require_org_role`) and use its returned
organization_id — they must not accept an org id from the client.
"""
import time
from dataclasses import dataclass
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Header, status
from jose import jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User, OrganizationMember

settings = get_settings()

_jwks_cache: Optional[dict] = None
_jwks_fetched_at: float = 0.0
_JWKS_CACHE_TTL_SECONDS = 3600  # Clerk rotates signing keys occasionally; refresh hourly rather than caching forever


def _get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.time()
    if _jwks_cache is None or (now - _jwks_fetched_at) > _JWKS_CACHE_TTL_SECONDS:
        if not settings.clerk_jwks_url:
            raise HTTPException(status_code=500, detail="Auth not configured (CLERK_JWKS_URL missing)")
        resp = httpx.get(settings.clerk_jwks_url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = now
    return _jwks_cache


def _decode_clerk_token(token: str) -> dict:
    global _jwks_cache
    jwks = _get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token header")

    key = next((k for k in jwks.get("keys", []) if k.get("kid") == unverified_header.get("kid")), None)
    if key is None:
        # Key not found — could be a genuinely unknown key, or Clerk rotated
        # signing keys since we last cached the JWKS. Force one refresh and
        # retry before giving up, rather than rejecting valid tokens for up
        # to an hour after a rotation.
        _jwks_cache = None
        jwks = _get_jwks()
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == unverified_header.get("kid")), None)
    if key is None:
        raise HTTPException(status_code=401, detail="Unknown signing key")

    try:
        claims = jwt.decode(
            token, key, algorithms=["RS256"],
            issuer=settings.clerk_issuer or None,
            options={"verify_aud": False},
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed")
    return claims


@dataclass
class AuthContext:
    user: User
    organization_id: str
    role: str


def get_current_user(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()

    if settings.clerk_jwks_url:
        claims = _decode_clerk_token(token)
        clerk_user_id = claims.get("sub")
        email = claims.get("email") or claims.get("email_address", "")
    else:
        # Local/dev/demo fallback ONLY. Hard-blocked in production regardless
        # of any other config — this branch must never be reachable once
        # ENVIRONMENT=production, even if CLERK_JWKS_URL was left unset by
        # mistake. See config.py's startup check in main.py for the other
        # half of this guarantee (fails fast at boot, not just per-request).
        if settings.environment == "production":
            raise HTTPException(
                status_code=500,
                detail="Auth misconfigured: CLERK_JWKS_URL is required in production.",
            )
        clerk_user_id = token
        email = f"{token}@demo.local"

    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")

    user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if user is None:
        user = User(clerk_user_id=clerk_user_id, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def require_org_member(
    x_organization_id: str = Header(..., alias="X-Organization-Id"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Verifies the authenticated user actually belongs to the org they're
    claiming to act in. The client tells us WHICH org (a UUID it already
    knows from listing the user's orgs), but never gets to assert ROLE or
    bypass membership — that's always checked server-side against the DB."""
    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == x_organization_id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return AuthContext(user=user, organization_id=str(membership.organization_id), role=membership.role)


def require_org_role(*allowed_roles: str):
    def _dep(ctx: AuthContext = Depends(require_org_member)) -> AuthContext:
        if ctx.role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Requires role in {allowed_roles}")
        return ctx
    return _dep
