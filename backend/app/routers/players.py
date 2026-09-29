"""Public player data: the waiver board, the matchup pool, and search."""
from fastapi import APIRouter, Depends, Query

from ..data import snapshot

router = APIRouter()


@router.get("/board")
def board():
    data = snapshot.get()
    return {
        "season": data["season"],
        "week": data["week"],
        "pickup_week": data["pickup_week"],
        "backtest": data.get("backtest"),
        "players": data["players"],
    }


@router.get("/pool")
def pool():
    return {"players": snapshot.get()["pool"]}


@router.get("/players/search")
def search_players(q: str = Query(min_length=1, max_length=80), limit: int = Query(20, le=50)):
    needle = q.strip().lower()
    matches = [p for p in snapshot.get()["pool"] if needle in p["name"].lower()]
    return matches[:limit]
