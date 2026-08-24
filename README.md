# CompetitorSignal

An AI competitive-intelligence assistant that monitors your competitors' public web pages and turns raw HTML changes into business decisions:

```
Raw website change → Meaningful difference → Business impact → Recommended action
```

It answers: **what did my competitor change, when, why does it matter, and what should I do?**

This is not a generic "screenshot diff" tool. Noise (cookie banners, tracking IDs, timestamps, nav menus) is filtered out before anything reaches you; only changes that clear a meaningful-change threshold get scored, classified, and (if important enough) alerted on.

**This project runs natively — no Docker, no containers, anywhere.** By default it uses SQLite (a single file, nothing to install or run) and Celery's in-process "eager" mode (tasks run inline, so no separate Redis/worker process is required to get real functionality). Postgres and a real Celery worker/beat setup are supported as an optional upgrade for production-scale concurrent write load — see "Optional: switch to Postgres" below — but SQLite is a fully first-class, production-supported path for a single-instance deployment.

---

## What's actually built here

- **Backend**: FastAPI + SQLAlchemy + Alembic, fully org-scoped authorization, SSRF-hardened crawler, normalization/diff/scoring/AI pipeline, Celery task pipeline, Razorpay billing, email alerts, weekly digest, CSV export, demo data seeder.
- **Frontend**: Next.js 16 (App Router, Turbopack) + TypeScript + Tailwind + TanStack Query + Recharts, wired to Clerk auth and the real API — public landing + pricing pages, dashboard, competitor management, change feed, change detail with diff view, alerts, reports, settings with Razorpay checkout.
- **Tests**: 61 backend unit tests, all passing (SSRF, diff engine, normalizer, extractor, impact scoring, pricing extractor, AI schema validation, Clerk/Razorpay webhook verification, billing idempotency, cross-dialect UUID handling). A full pipeline smoke test (HTML → snapshot → diff → AI classification → score → persisted Change → alert → cross-org isolation check) runs end-to-end and passes, exercised through real HTTP requests via FastAPI's `TestClient`, not just direct function calls.
- **Frontend build**: `npm run build` and `tsc --noEmit` both pass cleanly against all 13 routes.
- **Migrations**: `alembic upgrade head` was actually run against a real SQLite file and verified to produce all 10 tables correctly (not just written and assumed to work).

### What I could not personally verify
I don't have a live Postgres, Redis, Clerk project, Razorpay account, or LLM API key reachable in the sandbox that built this — so I could not click through the full running product against real external infrastructure (a real Clerk sign-up, a real Razorpay test payment). Everything above was verified with real test runs against SQLite, not just "looks right." What's left is running it in your environment with your own Clerk/Razorpay accounts, which is the instructions below.

---

## Setup

### Prerequisites
- Python 3.11, 3.12, or 3.13 — Node 20. (Verified: every pinned dependency in `requirements.txt` resolves to a real installable wheel on all three — no compilation required, including on Windows. Tests were actually executed on 3.12; 3.11/3.13 were verified by resolving the full dependency graph against those interpreters' wheel tags, not by running the test suite on them directly.)
- A free [Clerk](https://clerk.com) application — required for real auth (there's a dev-only fallback for quick local exploration without one, see below)
- Nothing else is required to get a fully working backend running. Optional: OpenAI/Anthropic API key (`AI_PROVIDER=mock` works with zero external AI key and gives clearly-labeled, non-hallucinated placeholder explanations), Razorpay keys (for the billing flow), Resend API key (for real email alerts instead of console logging).

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

`backend/.env.example` already defaults to SQLite (`DATABASE_URL=sqlite:///./app.db`), `AI_PROVIDER=mock`, `EMAIL_PROVIDER=console`, and `CELERY_TASK_ALWAYS_EAGER=true` — so the only things you actually need to fill in to get a real, usable app are the Clerk keys:
- `CLERK_SECRET_KEY`, `CLERK_JWKS_URL`, `CLERK_ISSUER` — from your Clerk dashboard (JWKS URL is typically `https://<your-clerk-domain>/.well-known/jwks.json`)
- `CLERK_WEBHOOK_SECRET` — from Clerk dashboard → Webhooks (see "Production readiness" below for the endpoint URL to register)

Edit `frontend/.env`:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — from the same Clerk application
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

### 2. Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head        # creates app.db (SQLite) with all 10 tables
uvicorn app.main:app --reload --port 8000
```

That's it — one process, no Redis, no separate worker. `CELERY_TASK_ALWAYS_EAGER=true` means crawling/classification/alerting run inline when triggered instead of being dispatched to a background worker. Fine for exploring the product and for lower-traffic single-instance production use; see "Optional: turn on real background workers" below for when you'd want to change that.

Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI).

**No Clerk account yet and just want to poke at the API first?** Leave `CLERK_JWKS_URL` empty in `backend/.env` — `security/auth.py` falls back to treating any Bearer token string as a dev user id, so `Authorization: Bearer trial-user-1` just works. **This fallback is automatically and permanently disabled the instant `CLERK_JWKS_URL` is set** (and hard-blocked outright if `ENVIRONMENT=production`) — never rely on it past local exploration.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Try it

1. Visit `http://localhost:3000` — public landing page. Sign up via Clerk.
2. Create a workspace.
3. Go to **Settings → Seed demo data** to instantly populate 8 competitors, ~30 pages, and 100+ realistic changes — no waiting for real crawls, no API keys needed.
4. Or click **Add competitor**, enter a real public website, approve the auto-suggested pricing/features/changelog pages, and monitoring starts (the initial snapshot runs immediately, inline, thanks to eager mode).
5. Try **Settings → Upgrade to Pro** to exercise the Razorpay checkout flow (needs `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET` in `backend/.env` — see "Billing" below).

---

## Optional: switch to Postgres

SQLite is fully supported for production at single-instance scale, but if you're expecting meaningful concurrent write load (many competitors checked at once across a real worker pool) or scaling across multiple machines, switch to Postgres — the code is dialect-portable (see "Design decisions" below), so this is just a config change, not a rewrite.

`psycopg2-binary` (the Postgres driver) is deliberately **not** in the main `requirements.txt` — SQLite users shouldn't need a Postgres C driver installed at all. Install it only when you actually switch:
```bash
pip install -r requirements-postgres.txt
```

macOS (Homebrew):
```bash
brew install postgresql@16
brew services start postgresql@16
createdb competitor_tracker
```

Ubuntu/Debian:
```bash
sudo apt-get install postgresql
sudo systemctl start postgresql
sudo -u postgres createdb competitor_tracker
sudo -u postgres psql -c "CREATE USER ctuser WITH PASSWORD 'ctpassword'; GRANT ALL PRIVILEGES ON DATABASE competitor_tracker TO ctuser;"
```

Or skip installing it locally entirely and use a free-tier managed Postgres (Neon, Supabase) — just paste the connection string in.

Then in `backend/.env`:
```
DATABASE_URL=postgresql://ctuser:ctpassword@localhost:5432/competitor_tracker
```
Re-run `alembic upgrade head` against the new URL, and restart the API.

## Optional: turn on real background workers

By default (`CELERY_TASK_ALWAYS_EAGER=true`), a crawl runs synchronously inside the API request that triggered it — simple, but it means "add competitor" or a scheduled check briefly blocks that request, and there's no automatic periodic re-checking of due pages happening on its own. For that, run Redis + a real worker + scheduler:

```bash
# install/start Redis first — brew install redis / apt-get install redis-server / a managed Upstash instance
```

In `backend/.env`, set `CELERY_TASK_ALWAYS_EAGER=false` and point `REDIS_URL`/`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` at your Redis instance. Then run two more processes alongside the API:

```bash
# Terminal 2 — picks up crawl/classify/alert jobs
cd backend && source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

```bash
# Terminal 3 — schedules due-page checks + weekly digest on their own cadence
cd backend && source venv/bin/activate
celery -A app.workers.celery_app beat --loglevel=info
```

If you want the worker to render JS-heavy pages via the browser crawler, install Playwright's browser once: `playwright install chromium`.

## Free deployment path (no Redis, no worker/beat process, $0/month)

As of 2026, none of Railway/Render/Fly.io offer a genuinely free tier that includes an always-on background worker process — Fly.io now requires a card for any usage, and Render/Railway both charge separately for background workers even on otherwise-free plans. If you want to deploy this for actually $0/month rather than pay for that, here's the supported path:

- **Frontend:** Vercel (free)
- **API:** Render free web service (free, but spins down after 15 min of inactivity — the next request has a few extra seconds of cold-start latency; no other functional impact)
- **Database:** Neon (permanent free Postgres tier, no card required)
- **Redis / worker / beat:** skip entirely — stay on `CELERY_TASK_ALWAYS_EAGER=true`

The one thing this breaks on its own: `celery beat` normally re-checks due pages every 15 minutes and sends the weekly digest automatically, and eager mode has no beat process at all. `.github/workflows/scheduled-checks.yml` fixes this for free — a GitHub Actions scheduled workflow calls `POST /api/v1/internal/trigger-due-checks` every 15 minutes and `POST /api/v1/internal/trigger-weekly-digest` on Mondays, standing in for beat at zero cost. Both endpoints are protected by `CRON_TRIGGER_SECRET` (a shared secret, not part of the normal Clerk/org auth model, since these operate across every organization the same way beat itself does) and fail closed — they refuse every request with a 401 if the secret isn't set at all.

**Setup:**
1. Generate a secret: `python3 -c "import secrets; print(secrets.token_hex(32))"`
2. Set `CRON_TRIGGER_SECRET=<that value>` in your deployed backend's environment variables
3. In your GitHub repo: Settings → Secrets and variables → Actions → add two repository secrets:
   - `API_BASE_URL` — your deployed API's base URL (e.g. `https://your-api.onrender.com`)
   - `CRON_TRIGGER_SECRET` — the same value from step 1
4. Push this repo to GitHub — the workflow runs automatically on its schedule from that point on. You can also trigger either job manually from the repo's Actions tab (`workflow_dispatch`) to verify it's wired up correctly before waiting for the schedule.

If you later add a real worker/beat setup (previous section), delete or disable this workflow — running both would trigger every check twice.

---

## Architecture

**A note on the Next.js version:** this project runs on Next.js 16, not 15. If you're setting this up and see a "middleware is deprecated, use proxy" warning from an older copy of this repo, or your `npm install` unexpectedly resolves Next 16 despite a `^15.0.0`-style pin elsewhere, that's what's going on — Next 16 removed the `middleware.ts` convention (replaced by `proxy.ts`, same `clerkMiddleware` API, just a file rename) and removed the `next lint` CLI command entirely (ESLint now runs directly via `eslint .`, using a flat `eslint.config.mjs` instead of the old `.eslintrc.json`, since `eslint-config-next@16` requires ESLint 9+). All of this was verified for real: a fresh `npm install`, `npm run lint`, `npx tsc --noEmit`, `npm run build`, and an actual `next dev` server hit with `curl` (confirming `/` and `/pricing` serve `200` while `/dashboard` correctly redirects `307` when signed out) all pass cleanly on Next 16.3.1.

```
frontend/          Next.js app (Clerk auth, TanStack Query, Recharts)
backend/
  app/
    models/         SQLAlchemy models (10 tables). Uses a custom GUID type
                     (column_types.py) and portable JSON columns — real
                     UUID/JSONB on Postgres, CHAR/JSON on SQLite — so the
                     exact same code runs correctly against either.
    schemas/        Pydantic request/response schemas
    api/            FastAPI routes (thin — logic lives in services/)
    services/
      crawler/       fetch, extract, normalize, robots.txt, SSRF-safe HTTP + browser crawlers, URL discovery
      diff/           word-level + structured diff, meaningful-change gate
      scoring/        deterministic 0–100 impact score (backend-owned, not LLM-owned)
      ai/             provider abstraction (OpenAI/Anthropic/Mock) + strict Pydantic-validated classifier
      pricing/        specialized price-pairing diff
      billing/        Razorpay order creation, payment verification, webhook handling
      alerts/         email abstraction (Resend/console) + alert decision logic
      reports/        weekly digest builder
      monitoring/      the full check_page() pipeline that ties it all together
    workers/         Celery tasks + beat schedule (jittered due-page checks, retries, digest;
                     defaults to task_always_eager so no Redis is required out of the box)
    security/        SSRF validator, Clerk JWT verification + org authorization
  alembic/          migrations — 0001 creates the core 9 tables, 0002 adds subscriptions.
                     Both were run for real against SQLite and produce all 10 tables correctly;
                     they also target Postgres cleanly via the same portable column types.
  scripts/          create_sqlite_db.py — quick DB bootstrap that bypasses Alembic entirely
                     (useful for throwaway/test databases; real setups should use `alembic upgrade head`)
  demo/             realistic demo data seeder (works with zero API keys)
  tests/            pytest suite
```

### Design decisions worth knowing about

- **The backend owns the impact score, not the LLM.** `services/scoring/impact_scoring.py` computes a deterministic 0–100 score from `change_type` base points + diff magnitude + page-type weight. The AI only supplies the human-readable explanation and its own advisory `importance` label (kept for QA comparison, never used for sorting/alerting).
- **False positives are filtered before anything else runs.** `services/diff/change_detector.py` requires both a minimum change-score threshold *and* a minimum changed-word count (or a structured field actually changing) before a change is even considered "meaningful." Nothing downstream — AI classification, scoring, alerting — runs on noise.
- **AI output is never trusted raw.** `services/ai/classifier.py` validates every LLM response against a strict Pydantic schema (`services/ai/schemas.py`); invalid/malformed output falls back to a clearly-labeled generic message rather than guessing.
- **SSRF protection is defense-in-depth**, not a single check: scheme allowlist, hostname blocklist, DNS resolution + per-IP validation (blocks the DNS-rebinding case), and re-validation of the *final* URL after every redirect.
- **Organization ID is never trusted from the client.** `security/auth.py`'s `require_org_member` looks up the caller's actual membership row in the DB; the `X-Organization-Id` header only tells the server *which* of the user's own orgs they're viewing, and every route depends on the resulting server-verified id.
- **Cross-dialect UUID handling.** Every id column uses a custom `GUID` type (`app/models/column_types.py`) instead of Postgres's native `UUID` type directly. This exists because of a real bug found while testing: the `X-Organization-Id` header and Celery task arguments both carry ids as plain strings, and SQLAlchemy's UUID handling only auto-coerces strings on Postgres — SQLite raised `AttributeError: 'str' object has no attribute 'hex'` on essentially every authenticated request beyond creating an org. `GUID` normalizes both `uuid.UUID` and `str` input on every dialect, so the identical code path works against SQLite and Postgres. Caught by exercising the real API through `TestClient` end-to-end, fixed, and covered by `tests/test_column_types.py`.

---

## Production readiness

- **Fail-fast startup validation.** With `ENVIRONMENT=production`, the API refuses to start unless Clerk keys, the webhook secret, Razorpay keys, a real `FRONTEND_ORIGIN`, and real `ENCRYPTION_KEY`/`APP_SECRET` values are all set, and `CELERY_TASK_ALWAYS_EAGER` is off — see `app/main.py::_validate_production_config()`. This was verified directly: a deliberately-unsafe production config raises a clear `RuntimeError` listing every problem before the app object is even created; a properly-configured one starts cleanly. (Using SQLite in production is a warning, logged at startup, not a hard failure — see "Optional: switch to Postgres" above for when that matters.)
- **The dev auth fallback is hard-blocked in production**, not just discouraged — `security/auth.py` raises a 500 if `ENVIRONMENT=production` and `CLERK_JWKS_URL` is somehow unset, on top of the startup check above (defense in depth, not a single point of failure).
- **Clerk webhook sync** (`POST /api/v1/webhooks/clerk`, `app/api/webhooks.py`) keeps `users` rows in sync with Clerk as the source of truth — `user.created`/`user.updated` upsert email and name, `user.deleted` scrubs the row. Every request is signature-verified with Svix using `CLERK_WEBHOOK_SECRET`; unverified requests are rejected before any DB write.
- **Security headers** (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Strict-Transport-Security` in production) are set on every response.
- **JWKS caching now expires and self-heals** — cached for an hour, and a single unknown `kid` triggers one forced refresh before rejecting the token, so a Clerk key rotation doesn't lock out real users for up to an hour.

### Wiring up the Clerk webhook
In your Clerk dashboard: **Webhooks → Add endpoint** → `https://your-api-domain.com/api/v1/webhooks/clerk`, subscribe to `user.created`, `user.updated`, `user.deleted`, then copy the **Signing Secret** into `CLERK_WEBHOOK_SECRET`.

---

## Marketing site

`/` is a public landing page (hero, worked example, how-it-works, pricing teaser) and `/pricing` is a public pricing page with three tiers matching the backend's actual enforced plan limits (`app/api/deps.py::PLAN_LIMITS` — Free: 5 competitors/20 pages, Pro: 50/500, Business: unlimited). Both are excluded from Clerk's route protection in `proxy.ts`; every other route still requires sign-in. A signed-in visitor who lands on `/` is redirected straight to `/dashboard` (`app/page.tsx`) rather than seeing the marketing page again.

The Pro tier's CTA is auth-aware (`components/PricingCards.tsx`): signed-out visitors go to `/sign-up`, signed-in users go straight to `/settings` where the real Razorpay checkout lives. Business stays a `mailto:` link — it's contact-sales only, not self-serve, matching the backend's `SUPPORTED_UPGRADE_PLANS`.

## SEO landing pages

10 additional public pages target specific competitor-monitoring search terms, plus 3 "alternatives" comparison pages:

- `/competitor-monitoring-software`, `/competitor-intelligence-software`, `/competitor-price-tracking`, `/competitor-feature-tracking`, `/saas-competitor-monitoring`, `/ai-competitor-monitoring`, `/competitor-change-tracker`
- `/visualping-alternatives`, `/competely-alternatives`, `/klue-alternatives`

Content for all 10 lives in `lib/seoContent.ts` and is rendered by a shared `components/SeoLandingPage.tsx` template — but each page has genuinely distinct copy (its own H1, intro, feature highlights, and FAQs), not a keyword swapped into identical boilerplate. Search engines treat near-duplicate pages as thin content and won't rank them well, so this was deliberate, not a shortcut. Each page also emits its own `<title>`/meta description/canonical URL and a `SoftwareApplication` JSON-LD block.

The "alternatives" pages name real competing products (standard, legal comparative marketing — nominative fair use) but make no factual claims *about* those products' current features, pricing, or limitations, since that can't be verified from here — copy is framed entirely around what CompetitorSignal does.

`/sitemap.xml` and `/robots.txt` are generated from `app/sitemap.ts` / `app/robots.ts`, which pull their list of pages directly from `lib/seoContent.ts` — a new SEO page added there is automatically included in both, and automatically added to `proxy.ts`'s public-route list (see the next paragraph for why that matters).

**A real bug worth knowing about, in case you add more SEO pages later:** the first version of these pages all 307-redirected to sign-in instead of being visible — I'd created the pages but forgot to also add their slugs to `proxy.ts`'s public-route matcher, so Clerk's auth gate caught them like any other protected route. Caught it by actually curling each page (not just checking `next build` succeeded, which doesn't catch this class of bug), and fixed it properly: `proxy.ts` now derives its public-route list from the same `seoContent.ts` export that `sitemap.ts` uses, so a new page added to that one file is automatically public everywhere it needs to be — this specific bug can't reoccur silently. Verified afterward with a live `next dev` + `curl` pass confirming all 10 pages return `200` with the correct unique title/meta description/H1, while `/dashboard` still correctly returns `307` when signed out.

The extra keyword variants (`competitor tracking software`, `competitor analysis tool`, `competitor website monitoring`, `competitor pricing monitoring`) are woven into these pages' copy and metadata rather than getting their own separate near-duplicate URLs — see `lib/seo.ts`'s `TARGET_KEYWORDS`.

---

## Billing (Razorpay)

Self-serve upgrade to Pro is wired end-to-end with real Razorpay Checkout — not a placeholder button. Business stays contact-sales-only by design (no self-serve checkout for it).

**Flow:** Settings → "Upgrade to Pro" → backend creates a Razorpay order (`POST /api/v1/billing/create-order`, amount always read from server-side config, never from the client) → Razorpay's hosted Checkout modal opens client-side → on success, the frontend calls `POST /api/v1/billing/verify` to confirm the payment signature and upgrade the org immediately (snappy UX) → Razorpay also calls `POST /api/v1/webhooks/razorpay` server-to-server on `payment.captured`, which is the actual authoritative confirmation, independent of whether the browser tab is even still open. Both paths write to the same `Subscription` audit-trail table and are idempotent — a webhook retry or a page refresh mid-checkout can't double-upgrade or double-charge.

**Free tier**, including moving back to it, is explicit rather than implicit: every new organization starts on `plan="free"` (`app/api/organizations.py`), and `POST /api/v1/billing/downgrade` lets an owner/admin return to Free at any time — no Razorpay order involved, since there's nothing to charge or refund, so it takes effect immediately. It does not touch existing competitors, pages, or change history; it only means new additions are capped at Free's limits going forward. The "Downgrade to Free" button appears in Settings whenever the org isn't already on Free.

**Setup:**
1. Create a Razorpay account (test mode is fine to start), grab the Key ID/Secret from **Settings → API Keys**, and put them in `backend/.env`: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`.
2. Confirm your price in `backend/.env`: `PRO_PLAN_AMOUNT=2900` (smallest currency unit — 2900 = $29.00) and `PRO_PLAN_CURRENCY=USD`. Note: standard Razorpay accounts settle in INR — charging in USD requires Razorpay's international/multi-currency payments feature enabled on your account first ([docs](https://razorpay.com/docs/payments/payments/international-payments/)); if you haven't enabled that, switch `PRO_PLAN_CURRENCY` to `INR` and set `PRO_PLAN_AMOUNT` in paise instead.
3. In the Razorpay dashboard: **Webhooks → Add new webhook** → `https://your-api-domain.com/api/v1/webhooks/razorpay`, subscribe to `payment.captured`, copy the **Webhook Secret** into `RAZORPAY_WEBHOOK_SECRET`.
4. Test with [Razorpay's test card numbers](https://razorpay.com/docs/payments/payments/test-card-upi-details/) in test mode before going live.

This was verified with real tests, not just written: `tests/test_billing.py` covers order creation refusing to charge an amount the client supplies, a rejected/invalid signature correctly leaving the org un-upgraded, webhook signature verification against a real HMAC, idempotency (replaying the same `payment.captured` webhook twice only upgrades once), and the downgrade path (rejects downgrading when already on Free, leaves `Subscription` rows untouched, works against an actual HTTP request end-to-end).

---

## Running tests

```bash
cd backend
source venv/bin/activate
export DATABASE_URL="sqlite:///./test.db"
export AI_PROVIDER="mock"
pytest tests/ -v
```

All 61 tests should pass. They cover:
- SSRF protection (localhost, private IPs, cloud metadata endpoint, disallowed schemes, credentials-in-URL, DNS-literal public IPs)
- Diff engine (added/removed/modified text, noise filtering, real pricing-change detection)
- Content normalizer (timestamp/session-token stripping, hash stability)
- Extractor (script/cookie-banner removal, price/CTA/title extraction)
- Impact scoring (band boundaries, page-weight effects, 100-point ceiling)
- Pricing diff pairing
- AI classification schema validation (valid input, invalid change_type, missing fields, out-of-range confidence, empty strings)
- Clerk webhook signature verification (missing/invalid/unconfigured)
- Razorpay billing (server-owned pricing, signature verification, idempotency, downgrade-to-free)
- Cross-dialect UUID handling (the GUID type, directly)

Frontend:
```bash
cd frontend
npm run typecheck   # tsc --noEmit
npm run lint
npm run build        # full production build
```

---

## API overview

All routes are under `/api/v1`. Every route except `POST /organizations` and `GET /organizations` requires:
- `Authorization: Bearer <Clerk session token>` (or a dev token string in local exploration mode — see Setup)
- `X-Organization-Id: <uuid>` (which of the caller's own orgs they're acting as — membership is re-verified server-side)

| Route | Purpose |
|---|---|
| `GET/POST /organizations` | List/create workspaces |
| `GET/POST/PATCH/DELETE /competitors` | Manage competitors |
| `GET/POST /competitors/{id}/pages`, `PATCH/DELETE /pages/{id}` | Manage monitored pages |
| `POST /pages/discover` | Suggest pricing/features/changelog/blog URLs from a homepage (single-page inspection only) |
| `GET /changes`, `GET /changes/{id}`, `PATCH /changes/{id}/review` | Change feed, detail, review-status workflow |
| `GET /changes/export/csv` | CSV export |
| `GET /dashboard` | Overview stats + recent important changes |
| `GET /alerts` | Alert history |
| `GET /reports` | Aggregate stats for charts |
| `GET/PATCH /settings/notifications` | Per-severity email toggle + weekly digest toggle |
| `GET /billing/plan`, `POST /billing/create-order`, `POST /billing/verify`, `POST /billing/downgrade` | Razorpay checkout + plan management |
| `POST /webhooks/clerk`, `POST /webhooks/razorpay` | Signature-verified server-to-server webhooks |
| `POST /internal/trigger-due-checks`, `POST /internal/trigger-weekly-digest` | Shared-secret-protected cron triggers — stand in for `celery beat` when running eager-only (see "Free deployment path") |
| `POST /demo/seed` | Seed demo data for the current org |

Interactive API docs are available at `http://localhost:8000/docs` once the API is running.

---

## Deployment

Two paths — both deploy the exact same code, no rewrite between them.

### Path A: free-tier hosting (recommended to start)

Uses SQLite and the built-in GitHub Actions cron trigger instead of a paid always-on worker process — genuinely free-tier-compatible on Render/Railway, not just "cheap."

1. **Backend** → Render/Railway free tier. Root directory `backend/`. Build: `pip install -r requirements.txt`. Start: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Attach a **persistent disk** for `app.db` — without one, SQLite gets wiped on every redeploy.
2. **Frontend** → Vercel, root directory `frontend/`.
3. **The scheduler**: `.github/workflows/scheduled-checks.yml` is already in this repo — it stands in for `celery beat` by calling `POST /api/v1/internal/trigger-due-checks` (every 15 min) and `/trigger-weekly-digest` (Mondays) on a GitHub Actions cron, authenticated by a shared secret (`CRON_TRIGGER_SECRET`, compared with `hmac.compare_digest` — see `app/api/internal.py`). Set two repo secrets — `API_BASE_URL` (your deployed backend URL) and `CRON_TRIGGER_SECRET` (same value as the backend's env var, generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`) — and it starts running automatically. No server of your own required for scheduling.
4. Set `ENVIRONMENT=production` on the backend. The startup check (`app/main.py::_validate_production_config()`) will refuse to boot with `CELERY_TASK_ALWAYS_EAGER=true` unless `CRON_TRIGGER_SECRET` is also set — that combination is exactly this deployment path, and is accepted with a warning (not an error) once both are configured. Verified directly: both the correct-rejection case (eager mode, no cron secret — genuinely nothing would ever check due pages) and the correct-acceptance case (eager mode + cron secret set) were tested, plus `tests/test_production_config.py` covers this permanently.
5. Point Clerk's and Razorpay's webhook URLs at your real deployed backend domain (`/api/v1/webhooks/clerk`, `/api/v1/webhooks/razorpay`), and set `FRONTEND_ORIGIN` on the backend to your real Vercel URL.

**Tradeoff to know about:** with eager mode on, adding a new competitor's initial page snapshot happens inline within that API request — so "add competitor" takes as long as the first crawl does, instead of returning instantly and crawling in the background. Fine for a solo founder's own usage; worth knowing if that request latency becomes user-visible at higher traffic.

### Path B: real background workers (once you outgrow free tier)

Same deploy, plus:
- Managed Postgres (Railway/Render/Neon), switch `DATABASE_URL`, and change the build command to `pip install -r requirements.txt -r requirements-postgres.txt` (the Postgres driver is deliberately excluded from the base `requirements.txt` — see "Optional: switch to Postgres" above).
- Managed Redis, set `REDIS_URL`/`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`, and set `CELERY_TASK_ALWAYS_EAGER=false`.
- Two more long-running processes from the same codebase: `celery -A app.workers.celery_app worker --loglevel=info` and `celery -A app.workers.celery_app beat --loglevel=info` (run `playwright install --with-deps chromium` in the worker's build step if you want JS-page rendering).
- **Disable or delete `.github/workflows/scheduled-checks.yml`** — running both a real `celery beat` and the cron trigger would check every due page twice.

---

## What's intentionally out of scope (per spec)

Social media / ad library / mobile app / dark web / employee monitoring, login-gated scraping, CAPTCHA bypass, aggressive crawling, search-engine scraping, and automated competitor outreach are not implemented. Plan limits (`FREE_MAX_COMPETITORS` etc.) are config-driven (`app/api/deps.py`), not hardcoded per-route.

## Security notes

- SSRF protection blocks localhost, RFC1918 private ranges, link-local (including the `169.254.169.254` cloud metadata address), and re-validates the final URL after every redirect — see `app/security/ssrf.py` and its test coverage.
- CORS is locked to a single configured frontend origin, not `*`.
- Basic per-IP rate limiting is in `app/main.py`; a real deployment should also rate-limit at the edge/gateway.
- Playwright browser contexts are created fresh per fetch (no persisted cookies/credentials across sites), block obvious private-network navigation, and are never used to authenticate into a competitor's site.
- The dev-auth fallback in `security/auth.py` (accepting any Bearer token as a user id) is automatically disabled the instant `CLERK_JWKS_URL` is set, and hard-blocked outright when `ENVIRONMENT=production` — do not rely on it past local exploration.
- Every Clerk and Razorpay webhook is signature-verified before any DB write — see `app/api/webhooks.py`.
