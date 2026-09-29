"""Signup, login, logout, and who-am-I."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from ..config import get_settings
from ..db import get_db
from ..deps import (
    clear_session_cookie,
    get_current_user_optional,
    set_session_cookie,
)
from ..models import Session as UserSession, User
from ..schemas import LoginIn, SignupIn, UserOut
from ..security import hash_password, hash_token, new_session_token, verify_password

router = APIRouter()


def _issue_session(db: DbSession, user: User) -> str:
    token = new_session_token()
    settings = get_settings()
    db.add(
        UserSession(
            token_hash=hash_token(token),
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.session_days),
        )
    )
    db.commit()
    return token


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupIn, response: Response, db: DbSession = Depends(get_db)):
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists",
        )
    db.refresh(user)
    set_session_cookie(response, _issue_session(db, user))
    return UserOut(id=user.id, email=user.email)


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, response: Response, db: DbSession = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(body.password, user.password_hash):
        # Same response either way: no account enumeration.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong email or password",
        )
    set_session_cookie(response, _issue_session(db, user))
    return UserOut(id=user.id, email=user.email)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: DbSession = Depends(get_db)):
    token = request.cookies.get("ww_session")
    if token:
        session = (
            db.query(UserSession).filter(UserSession.token_hash == hash_token(token)).first()
        )
        if session:
            db.delete(session)
            db.commit()
    clear_session_cookie(response)
    return None


@router.get("/me", response_model=UserOut)
def me(user: User | None = Depends(get_current_user_optional)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in")
    return UserOut(id=user.id, email=user.email)
