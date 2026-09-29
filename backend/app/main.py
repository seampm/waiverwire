"""WaiverWire: full-stack fantasy waiver edge tool."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from .config import get_settings
from .data import snapshot
from .ratelimit import AuthRateLimitMiddleware
from .routers import admin, auth, matchups, players, watchlist

app = FastAPI(title="WaiverWire", version="1.0.0")
app.add_middleware(AuthRateLimitMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(players.router, prefix="/api", tags=["players"])
app.include_router(matchups.router, prefix="/api/matchups", tags=["matchups"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@app.get("/api/health")
def health():
    data = snapshot.get()
    return {"ok": True, "season": data["season"], "week": data["week"]}


def _page(name: str) -> FileResponse:
    return FileResponse(FRONTEND_DIR / name)


@app.get("/")
def index():
    return _page("index.html")


@app.get("/login")
def login_page():
    return _page("login.html")


@app.get("/signup")
def signup_page():
    return _page("signup.html")
