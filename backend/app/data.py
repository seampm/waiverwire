"""Loads the computed nflverse snapshot built by dashboard/build_data.py.

The snapshot is read-only and reloaded when the file changes, so a weekly
data refresh only needs the pipeline re-run plus a touch of the file (or the
admin refresh endpoint).
"""
import json
from pathlib import Path

from .config import get_settings


class Snapshot:
    def __init__(self, path: str):
        self.path = Path(path)
        self._data = None
        self._mtime = None

    def _load(self):
        with open(self.path) as f:
            self._data = json.load(f)
        self._mtime = self.path.stat().st_mtime

    def get(self) -> dict:
        if self._data is None or self.path.stat().st_mtime != self._mtime:
            self._load()
        return self._data

    def refresh(self) -> dict:
        self._load()
        return self._data

    def find_player(self, name: str) -> dict | None:
        """Board entry first, then the wider matchup pool."""
        data = self.get()
        lname = name.strip().lower()
        for p in data["players"]:
            if p["name"].lower() == lname:
                return {"source": "board", **p}
        for p in data["pool"]:
            if p["name"].lower() == lname:
                return {"source": "pool", **p}
        return None


snapshot = Snapshot(get_settings().data_path)
