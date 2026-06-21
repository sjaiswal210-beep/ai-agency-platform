from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date

router = APIRouter(prefix="/api/org/{org_id}/events", tags=["events"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "events").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "Events module not enabled")

@router.get("/venues")
async def list_venues(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    return {"venues": db.table("venues").select("*").eq("organization_id", org_id).execute().data}

@router.post("/venues")
async def create_venue(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("venues").insert({"organization_id": org_id, "name": data["name"], "capacity": data.get("capacity", 100), "type": data.get("type", "hall"), "amenities": data.get("amenities", []), "price_per_day": data.get("price_per_day")}).execute()
    return {"venue": result.data[0], "message": "Venue created"}

@router.get("/bookings")
async def list_bookings(org_id: str, status: Optional[str] = None, month: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("event_bookings").select("*, venues(name)").eq("organization_id", org_id)
    if status: query = query.eq("status", status)
    if month: query = query.gte("event_date", f"{month}-01").lte("event_date", f"{month}-31")
    return {"bookings": query.order("event_date").execute().data}

@router.post("/bookings")
async def create_booking(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    total = float(data.get("total_amount", 0))
    advance = float(data.get("advance_paid", 0))
    result = db.table("event_bookings").insert({
        "organization_id": org_id, "venue_id": data.get("venue_id"),
        "client_name": data["client_name"], "client_phone": data.get("client_phone"),
        "event_type": data.get("event_type", "wedding"), "event_date": data["event_date"],
        "slot": data.get("slot", "fullday"), "guest_count": data.get("guest_count", 100),
        "status": data.get("status", "tentative"), "total_amount": total,
        "advance_paid": advance, "balance_due": total - advance,
        "special_requirements": data.get("special_requirements"), "notes": data.get("notes"),
    }).execute()
    return {"booking": result.data[0], "message": "Event booked"}

@router.put("/bookings/{booking_id}")
async def update_booking(org_id: str, booking_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    allowed = ["status", "total_amount", "advance_paid", "balance_due", "guest_count", "special_requirements", "notes"]
    update = {k: v for k, v in data.items() if k in allowed}
    db.table("event_bookings").update(update).eq("id", booking_id).eq("organization_id", org_id).execute()
    return {"message": "Booking updated"}

@router.get("/bookings/{booking_id}/checklist")
async def get_checklist(org_id: str, booking_id: str):
    await check_access(org_id)
    db = get_supabase()
    return {"checklist": db.table("event_checklist").select("*").eq("event_booking_id", booking_id).order("sort_order").execute().data}

@router.post("/bookings/{booking_id}/checklist")
async def add_checklist_item(org_id: str, booking_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("event_checklist").insert({"event_booking_id": booking_id, "task": data["task"], "assigned_to": data.get("assigned_to"), "due_date": data.get("due_date")}).execute()
    return {"item": result.data[0]}

@router.post("/bookings/{booking_id}/vendors")
async def add_vendor(org_id: str, booking_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("event_vendors").insert({"organization_id": org_id, "event_booking_id": booking_id, "vendor_name": data["vendor_name"], "vendor_phone": data.get("vendor_phone"), "service_type": data.get("service_type"), "amount": data.get("amount", 0)}).execute()
    return {"vendor": result.data[0]}

@router.get("/packages")
async def list_packages(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    return {"packages": db.table("event_packages").select("*").eq("organization_id", org_id).eq("is_active", True).order("sort_order").execute().data}

@router.post("/packages")
async def create_package(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("event_packages").insert({"organization_id": org_id, "name": data["name"], "description": data.get("description"), "price": data.get("price"), "per_plate_price": data.get("per_plate_price"), "min_guests": data.get("min_guests", 50), "includes": data.get("includes", []), "add_ons": data.get("add_ons", [])}).execute()
    return {"package": result.data[0]}

@router.get("/dashboard")
async def events_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    bookings = db.table("event_bookings").select("status, total_amount, advance_paid, event_date").eq("organization_id", org_id).execute()
    upcoming = sum(1 for b in bookings.data if b["status"] in ("tentative", "confirmed") and b.get("event_date", "") >= str(date.today()))
    revenue = sum(float(b.get("advance_paid", 0) or 0) for b in bookings.data)
    pending = sum(float(b.get("total_amount", 0) or 0) - float(b.get("advance_paid", 0) or 0) for b in bookings.data if b["status"] != "cancelled")
    return {"total_bookings": len(bookings.data), "upcoming": upcoming, "revenue_collected": revenue, "pending_amount": pending}
