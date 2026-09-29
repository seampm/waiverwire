"""Application configuration. Everything secret comes from the environment."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WW_", extra="ignore")

    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite:///./waiverwire.db"
    # Snapshot produced by dashboard/build_data.py (season players + matchup pool).
    data_path: str = str(REPO_ROOT / "dashboard" / "data.json")
    admin_token: str = "dev-admin-token"
    cookie_secure: bool = False
    session_days: int = 30
    # Auth POSTs allowed per IP per minute. Raise in tests via WW_AUTH_RATE_LIMIT.
    auth_rate_limit: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
