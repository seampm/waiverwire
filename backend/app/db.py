"""Database engine and session handling."""
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    settings = get_settings()
    kwargs = {}
    if settings.database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
        kwargs["pool_pre_ping"] = True
    return create_engine(settings.database_url, **kwargs)


@lru_cache
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db():
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
