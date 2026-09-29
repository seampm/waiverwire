# WaiverWire

Fantasy football is won on the waiver wire. WaiverWire finds breakout players before they break out by tracking usage (snap share, target share, routes run) instead of last week's points.

The idea is simple: when a player's routes and targets spike but the touchdowns haven't come yet, he's usually free. By the time he scores, everyone has missed him. This tool flags those players every Tuesday morning.

It will not predict the future. No model does. It just makes you systematic while your league mates go by gut feel and headlines.

## Status

Working now: data ingestion from nflverse and usage metrics (target share, rush share, touch trends). Yahoo league integration is wired up but needs your one manual OAuth step below. Still to build: breakout detection, the projection model, start/sit flags, and a web dashboard.

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

- `waiverwire/data/` — downloads weekly NFL stats from nflverse, caches locally as parquet
- `waiverwire/metrics/` — usage metrics: target share, rush share, touch trends
- `waiverwire/yahoo/` — Yahoo Fantasy API: auth, league discovery

## Roadmap

- Breakout detection on usage trends, first weekly waiver report
- Projection model, backtested against 3+ seasons with honest error bars
- Start/sit with disagreement flags vs expert consensus
- Web dashboard
