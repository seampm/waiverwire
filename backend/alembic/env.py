"""Alembic environment: migrations run against the configured database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import context

from app.config import get_settings
from app.db import Base
from app import models  # noqa: F401 -- register tables on Base.metadata

config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = __import__("sqlalchemy").create_engine(get_settings().database_url)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
