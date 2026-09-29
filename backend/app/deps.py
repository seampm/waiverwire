"""Request dependencies: database session and the logged-in user."""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from .config import get_settings
from .db import get_db
from .models import Session as UserSession, User
from .security import hash_token

COOKIE_NAME = "ww_session"


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in")


def get_current_user_optional(
    request: Request, db: DbSession = Depends(get_db)
) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    session = (
        db.query(UserSession).filter(UserSession.token_hash == hash_token(token)).first()
    )
    if session is None:
        return None
    now = datetime.now(timezone.utc)
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        db.delete(session)
        db.commit()
        return None
    return db.get(User, session.user_id)


def get_current_user(
    request: Request, db: DbSession = Depends(get_db)
) -> User:
    user = get_current_user_optional(request, db)
    if user is None:
        raise _unauthorized()
    return user


def set_session_cookie(response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def clear_session_cookie(response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")
