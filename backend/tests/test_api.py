"""API tests: public data, auth flow, and per-user isolation."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def make_user(client, n=""):
    email = f"user{n}-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/signup", json={"email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    return email


# --- public data ---


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["season"] == 2026
    assert r.json()["week"] == 3


def test_board(client):
    r = client.get("/api/board")
    assert r.status_code == 200
    body = r.json()
    assert len(body["players"]) == 150
    assert body["backtest"] is not None
    assert body["players"][0]["score"] >= body["players"][-1]["score"]


def test_pool(client):
    r = client.get("/api/pool")
    assert r.status_code == 200
    assert len(r.json()["players"]) == 398


def test_search(client):
    r = client.get("/api/players/search", params={"q": "chase"})
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert names, "expected at least one Chase"
    assert all("chase" in n.lower() for n in names)


# --- auth ---


def test_signup_validation(client):
    assert client.post("/api/auth/signup", json={"email": "not-an-email", "password": "password123"}).status_code == 422
    assert client.post("/api/auth/signup", json={"email": "a@b.com", "password": "short"}).status_code == 422


def test_duplicate_email_rejected(client):
    email = f"dup2-{uuid.uuid4().hex[:8]}@example.com"
    assert client.post("/api/auth/signup", json={"email": email, "password": "password123"}).status_code == 201
    r = client.post("/api/auth/signup", json={"email": email, "password": "password123"})
    assert r.status_code == 409


def test_login_logout_flow(client):
    email = make_user(client, "flow")
    # fresh client: not signed in
    anon = TestClient(app)
    assert anon.get("/api/auth/me").status_code == 401

    r = anon.post("/api/auth/login", json={"email": email, "password": "wrongpass1"})
    assert r.status_code == 401

    r = anon.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200
    assert r.json()["email"] == email

    r = anon.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == email

    assert anon.post("/api/auth/logout").status_code == 204
    assert anon.get("/api/auth/me").status_code == 401


# --- matchups ---


def test_matchups_require_auth(client):
    assert client.get("/api/matchups").status_code == 401
    assert client.post("/api/matchups", json={"name": "x", "roster_a": [], "roster_b": []}).status_code == 401


def test_matchup_crud(client):
    make_user(client, "mu")
    r = client.post(
        "/api/matchups",
        json={"name": "Week 4 vs Sam", "roster_a": ["E.Wilson", "S.Moore"], "roster_b": ["J.Chase"]},
    )
    assert r.status_code == 201, r.text
    mid = r.json()["id"]

    r = client.get("/api/matchups")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get(f"/api/matchups/{mid}")
    assert r.status_code == 200
    assert r.json()["roster_a"] == ["E.Wilson", "S.Moore"]

    assert client.delete(f"/api/matchups/{mid}").status_code == 204
    assert client.get(f"/api/matchups/{mid}").status_code == 404


def test_matchup_isolation_between_users():
    from fastapi.testclient import TestClient

    alice = TestClient(app)
    bob = TestClient(app)
    make_user(alice, "alice")
    make_user(bob, "bob")

    r = alice.post(
        "/api/matchups",
        json={"name": "private", "roster_a": ["E.Wilson"], "roster_b": []},
    )
    mid = r.json()["id"]

    assert bob.get("/api/matchups").json() == []
    assert bob.get(f"/api/matchups/{mid}").status_code == 404
    assert bob.delete(f"/api/matchups/{mid}").status_code == 404


# --- watchlist ---


def test_watchlist_flow(client):
    make_user(client, "wl")
    r = client.post("/api/watchlist", json={"player_name": "E.Wilson"})
    assert r.status_code == 201, r.text
    assert r.json()["info"] is not None

    assert client.post("/api/watchlist", json={"player_name": "E.Wilson"}).status_code == 409

    r = client.get("/api/watchlist")
    assert r.status_code == 200
    assert [w["player_name"] for w in r.json()] == ["E.Wilson"]

    assert client.delete("/api/watchlist/E.Wilson").status_code == 204
    assert client.delete("/api/watchlist/E.Wilson").status_code == 404


# --- admin ---


def test_admin_refresh(client):
    assert client.post("/api/admin/refresh").status_code == 403
    r = client.post("/api/admin/refresh", headers={"x-admin-token": "test-admin-token"})
    assert r.status_code == 200
    assert r.json()["players"] == 150
