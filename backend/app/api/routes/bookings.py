from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.core.supabase import get_supabase
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/bookings", tags=["bookings"])


class BookingCreate(BaseModel):
    website_id: str
    customer_name: str
    customer_phone: str
    service: Optional[str] = ""
    date: Optional[str] = ""
    time: Optional[str] = ""
    notes: Optional[str] = ""


@router.post("/create")
def create_booking(req: BookingCreate):
    """Create a new booking from a website visitor."""
    db = get_supabase()
    service = WebsiteService()

    website = service.get(req.website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead_id = website.get("lead_id")

    booking = {
        "website_id": req.website_id,
        "lead_id": lead_id,
        "customer_name": req.customer_name,
        "customer_phone": req.customer_phone,
        "service": req.service,
        "date": req.date,
        "time": req.time,
        "notes": req.notes,
        "status": "pending",
    }

    try:
        result = db.table("bookings").insert(booking).execute()
        booking_id = result.data[0]["id"] if result.data else None
    except Exception as e:
        raise HTTPException(500, f"Failed to create booking: {str(e)}")

    # Track as analytics event
    try:
        db.table("analytics_events").insert({
            "website_id": req.website_id,
            "event_type": "booking",
            "page": "/booking",
        }).execute()
    except Exception:
        pass

    return {
        "status": "confirmed",
        "booking_id": booking_id,
        "message": "Booking received! We will confirm shortly via WhatsApp/call.",
    }


@router.get("/website/{website_id}")
def list_bookings(website_id: str, status: str = ""):
    """List all bookings for a website (business owner view)."""
    db = get_supabase()
    query = db.table("bookings").select("*").eq("website_id", website_id).order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    result = query.limit(50).execute()
    return result.data or []


@router.patch("/{booking_id}/status")
def update_booking_status(booking_id: str, status: str = "confirmed"):
    """Update booking status (pending/confirmed/cancelled/completed)."""
    db = get_supabase()
    valid = ["pending", "confirmed", "cancelled", "completed"]
    if status not in valid:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid}")

    db.table("bookings").update({"status": status}).eq("id", booking_id).execute()
    return {"booking_id": booking_id, "status": status, "updated": True}


@router.get("/stats/{website_id}")
def booking_stats(website_id: str):
    """Get booking statistics for a website."""
    db = get_supabase()
    all_bookings = db.table("bookings").select("status").eq("website_id", website_id).execute()

    stats = {"total": 0, "pending": 0, "confirmed": 0, "completed": 0, "cancelled": 0}
    for b in (all_bookings.data or []):
        stats["total"] += 1
        s = b.get("status", "pending")
        stats[s] = stats.get(s, 0) + 1

    return stats
