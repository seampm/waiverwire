"""Tiny in-memory rate limiter for the auth endpoints.

Per-process and per-IP; good enough to blunt credential stuffing on a single
instance. Behind multiple instances, put a shared limiter at the edge.
"""
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings

WINDOW_SECONDS = 60


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.limit = settings.auth_rate_limit
        self.window = WINDOW_SECONDS
        self.hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/auth/") and request.method == "POST":
            ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            bucket = self.hits[ip]
            while bucket and bucket[0] <= now - self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return JSONResponse(
                    {"detail": "Too many attempts, try again in a minute."},
                    status_code=429,
                )
            bucket.append(now)
        return await call_next(request)
