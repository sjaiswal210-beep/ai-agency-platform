from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date

router = APIRouter(prefix="/api/org/{org_id}/students", tags=["students"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "students").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "Students module not enabled")

@router.get("/batches")
async def list_batches(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("batches").select("*").eq("organization_id", org_id).eq("is_active", True).execute()
    return {"batches": result.data}

@router.post("/batches")
async def create_batch(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("batches").insert({
        "organization_id": org_id, "name": data["name"],
        "description": data.get("description"), "schedule": data.get("schedule", {}),
        "teacher_name": data.get("teacher_name"), "capacity": data.get("capacity", 30),
        "fee_amount": data.get("fee_amount", 0), "fee_frequency": data.get("fee_frequency", "monthly"),
        "start_date": data.get("start_date"),
    }).execute()
    return {"batch": result.data[0], "message": "Batch created"}

@router.get("/")
async def list_students(org_id: str, status: Optional[str] = None, batch_id: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("students").select("*, student_batches(batch_id, batches(name))").eq("organization_id", org_id)
    if status: query = query.eq("status", status)
    result = query.order("name").execute()
    return {"students": result.data}

@router.post("/")
async def enroll_student(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("students").insert({
        "organization_id": org_id, "name": data["name"],
        "phone": data.get("phone"), "parent_phone": data.get("parent_phone"),
        "email": data.get("email"), "date_of_birth": data.get("date_of_birth"),
        "notes": data.get("notes"),
    }).execute()
    student_id = result.data[0]["id"]
    if data.get("batch_id"):
        db.table("student_batches").insert({"student_id": student_id, "batch_id": data["batch_id"]}).execute()
        db.table("batches").update({"current_strength": db.table("student_batches").select("id", count="exact").eq("batch_id", data["batch_id"]).execute().count}).eq("id", data["batch_id"]).execute()
    return {"student": result.data[0], "message": "Student enrolled"}

@router.post("/attendance")
async def mark_attendance(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    batch_id = data["batch_id"]
    att_date = data.get("date", str(date.today()))
    records = data.get("records", [])  # [{student_id, status}]
    for r in records:
        db.table("student_attendance").upsert({
            "organization_id": org_id, "batch_id": batch_id,
            "student_id": r["student_id"], "date": att_date,
            "status": r.get("status", "present"),
        }).execute()
    return {"message": f"Attendance marked for {len(records)} students"}

@router.get("/attendance/{batch_id}")
async def get_attendance(org_id: str, batch_id: str, date_str: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    d = date_str or str(date.today())
    result = db.table("student_attendance").select("*, students(name)").eq("batch_id", batch_id).eq("date", d).execute()
    return {"attendance": result.data, "date": d}

@router.post("/fees/generate")
async def generate_fees(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    batch_id = data.get("batch_id")
    month = data.get("month", date.today().month)
    year = data.get("year", date.today().year)
    batch = db.table("batches").select("fee_amount").eq("id", batch_id).single().execute()
    fee_amt = float(batch.data.get("fee_amount", 0)) if batch.data else 0
    students = db.table("student_batches").select("student_id").eq("batch_id", batch_id).eq("status", "active").execute()
    generated = 0
    for s in (students.data or []):
        db.table("student_fees").upsert({
            "organization_id": org_id, "student_id": s["student_id"],
            "batch_id": batch_id, "month": month, "year": year,
            "amount": fee_amt, "discount": 0, "final_amount": fee_amt,
        }).execute()
        generated += 1
    return {"message": f"Fees generated for {generated} students", "amount": fee_amt}

@router.get("/fees")
async def list_fees(org_id: str, status: Optional[str] = None, month: Optional[int] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("student_fees").select("*, students(name, phone, parent_phone)").eq("organization_id", org_id)
    if status: query = query.eq("status", status)
    if month: query = query.eq("month", month)
    result = query.order("created_at", desc=True).execute()
    return {"fees": result.data}

@router.post("/fees/{fee_id}/pay")
async def pay_fee(org_id: str, fee_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    db.table("student_fees").update({
        "status": "paid", "paid_date": data.get("date", str(date.today())),
        "payment_method": data.get("method", "cash"),
    }).eq("id", fee_id).execute()
    return {"message": "Fee paid"}

@router.get("/dashboard")
async def students_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    students = db.table("students").select("status", count="exact").eq("organization_id", org_id).eq("status", "active").execute()
    batches = db.table("batches").select("id", count="exact").eq("organization_id", org_id).eq("is_active", True).execute()
    fees = db.table("student_fees").select("status, final_amount").eq("organization_id", org_id).execute()
    pending = sum(float(f.get("final_amount", 0)) for f in fees.data if f["status"] in ("due", "overdue"))
    collected = sum(float(f.get("final_amount", 0)) for f in fees.data if f["status"] == "paid")
    return {"active_students": students.count, "active_batches": batches.count, "pending_fees": pending, "collected_fees": collected}
