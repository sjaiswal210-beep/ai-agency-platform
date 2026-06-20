from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date, datetime, timedelta

router = APIRouter(prefix="/api/org/{org_id}/booking", tags=["booking"])


async def check_booking_access(org_id: str):
    supabase = get_supabase()
    result = supabase.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "booking").single().execute()
    if not result.data or not result.data.get("enabled"):
        raise HTTPException(403, "Booking module not enabled for this organization")


@router.get("/services")
async def list_services(org_id: str):
    await check_booking_access(org_id)
    supabase = get_supabase()
    result = supabase.table("booking_services").select("*").eq("organization_id", org_id).order("sort_order").execute()
    return {"services": result.data}


@router.post("/services")
async def create_service(org_id: str, data: dict):
    await check_booking_access(org_id)
    supabase = get_supabase()
    
    service_data = {
        "organization_id": org_id,
        "name": data["name"],
        "description": data.get("description"),
        "duration_minutes": data.get("duration_minutes", 60),
        "price": data.get("price"),
        "currency": data.get("currency", "INR"),
        "category": data.get("category"),
        "is_active": data.get("is_active", True),
    }
    
    result = supabase.table("booking_services").insert(service_data).execute()
    return {"service": result.data[0], "message": "Service created"}


@router.put("/services/{service_id}")
async def update_service(org_id: str, service_id: str, data: dict):
    await check_booking_access(org_id)
    supabase = get_supabase()
    allowed = ["name", "description", "duration_minutes", "price", "currency", "category", "is_active", "sort_order"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    
    result = supabase.table("booking_services").update(update_data).eq("id", service_id).eq("organization_id", org_id).execute()
    if not result.data:
        raise HTTPException(404, "Service not found")
    return {"service": result.data[0], "message": "Updated"}


@router.get("/staff")
async def list_staff(org_id: str):
    await check_booking_access(org_id)
    supabase = get_supabase()
    result = supabase.table("booking_staff").select("*").eq("organization_id", org_id).execute()
    return {"staff": result.data}


@router.post("/staff")
async def add_staff(org_id: str, data: dict):
    await check_booking_access(org_id)
    supabase = get_supabase()
    
    staff_data = {
        "organization_id": org_id,
        "name": data["name"],
        "email": data.get("email"),
        "phone": data.get("phone"),
        "services": data.get("services", []),
        "availability": data.get("availability", {}),
        "is_active": data.get("is_active", True),
    }
    
    result = supabase.table("booking_staff").insert(staff_data).execute()
    return {"staff": result.data[0], "message": "Staff added"}


@router.get("/appointments")
async def list_appointments(
    org_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    staff_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    await check_booking_access(org_id)
    supabase = get_supabase()
    query = supabase.table("booking_appointments").select("*, booking_services(name, duration_minutes), booking_staff(name)").eq("organization_id", org_id)
    
    if date_from:
        query = query.gte("date", date_from)
    if date_to:
        query = query.lte("date", date_to)
    if staff_id:
        query = query.eq("staff_id", staff_id)
    if status:
        query = query.eq("status", status)
    
    result = query.order("date").order("start_time").limit(limit).execute()
    return {"appointments": result.data}


@router.post("/appointments")
async def create_appointment(org_id: str, data: dict):
    await check_booking_access(org_id)
    supabase = get_supabase()
    
    appt_data = {
        "organization_id": org_id,
        "service_id": data.get("service_id"),
        "staff_id": data.get("staff_id"),
        "contact_id": data.get("contact_id"),
        "customer_name": data["customer_name"],
        "customer_phone": data.get("customer_phone"),
        "customer_email": data.get("customer_email"),
        "date": data["date"],
        "start_time": data["start_time"],
        "end_time": data["end_time"],
        "status": data.get("status", "confirmed"),
        "notes": data.get("notes"),
        "source": data.get("source", "manual"),
    }
    
    result = supabase.table("booking_appointments").insert(appt_data).execute()
    return {"appointment": result.data[0], "message": "Appointment created"}


@router.put("/appointments/{appt_id}")
async def update_appointment(org_id: str, appt_id: str, data: dict):
    await check_booking_access(org_id)
    supabase = get_supabase()
    allowed = ["service_id", "staff_id", "customer_name", "customer_phone", "date", "start_time", "end_time", "status", "notes"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    
    result = supabase.table("booking_appointments").update(update_data).eq("id", appt_id).eq("organization_id", org_id).execute()
    if not result.data:
        raise HTTPException(404, "Appointment not found")
    return {"appointment": result.data[0], "message": "Updated"}


@router.get("/availability")
async def check_availability(org_id: str, date_str: str, staff_id: Optional[str] = None):
    await check_booking_access(org_id)
    supabase = get_supabase()
    
    # Get existing appointments for the date
    query = supabase.table("booking_appointments").select("start_time, end_time, staff_id").eq("organization_id", org_id).eq("date", date_str).neq("status", "cancelled")
    if staff_id:
        query = query.eq("staff_id", staff_id)
    
    booked = query.execute()
    
    # Get staff availability
    staff_query = supabase.table("booking_staff").select("id, name, availability").eq("organization_id", org_id).eq("is_active", True)
    if staff_id:
        staff_query = staff_query.eq("id", staff_id)
    
    staff = staff_query.execute()
    
    return {
        "date": date_str,
        "booked_slots": booked.data,
        "staff": staff.data,
    }
