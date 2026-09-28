# WaiverWire

Fantasy football is won on the waiver wire. WaiverWire finds breakout players before they break out by tracking usage (snap share, target share, routes run) instead of last week's points.

The idea is simple: when a player's routes and targets spike but the touchdowns haven't come yet, he's usually free. By the time he scores, everyone has missed him. This tool flags those players every Tuesday morning.

It will not predict the future. No model does. It just makes you systematic while your league mates go by gut feel and headlines.

## Status

Phase 0: project scaffold. Data ingestion and usage metrics work. Yahoo league integration is wired up but needs your one manual OAuth step below. Breakout detection and the projection model come next.

## Yahoo setup (one manual step)

WaiverWire reads your league through the Yahoo Fantasy API, which needs OAuth. This part needs your Yahoo login, so you do it once:

1. Create an app at https://developer.yahoo.com/apps/create/ — choose "Installed Application" and give it Fantasy Sports read access.
2. Save your credentials to `~/.waiverwire/yahoo.json`:
   `{"consumer_key": "...", "consumer_secret": "..."}`
3. Run `python -m waiverwire.yahoo.auth` — it prints a URL, you authorize, paste the verifier code back.
4. Run `python -m waiverwire.yahoo.league` to see your leagues.

Tokens stay in `~/.waiverwire/` and are never committed.

## Layout

- `waiverwire/data/` — downloads weekly NFL stats from nflverse, caches locally as parquet
- `waiverwire/metrics/` — usage metrics: target share, rush share, touch trends
- `waiverwire/yahoo/` — Yahoo Fantasy API: auth, league discovery

## Roadmap

- Phase 1: breakout detection on usage trends, first weekly waiver report
- Phase 2: projection model, backtested against 3+ seasons with honest error bars
- Phase 3: start/sit with disagreement flags vs expert consensus
- Phase 4: web dashboard
