"""Yahoo OAuth2 setup for the Fantasy Sports API.

Run: python -m waiverwire.yahoo.auth

Yahoo's OAuth1 endpoints no longer issue tokens for new apps, so this uses
the OAuth2 authorization-code flow:

  1. The WaiverWire app is registered at https://developer.yahoo.com/apps/
     with redirect URI https://localhost and Fantasy Sports read access.
     Its client ID and secret live in ~/.waiverwire/yahoo.json and are
     never committed.
  2. This module prints an authorize URL. Open it while signed in to Yahoo,
     click Agree, and copy the `code` query parameter from the redirected
     URL. (The https://localhost page itself will not load; the code is in
     the address bar.)
  3. The code is exchanged for an access token plus a long-lived refresh
     token, both saved to the same file. API calls use the Bearer token and
     refresh it automatically when it expires (~1 hour).
"""
from __future__ import annotations

import base64
import json
import time
import urllib.parse
from pathlib import Path

import requests

AUTHORIZE_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
REDIRECT_URI = "https://localhost"
SCOPE = "fspt-r"  # fantasy sports, read-only

CREDS_PATH = Path.home() / ".waiverwire" / "yahoo.json"


def _load() -> dict:
    if not CREDS_PATH.exists():
        raise SystemExit(
            f"Missing {CREDS_PATH}\n"
            "Register a Yahoo app, then save "
            '\'{"consumer_key": "...", "consumer_secret": "..."}\' there. See README.'
        )
    return json.loads(CREDS_PATH.read_text())


def _save(data: dict) -> None:
    CREDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CREDS_PATH.write_text(json.dumps(data, indent=2))
    CREDS_PATH.chmod(0o600)


def _basic_auth_header(consumer_key: str, consumer_secret: str) -> dict:
    raw = f"{consumer_key}:{consumer_secret}".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode()}


def authorization_url(consumer_key: str) -> str:
    params = {
        "client_id": consumer_key,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "language": "en-us",
        "scope": SCOPE,
    }
    return AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)


def exchange_code(code: str) -> dict:
    """Trade an authorization code for tokens and persist them."""
    data = _load()
    key, secret = data["consumer_key"], data["consumer_secret"]
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        headers=_basic_auth_header(key, secret),
        timeout=30,
    )
    resp.raise_for_status()
    tok = resp.json()
    data["access_token"] = tok["access_token"]
    data["refresh_token"] = tok["refresh_token"]
    data["expires_at"] = time.time() + tok.get("expires_in", 3600) - 60
    _save(data)
    print(f"Saved Yahoo tokens to {CREDS_PATH}")
    return tok


def _refresh(data: dict) -> dict:
    key, secret = data["consumer_key"], data["consumer_secret"]
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": data["refresh_token"],
        },
        headers=_basic_auth_header(key, secret),
        timeout=30,
    )
    resp.raise_for_status()
    tok = resp.json()
    data["access_token"] = tok["access_token"]
    # Yahoo may or may not rotate the refresh token; keep the old one if absent.
    data["refresh_token"] = tok.get("refresh_token", data["refresh_token"])
    data["expires_at"] = time.time() + tok.get("expires_in", 3600) - 60
    _save(data)
    return data


class YahooSession:
    """requests-style session using a Bearer token with auto-refresh."""

    def __init__(self) -> None:
        self._data = _load()
        if "access_token" not in self._data:
            raise SystemExit(
                "No Yahoo tokens yet. Run `python -m waiverwire.yahoo.auth` first."
            )

    def _token(self) -> str:
        if time.time() >= self._data.get("expires_at", 0):
            self._data = _refresh(self._data)
        return self._data["access_token"]

    def get(self, url: str, params: dict | None = None, timeout: int = 30):
        return requests.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {self._token()}"},
            timeout=timeout,
        )


def authorize_interactive() -> YahooSession:
    """Print the authorize URL, read the code from stdin, exchange it."""
    data = _load()
    print("Open this URL while signed in to Yahoo, click Agree, then copy")
    print("the `code` value from the redirected URL:\n")
    print(authorization_url(data["consumer_key"]) + "\n")
    code = input("Code: ").strip()
    exchange_code(code)
    return YahooSession()


def get_session() -> YahooSession:
    data = _load()
    if "access_token" not in data:
        return authorize_interactive()
    return YahooSession()


def main() -> None:
    sess = get_session()
    resp = sess.get(
        "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1",
        params={"format": "json"},
    )
    resp.raise_for_status()
    print("Authenticated OK.")


if __name__ == "__main__":
    main()
