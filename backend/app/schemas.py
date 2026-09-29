"""Pydantic request/response shapes for the API."""
import re
from datetime import datetime

from pydantic import BaseModel, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v) or len(v) > 320:
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 128:
            raise ValueError("Password must be 8-128 characters")
        return v


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    id: int
    email: str


class MatchupIn(BaseModel):
    name: str
    roster_a: list[str]
    roster_b: list[str]

    @field_validator("name")
    @classmethod
    def name_ok(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 120:
            raise ValueError("Name must be 1-120 characters")
        return v

    @field_validator("roster_a", "roster_b")
    @classmethod
    def roster_ok(cls, v: list[str]) -> list[str]:
        if len(v) > 30:
            raise ValueError("A roster holds at most 30 players")
        cleaned = [p.strip() for p in v if p.strip()]
        if any(len(p) > 80 for p in cleaned):
            raise ValueError("Player names must be under 80 characters")
        return cleaned


class MatchupOut(BaseModel):
    id: int
    name: str
    roster_a: list[str]
    roster_b: list[str]
    created_at: datetime


class WatchlistIn(BaseModel):
    player_name: str

    @field_validator("player_name")
    @classmethod
    def name_ok(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 120:
            raise ValueError("Player name must be 1-120 characters")
        return v


class WatchlistOut(BaseModel):
    player_name: str
    added_at: datetime
    info: dict | None = None
