"""A user's saved waiver targets."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from ..data import snapshot
from ..db import get_db
from ..deps import get_current_user
from ..models import User, WatchlistItem
from ..schemas import WatchlistIn, WatchlistOut

router = APIRouter()


def _out(item: WatchlistItem) -> WatchlistOut:
    info = snapshot.find_player(item.player_name)
    return WatchlistOut(player_name=item.player_name, added_at=item.created_at, info=info)


@router.get("", response_model=list[WatchlistOut])
def list_watchlist(
    user: User = Depends(get_current_user), db: DbSession = Depends(get_db)
):
    rows = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id)
        .order_by(WatchlistItem.created_at.desc())
        .all()
    )
    return [_out(r) for r in rows]


@router.post("", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def add_watchlist(
    body: WatchlistIn, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)
):
    item = WatchlistItem(user_id=user.id, player_name=body.player_name)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Already on your watchlist")
    db.refresh(item)
    return _out(item)


@router.delete("/{player_name}", status_code=status.HTTP_204_NO_CONTENT)
def remove_watchlist(
    player_name: str, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)
):
    item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == user.id,
            WatchlistItem.player_name == player_name.strip(),
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Not on your watchlist")
    db.delete(item)
    db.commit()
    return None
