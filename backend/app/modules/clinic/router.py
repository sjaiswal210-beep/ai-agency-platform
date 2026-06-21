from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date

router = APIRouter(prefix="/api/org/{org_id}/clinic", tags=["clinic"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "clinic").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "Clinic module not enabled")

@router.get("/patients")
async def list_patients(org_id: str, search: Optional[str] = None, limit: int = Query(default=50, le=200)):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("patients").select("*").eq("organization_id", org_id)
    if search: query = query.or_(f"name.ilike.%{search}%,phone.ilike.%{search}%")
    result = query.order("created_at", desc=True).limit(limit).execute()
    return {"patients": result.data}

@router.post("/patients")
async def create_patient(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    count = db.table("patients").select("id", count="exact").eq("organization_id", org_id).execute()
    patient_number = f"PAT-{(count.count or 0) + 1:04d}"
    result = db.table("patients").insert({
        "organization_id": org_id, "patient_number": patient_number,
        "name": data["name"], "age": data.get("age"), "gender": data.get("gender"),
        "phone": data.get("phone"), "blood_group": data.get("blood_group"),
        "allergies": data.get("allergies", []), "medical_history": data.get("medical_history"),
        "ongoing_medications": data.get("ongoing_medications"),
        "emergency_contact": data.get("emergency_contact"), "address": data.get("address"),
    }).execute()
    return {"patient": result.data[0], "message": f"Patient {patient_number} registered"}

@router.get("/patients/{patient_id}")
async def get_patient(org_id: str, patient_id: str):
    await check_access(org_id)
    db = get_supabase()
    patient = db.table("patients").select("*").eq("id", patient_id).eq("organization_id", org_id).single().execute()
    consultations = db.table("consultations").select("*").eq("patient_id", patient_id).order("date", desc=True).limit(20).execute()
    documents = db.table("patient_documents").select("*").eq("patient_id", patient_id).order("date", desc=True).execute()
    return {"patient": patient.data, "consultations": consultations.data, "documents": documents.data}

@router.post("/consultations")
async def create_consultation(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    fee = float(data.get("consultation_fee", 0))
    proc = float(data.get("procedure_charges", 0))
    result = db.table("consultations").insert({
        "organization_id": org_id, "patient_id": data["patient_id"],
        "doctor_name": data.get("doctor_name"), "symptoms": data.get("symptoms"),
        "diagnosis": data.get("diagnosis"), "prescription": data.get("prescription", []),
        "vitals": data.get("vitals", {}), "follow_up_date": data.get("follow_up_date"),
        "lab_tests_ordered": data.get("lab_tests_ordered", []),
        "notes": data.get("notes"), "consultation_fee": fee,
        "procedure_charges": proc, "total_bill": fee + proc,
    }).execute()
    return {"consultation": result.data[0], "message": "Consultation saved"}

@router.get("/today")
async def todays_patients(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("consultations").select("*, patients(name, phone, age, gender)").eq("organization_id", org_id).eq("date", str(date.today())).order("token_number").execute()
    return {"consultations": result.data, "count": len(result.data)}

@router.get("/dashboard")
async def clinic_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    today_count = db.table("consultations").select("id", count="exact").eq("organization_id", org_id).eq("date", str(date.today())).execute()
    total_patients = db.table("patients").select("id", count="exact").eq("organization_id", org_id).execute()
    return {"today_patients": today_count.count, "total_patients": total_patients.count}
