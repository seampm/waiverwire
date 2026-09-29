"""Saved team-vs-team comparisons, one user's own."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from ..db import get_db
from ..deps import get_current_user
from ..models import Matchup, User
from ..schemas import MatchupIn, MatchupOut

router = APIRouter()


def _out(m: Matchup) -> MatchupOut:
    return MatchupOut(
        id=m.id,
        name=m.name,
        roster_a=m.roster_a,
        roster_b=m.roster_b,
        created_at=m.created_at,
    )


@router.get("", response_model=list[MatchupOut])
def list_matchups(
    user: User = Depends(get_current_user), db: DbSession = Depends(get_db)
):
    rows = (
        db.query(Matchup)
        .filter(Matchup.user_id == user.id)
        .order_by(Matchup.updated_at.desc())
        .all()
    )
    return [_out(m) for m in rows]


@router.post("", response_model=MatchupOut, status_code=status.HTTP_201_CREATED)
def create_matchup(
    body: MatchupIn, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)
):
    m = Matchup(user_id=user.id, name=body.name, roster_a=body.roster_a, roster_b=body.roster_b)
    db.add(m)
    db.commit()
    db.refresh(m)
    return _out(m)


@router.get("/{matchup_id}", response_model=MatchupOut)
def get_matchup(
    matchup_id: int, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)
):
    m = (
        db.query(Matchup)
        .filter(Matchup.id == matchup_id, Matchup.user_id == user.id)
        .first()
    )
    if m is None:
        raise HTTPException(status_code=404, detail="Matchup not found")
    return _out(m)


@router.delete("/{matchup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matchup(
    matchup_id: int, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)
):
    m = (
        db.query(Matchup)
        .filter(Matchup.id == matchup_id, Matchup.user_id == user.id)
        .first()
    )
    if m is None:
        raise HTTPException(status_code=404, detail="Matchup not found")
    db.delete(m)
    db.commit()
    return None
