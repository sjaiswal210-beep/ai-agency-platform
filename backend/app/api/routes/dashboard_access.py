from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.core.supabase import get_supabase
from app.core.logging import get_logger

router = APIRouter(prefix="/api/dashboard-access", tags=["dashboard-access"])
logger = get_logger(__name__)


class TrackAccessRequest(BaseModel):
    phone: str
    org_slug: str
    org_id: Optional[str] = None
    org_name: Optional[str] = None
    source: Optional[str] = "web"  # web or app


@router.post("/track")
async def track_access(req: TrackAccessRequest):
    """Record that a phone number opened a business dashboard.

    Stores phone -> website mapping so admin can see which owner
    opened which generated website. Upserts on (phone, org_slug).
    """
    phone = req.phone.strip().replace(" ", "").replace("-", "")
    if len(phone) < 10:
        raise HTTPException(400, "Invalid phone number")

    db = get_supabase()

    # Resolve org_id from slug if not provided
    org_id = req.org_id
    org_name = req.org_name
    if not org_id:
        orgs = db.table("organizations").select("id, name").eq("slug", req.org_slug).execute()
        if orgs.data:
            org_id = orgs.data[0]["id"]
            org_name = orgs.data[0]["name"]

    # Check for existing record (same phone + slug)
    existing = db.table("dashboard_visitors").select("id, visit_count").eq("phone", phone).eq("org_slug", req.org_slug).execute()

    if existing.data:
        # Increment visit count
        row = existing.data[0]
        db.table("dashboard_visitors").update({
            "visit_count": (row.get("visit_count", 1) or 1) + 1,
            "last_source": req.source,
        }).eq("id", row["id"]).execute()
        return {"status": "updated", "returning": True}

    # Insert new record
    db.table("dashboard_visitors").insert({
        "phone": phone,
        "org_slug": req.org_slug,
        "org_id": org_id,
        "org_name": org_name,
        "last_source": req.source,
        "visit_count": 1,
    }).execute()

    # Also stamp owner_phone on the org if missing (so OTP login works)
    if org_id:
        try:
            org = db.table("organizations").select("owner_phone").eq("id", org_id).single().execute()
            if org.data and not org.data.get("owner_phone"):
                db.table("organizations").update({"owner_phone": phone}).eq("id", org_id).execute()
        except Exception:
            pass

    return {"status": "tracked", "returning": False}


@router.get("/list")
async def list_visitors(
    pwd: str = Query(...),
    limit: int = Query(default=100, le=500),
    search: Optional[str] = None,
):
    """Admin: list all dashboard visitors (phone -> website)."""
    if pwd != "kalpdev2024":
        raise HTTPException(403, "Forbidden")

    db = get_supabase()
    query = db.table("dashboard_visitors").select("*").order("created_at", desc=True).limit(limit)
    if search:
        query = query.ilike("phone", f"%{search}%")
    result = query.execute()
    return {"visitors": result.data, "count": len(result.data)}
