"""Test setup: fresh SQLite database migrated with Alembic, generous rate limit."""
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DB = "/tmp/ww_test.db"

os.environ["WW_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["WW_DATA_PATH"] = str(
    BACKEND_DIR.parents[0] / "dashboard" / "data.json"
)
os.environ["WW_AUTH_RATE_LIMIT"] = "1000"
os.environ["WW_ADMIN_TOKEN"] = "test-admin-token"

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

subprocess.run(
    [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
    cwd=BACKEND_DIR,
    check=True,
    capture_output=True,
    env=os.environ,
)
