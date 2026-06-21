from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date, timedelta

router = APIRouter(prefix="/api/org/{org_id}/reminders", tags=["reminders"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "reminders").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "Reminders module not enabled")

@router.get("/")
async def list_reminders(org_id: str, status: Optional[str] = None, type: Optional[str] = None, limit: int = Query(default=100)):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("reminders").select("*").eq("organization_id", org_id)
    if status: query = query.eq("status", status)
    if type: query = query.eq("type", type)
    return {"reminders": query.order("due_date").limit(limit).execute().data}

@router.post("/")
async def create_reminder(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("reminders").insert({
        "organization_id": org_id,
        "customer_name": data["customer_name"],
        "customer_phone": data["customer_phone"],
        "customer_email": data.get("customer_email"),
        "type": data.get("type", "general"),
        "item_description": data.get("item_description"),
        "reference_number": data.get("reference_number"),
        "due_date": data["due_date"],
        "remind_days_before": data.get("remind_days_before", [30, 7, 1]),
        "recurrence": data.get("recurrence", "none"),
        "message_template": data.get("message_template"),
        "amount": data.get("amount"),
        "notes": data.get("notes"),
    }).execute()
    return {"reminder": result.data[0], "message": "Reminder created"}

@router.put("/{reminder_id}")
async def update_reminder(org_id: str, reminder_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    allowed = ["status", "due_date", "notes", "amount", "message_template", "recurrence"]
    update = {k: v for k, v in data.items() if k in allowed}
    db.table("reminders").update(update).eq("id", reminder_id).eq("organization_id", org_id).execute()
    return {"message": "Reminder updated"}

@router.post("/{reminder_id}/renew")
async def mark_renewed(org_id: str, reminder_id: str, data: dict):
    """Mark as renewed and auto-create next reminder if recurring."""
    await check_access(org_id)
    db = get_supabase()
    reminder = db.table("reminders").select("*").eq("id", reminder_id).single().execute()
    if not reminder.data: raise HTTPException(404, "Not found")
    
    r = reminder.data
    db.table("reminders").update({"status": "renewed", "renewed_at": str(date.today())}).eq("id", reminder_id).execute()
    
    # Create next reminder if recurring
    recurrence = r.get("recurrence", "none")
    if recurrence != "none":
        current_due = date.fromisoformat(r["due_date"]) if isinstance(r["due_date"], str) else r["due_date"]
        if recurrence == "monthly": next_due = current_due + timedelta(days=30)
        elif recurrence == "quarterly": next_due = current_due + timedelta(days=90)
        elif recurrence == "half_yearly": next_due = current_due + timedelta(days=180)
        elif recurrence == "yearly": next_due = current_due + timedelta(days=365)
        else: next_due = None
        
        if next_due:
            db.table("reminders").insert({
                "organization_id": org_id,
                "customer_name": r["customer_name"],
                "customer_phone": r["customer_phone"],
                "type": r["type"],
                "item_description": r.get("item_description"),
                "reference_number": r.get("reference_number"),
                "due_date": str(next_due),
                "remind_days_before": r.get("remind_days_before", [30, 7, 1]),
                "recurrence": recurrence,
                "message_template": r.get("message_template"),
                "amount": r.get("amount"),
            }).execute()
    
    return {"message": "Marked as renewed", "next_created": recurrence != "none"}

@router.get("/due-soon")
async def due_soon(org_id: str, days: int = Query(default=7)):
    """Get reminders due within X days."""
    await check_access(org_id)
    db = get_supabase()
    due_by = str(date.today() + timedelta(days=days))
    result = db.table("reminders").select("*").eq("organization_id", org_id).eq("status", "active").lte("due_date", due_by).gte("due_date", str(date.today())).order("due_date").execute()
    return {"reminders": result.data, "count": len(result.data)}

@router.get("/overdue")
async def overdue(org_id: str):
    """Get all overdue reminders."""
    await check_access(org_id)
    db = get_supabase()
    result = db.table("reminders").select("*").eq("organization_id", org_id).eq("status", "active").lt("due_date", str(date.today())).order("due_date").execute()
    return {"reminders": result.data, "count": len(result.data)}

@router.get("/dashboard")
async def reminders_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    all_r = db.table("reminders").select("status, due_date, type").eq("organization_id", org_id).execute()
    today = str(date.today())
    week = str(date.today() + timedelta(days=7))
    
    active = sum(1 for r in all_r.data if r["status"] == "active")
    overdue = sum(1 for r in all_r.data if r["status"] == "active" and r.get("due_date", "") < today)
    due_this_week = sum(1 for r in all_r.data if r["status"] == "active" and today <= r.get("due_date", "") <= week)
    renewed = sum(1 for r in all_r.data if r["status"] == "renewed")
    
    by_type = {}
    for r in all_r.data:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
    
    return {"active": active, "overdue": overdue, "due_this_week": due_this_week, "total_renewed": renewed, "by_type": by_type}
