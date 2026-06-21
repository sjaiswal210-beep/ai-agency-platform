from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date, datetime

router = APIRouter(prefix="/api/org/{org_id}/job-cards", tags=["job-cards"])


async def check_access(org_id: str):
    db = get_supabase()
    result = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "job_cards").single().execute()
    if not result.data or not result.data.get("enabled"):
        raise HTTPException(403, "Job Cards module not enabled")


@router.get("/")
async def list_job_cards(org_id: str, status: Optional[str] = None, priority: Optional[str] = None, limit: int = Query(default=50, le=200)):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("job_cards").select("*").eq("organization_id", org_id)
    if status:
        query = query.eq("status", status)
    if priority:
        query = query.eq("priority", priority)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return {"job_cards": result.data, "count": len(result.data)}


@router.post("/")
async def create_job_card(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    
    # Auto-generate job number
    count = db.table("job_cards").select("id", count="exact").eq("organization_id", org_id).execute()
    job_number = f"JOB-{(count.count or 0) + 1:04d}"
    
    result = db.table("job_cards").insert({
        "organization_id": org_id,
        "job_number": job_number,
        "customer_name": data["customer_name"],
        "customer_phone": data.get("customer_phone"),
        "customer_address": data.get("customer_address"),
        "device_type": data.get("device_type", "other"),
        "device_brand": data.get("device_brand"),
        "device_model": data.get("device_model"),
        "registration_no": data.get("registration_no"),
        "serial_number": data.get("serial_number"),
        "problem_description": data["problem_description"],
        "assigned_to": data.get("assigned_to"),
        "priority": data.get("priority", "normal"),
        "estimated_cost": data.get("estimated_cost"),
        "estimated_hours": data.get("estimated_hours"),
        "advance_paid": data.get("advance_paid", 0),
    }).execute()
    return {"job_card": result.data[0], "message": f"Job card {job_number} created"}


@router.get("/{job_id}")
async def get_job_card(org_id: str, job_id: str):
    await check_access(org_id)
    db = get_supabase()
    job = db.table("job_cards").select("*").eq("id", job_id).eq("organization_id", org_id).single().execute()
    if not job.data:
        raise HTTPException(404, "Job card not found")
    parts = db.table("job_parts").select("*").eq("job_card_id", job_id).execute()
    history = db.table("job_status_history").select("*").eq("job_card_id", job_id).order("created_at").execute()
    return {**job.data, "parts": parts.data, "history": history.data}


@router.post("/{job_id}/status")
async def update_status(org_id: str, job_id: str, data: dict):
    """Update job status and log the change."""
    await check_access(org_id)
    db = get_supabase()
    
    new_status = data["status"]
    job = db.table("job_cards").select("status").eq("id", job_id).eq("organization_id", org_id).single().execute()
    if not job.data:
        raise HTTPException(404, "Job card not found")
    
    old_status = job.data["status"]
    update = {"status": new_status}
    if new_status == "ready" or new_status == "delivered":
        update["completed_at"] = datetime.utcnow().isoformat()
    if new_status == "delivered":
        update["delivered_at"] = datetime.utcnow().isoformat()
    
    db.table("job_cards").update(update).eq("id", job_id).execute()
    
    # Log status change
    db.table("job_status_history").insert({
        "job_card_id": job_id,
        "from_status": old_status,
        "to_status": new_status,
        "changed_by": data.get("changed_by"),
        "notes": data.get("notes"),
        "photo_url": data.get("photo_url"),
    }).execute()
    
    return {"message": f"Status: {old_status} -> {new_status}"}


@router.post("/{job_id}/parts")
async def add_part(org_id: str, job_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    qty = int(data.get("quantity", 1))
    price = float(data.get("unit_price", 0))
    
    db.table("job_parts").insert({
        "job_card_id": job_id,
        "organization_id": org_id,
        "part_name": data["part_name"],
        "quantity": qty,
        "unit_price": price,
        "total_price": qty * price,
        "source": data.get("source", "stock"),
        "vendor": data.get("vendor"),
    }).execute()
    
    # Update total parts cost on job
    parts = db.table("job_parts").select("total_price").eq("job_card_id", job_id).execute()
    total_parts = sum(float(p.get("total_price", 0) or 0) for p in parts.data)
    job = db.table("job_cards").select("labor_cost").eq("id", job_id).single().execute()
    labor = float(job.data.get("labor_cost", 0) or 0) if job.data else 0
    db.table("job_cards").update({"parts_cost": total_parts, "total_cost": total_parts + labor}).eq("id", job_id).execute()
    
    return {"message": "Part added", "parts_cost": total_parts}


@router.put("/{job_id}/cost")
async def update_cost(org_id: str, job_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    labor = float(data.get("labor_cost", 0))
    job = db.table("job_cards").select("parts_cost").eq("id", job_id).single().execute()
    parts = float(job.data.get("parts_cost", 0) or 0) if job.data else 0
    db.table("job_cards").update({
        "labor_cost": labor,
        "total_cost": parts + labor,
        "diagnosis_notes": data.get("diagnosis_notes"),
    }).eq("id", job_id).eq("organization_id", org_id).execute()
    return {"message": "Cost updated", "total": parts + labor}


@router.get("/customer/{phone}")
async def customer_history(org_id: str, phone: str):
    """Get all past jobs for a customer phone number."""
    await check_access(org_id)
    db = get_supabase()
    result = db.table("job_cards").select("*").eq("organization_id", org_id).eq("customer_phone", phone).order("created_at", desc=True).execute()
    return {"jobs": result.data, "count": len(result.data)}


@router.get("/reminders/due")
async def due_reminders(org_id: str, days: int = Query(default=7)):
    await check_access(org_id)
    db = get_supabase()
    due_by = str(date.today() + __import__('datetime').timedelta(days=days))
    result = db.table("service_reminders").select("*").eq("organization_id", org_id).eq("status", "pending").lte("due_date", due_by).order("due_date").execute()
    return {"reminders": result.data}


@router.post("/reminders")
async def create_reminder(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("service_reminders").insert({
        "organization_id": org_id,
        "customer_name": data["customer_name"],
        "customer_phone": data["customer_phone"],
        "device_info": data.get("device_info"),
        "reminder_type": data.get("reminder_type", "service_due"),
        "due_date": data["due_date"],
        "message": data.get("message"),
        "recurrence": data.get("recurrence", "none"),
    }).execute()
    return {"reminder": result.data[0], "message": "Reminder set"}


@router.get("/dashboard")
async def job_cards_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    
    jobs = db.table("job_cards").select("status, total_cost, priority").eq("organization_id", org_id).execute()
    reminders = db.table("service_reminders").select("status").eq("organization_id", org_id).eq("status", "pending").execute()
    
    total = len(jobs.data)
    pending = sum(1 for j in jobs.data if j["status"] not in ("delivered", "cancelled"))
    urgent = sum(1 for j in jobs.data if j["priority"] == "urgent" and j["status"] not in ("delivered", "cancelled"))
    revenue = sum(float(j.get("total_cost", 0) or 0) for j in jobs.data if j["status"] == "delivered")
    
    by_status = {}
    for j in jobs.data:
        by_status[j["status"]] = by_status.get(j["status"], 0) + 1
    
    return {
        "total_jobs": total,
        "pending_jobs": pending,
        "urgent_jobs": urgent,
        "total_revenue": revenue,
        "due_reminders": len(reminders.data),
        "by_status": by_status,
    }
