from __future__ import annotations
import secrets
import string
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.core.supabase import get_supabase
from app.core.logging import get_logger

router = APIRouter(tags=["short-links"])
logger = get_logger(__name__)

_ALPHABET = string.ascii_letters + string.digits


def create_short_link(target_url: str) -> str | None:
    """Create a short code for a target URL. Returns the code, or None on failure."""
    db = get_supabase()
    for _ in range(5):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(6))
        try:
            existing = db.table("short_links").select("code").eq("code", code).execute()
            if existing.data:
                continue
            db.table("short_links").insert({"code": code, "target_url": target_url}).execute()
            return code
        except Exception as e:
            logger.warning("create_short_link failed", error=str(e))
            return None
    return None


@router.get("/api/s/{code}")
async def follow_short_link(code: str):
    """Redirect a short code to its target URL."""
    db = get_supabase()
    try:
        result = db.table("short_links").select("target_url, clicks").eq("code", code).limit(1).execute()
    except Exception:
        raise HTTPException(404, "Link not found")
    if not result.data:
        raise HTTPException(404, "Link not found")
    row = result.data[0]
    try:
        db.table("short_links").update({"clicks": (row.get("clicks", 0) or 0) + 1}).eq("code", code).execute()
    except Exception:
        pass
    return RedirectResponse(url=row["target_url"], status_code=302)

# Fixed APK download page (Expo internal-distribution install page) as fallback
_APK_FALLBACK = "https://expo.dev/artifacts/eas/S-D-qEmLMwfNDDnbhRIWOVgaIBFZEViBFHxW5Yrz11k.apk"


@router.get("/api/app/download")
async def download_app():
    """Stable link for the Android app. Redirects to the current APK / install page."""
    from app.core.config import get_settings
    url = (getattr(get_settings(), "app_apk_url", "") or "").strip() or _APK_FALLBACK
    return RedirectResponse(url=url, status_code=302)