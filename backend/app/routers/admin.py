"""Operational endpoints guarded by the admin token."""
from fastapi import APIRouter, Header, HTTPException

from ..config import get_settings
from ..data import snapshot

router = APIRouter()


@router.post("/refresh")
def refresh(x_admin_token: str = Header(default="")):
    if x_admin_token != get_settings().admin_token:
        raise HTTPException(status_code=403, detail="Forbidden")
    data = snapshot.refresh()
    return {"ok": True, "players": len(data["players"]), "pool": len(data["pool"])}
