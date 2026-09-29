# WaiverWire

Fantasy football is won on the waiver wire. WaiverWire finds breakout players before they break out by tracking usage (snap share, targets, touches) instead of last week's points.

The idea is simple: when a player's snaps and targets spike but the touchdowns haven't come yet, he's usually free. By the time he scores, everyone has missed him. This tool flags those players every week.

It will not predict the future. No model does. It just makes you systematic while your league mates go by gut feel and headlines.

## The app

WaiverWire is a full-stack web app. Sign up for an account and you get:

- **The waiver board**: 150 players ranked by breakout score, with week-by-week usage charts, advanced metrics (target share, air yards share, WOPR, red-zone usage), and a plain-English reason for every flag.
- **Matchup tool**: line up your roster against your opponent's head to head, with position-by-position edges. Save matchups to your account and reload them later.
- **Watchlist**: save waiver targets to your account so they're waiting next Tuesday.
- **Honest backtest**: the one-season 2025 validation, shown with its limits.

The board works without an account. Saving matchups and watchlists needs one.

## Quickstart

The fastest way to run everything (app + Postgres):

```bash
cp .env.example .env   # then set WW_SECRET_KEY, WW_DB_PASSWORD, WW_ADMIN_TOKEN
docker compose up
```

Open http://localhost:8000. The compose command runs migrations automatically.

Local development without Docker:

```bash
python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt
export WW_DATABASE_URL="sqlite:///./waiverwire.db"
backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
backend/.venv/bin/uvicorn app.main:app --app-dir backend
```

## Architecture

```
browser  ->  FastAPI (backend/app)  ->  Postgres (users, sessions, matchups, watchlist)
                  |
                  v
         nflverse snapshot (dashboard/data.json, rebuilt weekly by dashboard/build_data.py)
```

- **Backend**: FastAPI. Serves the API under `/api/*` and the frontend pages (`/`, `/login`, `/signup`).
- **Auth**: email + password, bcrypt-hashed. Sessions are random tokens stored hashed in the database, sent as `HttpOnly`/`SameSite=Lax` cookies (set `WW_COOKIE_SECURE=true` behind HTTPS). Auth endpoints are rate-limited per IP.
- **Database**: Postgres in production (via docker-compose), SQLite for local dev. Migrations with Alembic (`backend/alembic/versions/`).
- **Data**: the player snapshot is computed from nflverse play-by-play and served read-only. Refresh it by re-running `dashboard/build_data.py`, then `POST /api/admin/refresh` with the admin token.
- **Scaling**: the API is stateless (sessions live in the database), so it scales horizontally behind any load balancer. The snapshot is loaded per instance; a weekly rebuild plus the refresh endpoint keeps instances in sync.

## API

Public:

- `GET /api/health`
- `GET /api/board` — 150 ranked players with weekly series
- `GET /api/pool` — 398-player QB/RB/WR/TE lookup pool for the matchup tool
- `GET /api/players/search?q=...`

Auth (`/api/auth`): `POST /signup`, `POST /login`, `POST /logout`, `GET /me`.

Per-user (requires login): `GET/POST /api/matchups`, `GET /api/matchups/{id}`, `DELETE /api/matchups/{id}`, `GET/POST /api/watchlist`, `DELETE /api/watchlist/{name}`.

Admin: `POST /api/admin/refresh` (header `x-admin-token`).

## Deploying

Any host that runs containers works (Fly.io, Railway, Render, a VPS). You need:

1. Postgres (managed, or the `db` service in `docker-compose.yml`).
2. Environment variables from `.env.example`: `WW_SECRET_KEY`, `WW_DATABASE_URL`, `WW_ADMIN_TOKEN`, and `WW_COOKIE_SECURE=true`.
3. Run migrations on deploy: `alembic -c backend/alembic.ini upgrade head` (docker-compose does this).
4. Rebuild `dashboard/data.json` weekly and hit the admin refresh endpoint, or redeploy.

## The weekly report (CLI)

The original terminal report still works:

```bash
python -m waiverwire.report
```

## Does it work?

Backtested once, honestly: scored at week 4 of the 2025 season using only weeks 1-4, then measured weeks 5-8.

- Priority pickups (usage up, points lagging): **+2.2 PPR/week** vs their weeks 1-4 average
- Baseline (all WR/RB/TE): **+0.6 PPR/week**
- Trending-but-already-scoring players: **-0.8 PPR/week** (regression to the mean, as expected)

One season, one checkpoint, not a guarantee. The pattern makes sense though: players who were already scoring regress, while players earning more snaps and targets tend to convert them into points.

## Data

nflverse retired the old weekly player stats after 2024, so for 2025+ WaiverWire aggregates weekly stats from play-by-play and joins snap shares from snap counts (via the roster ID crosswalk). Everything caches locally as parquet under `data/` (gitignored). No API key needed.

## Yahoo status

Yahoo league sync is deferred. The Fantasy Sports API now requires manual approval (applied at https://sports.yahoo.com/developer/access/) and returns 403 on all fantasy endpoints until granted. The OAuth flow in `waiverwire/yahoo/` works and tokens refresh correctly; the per-user league connection will plug into the accounts system once Yahoo approves the app.

## Layout

- `backend/app/` — FastAPI app: auth, players, matchups, watchlist, admin routes
- `backend/alembic/` — database migrations
- `frontend/` — the web UI (built from `docs/index.html` by `build_frontend.py`)
- `dashboard/build_data.py` — builds the player snapshot from nflverse
- `waiverwire/data/weekly.py` — weekly stats from nflverse play-by-play + snap counts
- `waiverwire/metrics/` — usage metrics and breakout scoring
- `waiverwire/report.py` — the Tuesday-morning terminal report
- `waiverwire/yahoo/` — Yahoo Fantasy API auth and league discovery (waiting on approval)
- `docs/` — the static GitHub Pages demo snapshot

## Roadmap

- Plug in Yahoo roster/availability per user once the app is approved
- Projection model, backtested against 3+ seasons with honest error bars
- Start/sit with disagreement flags vs expert consensus
- Password reset and email verification
