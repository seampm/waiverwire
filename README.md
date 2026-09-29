# WaiverWire

Fantasy football is won on the waiver wire. WaiverWire finds breakout players before they break out by tracking usage (snap share, targets, touches) instead of last week's points.

The idea is simple: when a player's snaps and targets spike but the touchdowns haven't come yet, he's usually free. By the time he scores, everyone has missed him. This tool flags those players every Tuesday morning.

It will not predict the future. No model does. It just makes you systematic while your league mates go by gut feel and headlines.

## The weekly report

```bash
python -m waiverwire.report
```

```
WAIVER WIRE — pickups ahead of week 4 (2026 season)
Ranked by usage trend, not last week's box score.

PRIORITY PICKUPS — usage spiking, points lagging behind:
  A.Kamara (RB, NO) — score 75: targets 0.0 to 3.5/wk; snaps 0% to 30%; points have not caught up yet
  ...

TRENDING — usage up and already producing (likely rostered, check):
  B.Bowers (TE, LV) — score 99: targets 0.0 to 13.0/wk; snaps 0% to 79%
  ...
```

Each player gets a 0-100 breakout score from rising snap share, targets, and touches, plus a plain-English reason. The priority list is the edge: players whose usage is surging while their fantasy points lag behind.

## Does it work?

Backtested once, honestly: scored at week 4 of the 2025 season using only weeks 1-4, then measured weeks 5-8.

- Priority pickups (usage up, points lagging): **+2.2 PPR/week** vs their weeks 1-4 average
- Baseline (all WR/RB/TE): **+0.6 PPR/week**
- Trending-but-already-scoring players: **-0.8 PPR/week** (regression to the mean, as expected)

One season, one checkpoint — not a guarantee. The pattern makes sense though: players who were already scoring regress, while players earning more snaps and targets tend to convert them into points.

## Data

nflverse retired the old weekly player stats after 2024, so for 2025+ WaiverWire aggregates weekly stats from play-by-play and joins snap shares from snap counts (via the roster ID crosswalk). Everything caches locally as parquet under `data/` (gitignored). No API key needed.

## Yahoo setup (one manual step)

WaiverWire reads your league through the Yahoo Fantasy API, which needs OAuth. This part needs your Yahoo login, so you do it once:

1. Create an app at https://developer.yahoo.com/apps/create/ — give it Fantasy Sports read access and set the redirect URI to https://localhost.
2. Save your credentials to `~/.waiverwire/yahoo.json`:
   `{"consumer_key": "...", "consumer_secret": "..."}`
3. Run `python -m waiverwire.yahoo.auth` — it prints a URL, you authorize, then paste the `code` from the redirected URL back.
4. Run `python -m waiverwire.yahoo.league` to see your leagues.

Tokens stay in `~/.waiverwire/` and are never committed.

Note: Yahoo now requires manual approval for Fantasy Sports API access (apply at https://sports.yahoo.com/developer/access/). Until the app is approved, Yahoo returns 403 on all fantasy endpoints.

## Layout

- `waiverwire/data/weekly.py` — builds weekly player stats from nflverse play-by-play + snap counts
- `waiverwire/metrics/` — usage metrics (target share, rush share, touch trends) and breakout scoring
- `waiverwire/report.py` — the Tuesday-morning waiver report
- `waiverwire/yahoo/` — Yahoo Fantasy API: auth, league discovery

## Roadmap

- Plug in Yahoo roster/availability once the app is approved
- Projection model, backtested against 3+ seasons with honest error bars
- Start/sit with disagreement flags vs expert consensus
- Web dashboard
