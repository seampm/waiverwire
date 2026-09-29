"""Read-only client for the Yahoo Fantasy Sports API.

Phase 0 scope: authenticate (see auth.py), discover your leagues, and
fetch raw league JSON. Roster and matchup parsing land in Phase 1,
once we've seen the real response shapes.
"""
from __future__ import annotations

from typing import Any

BASE = "https://fantasysports.yahooapis.com/fantasy/v2"


def _get(session, path: str) -> Any:
    resp = session.get(f"{BASE}/{path}", params={"format": "json"})
    resp.raise_for_status()
    return resp.json()


def _walk(obj: Any, key: str):
    """Yield every dict in a nested JSON blob that contains `key`."""
    if isinstance(obj, dict):
        if key in obj:
            yield obj
        for v in obj.values():
            yield from _walk(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v, key)


def discover_leagues(session) -> list[dict]:
    """Return [{'league_key', 'name', 'season'}] for the user's NFL leagues."""
    data = _get(session, "users;use_login=1/games;game_code=nfl/leagues")
    leagues = []
    for node in _walk(data, "league_key"):
        leagues.append(
            {
                "league_key": node.get("league_key"),
                "name": node.get("name"),
                "season": node.get("season"),
            }
        )
    return leagues


def get_league(session, league_key: str) -> Any:
    return _get(session, f"league/{league_key}")


def main() -> None:
    from .auth import get_session

    session = get_session()
    leagues = discover_leagues(session)
    if not leagues:
        print("No NFL leagues found.")
        return
    for lg in leagues:
        print(f"{lg['league_key']}: {lg['name']} ({lg['season']})")


if __name__ == "__main__":
    main()
