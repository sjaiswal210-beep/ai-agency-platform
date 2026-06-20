from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/org/{org_id}/crm", tags=["crm"])


async def check_crm_access(org_id: str):
    supabase = get_supabase()
    result = supabase.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "crm").single().execute()
    if not result.data or not result.data.get("enabled"):
        raise HTTPException(403, "CRM module not enabled for this organization")


@router.get("/contacts")
async def list_contacts(
    org_id: str,
    type: Optional[str] = None,
    stage: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0
):
    await check_crm_access(org_id)
    supabase = get_supabase()
    query = supabase.table("crm_contacts").select("*").eq("organization_id", org_id).eq("is_deleted", False)
    
    if type:
        query = query.eq("type", type)
    if stage:
        query = query.eq("stage", stage)
    if search:
        query = query.or_(f"name.ilike.%{search}%,phone.ilike.%{search}%,email.ilike.%{search}%")
    if tags:
        query = query.contains("tags", [tags])
    
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"contacts": result.data, "count": len(result.data)}


@router.post("/contacts")
async def create_contact(org_id: str, data: dict):
    await check_crm_access(org_id)
    supabase = get_supabase()
    
    contact_data = {
        "organization_id": org_id,
        "name": data["name"],
        "type": data.get("type", "lead"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "company": data.get("company"),
        "designation": data.get("designation"),
        "stage": data.get("stage", "new"),
        "tags": data.get("tags", []),
        "custom_fields": data.get("custom_fields", {}),
        "source": data.get("source"),
        "assigned_to": data.get("assigned_to"),
        "notes": data.get("notes"),
    }
    
    result = supabase.table("crm_contacts").insert(contact_data).execute()
    return {"contact": result.data[0], "message": "Contact created"}


@router.get("/contacts/{contact_id}")
async def get_contact(org_id: str, contact_id: str):
    await check_crm_access(org_id)
    supabase = get_supabase()
    result = supabase.table("crm_contacts").select("*").eq("id", contact_id).eq("organization_id", org_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Contact not found")
    return result.data


@router.put("/contacts/{contact_id}")
async def update_contact(org_id: str, contact_id: str, data: dict):
    await check_crm_access(org_id)
    supabase = get_supabase()
    allowed = ["name", "type", "email", "phone", "company", "designation", "stage", "score", "tags", "custom_fields", "source", "assigned_to", "notes"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    
    result = supabase.table("crm_contacts").update(update_data).eq("id", contact_id).eq("organization_id", org_id).execute()
    if not result.data:
        raise HTTPException(404, "Contact not found")
    return {"contact": result.data[0], "message": "Updated"}


@router.delete("/contacts/{contact_id}")
async def delete_contact(org_id: str, contact_id: str):
    await check_crm_access(org_id)
    supabase = get_supabase()
    result = supabase.table("crm_contacts").update({"is_deleted": True}).eq("id", contact_id).eq("organization_id", org_id).execute()
    return {"message": "Contact deleted"}


@router.get("/contacts/{contact_id}/activities")
async def list_activities(org_id: str, contact_id: str, limit: int = Query(default=30, le=100)):
    await check_crm_access(org_id)
    supabase = get_supabase()
    result = supabase.table("crm_activities").select("*").eq("contact_id", contact_id).eq("organization_id", org_id).order("created_at", desc=True).limit(limit).execute()
    return {"activities": result.data}


@router.post("/contacts/{contact_id}/activities")
async def add_activity(org_id: str, contact_id: str, data: dict):
    await check_crm_access(org_id)
    supabase = get_supabase()
    
    activity_data = {
        "organization_id": org_id,
        "contact_id": contact_id,
        "type": data["type"],
        "title": data.get("title"),
        "description": data.get("description"),
        "status": data.get("status", "pending"),
        "due_date": data.get("due_date"),
        "created_by": data.get("created_by"),
    }
    
    result = supabase.table("crm_activities").insert(activity_data).execute()
    
    # Update last_contacted_at
    supabase.table("crm_contacts").update({"last_contacted_at": "now()"}).eq("id", contact_id).execute()
    
    return {"activity": result.data[0], "message": "Activity added"}


@router.get("/pipeline")
async def get_pipeline(org_id: str):
    await check_crm_access(org_id)
    supabase = get_supabase()
    result = supabase.table("crm_pipelines").select("*").eq("organization_id", org_id).eq("is_default", True).single().execute()
    
    if not result.data:
        # Create default pipeline
        default = supabase.table("crm_pipelines").insert({
            "organization_id": org_id,
            "name": "Default Pipeline",
            "is_default": True
        }).execute()
        return default.data[0]
    
    return result.data


@router.put("/pipeline")
async def update_pipeline(org_id: str, data: dict):
    await check_crm_access(org_id)
    supabase = get_supabase()
    result = supabase.table("crm_pipelines").update({"stages": data["stages"]}).eq("organization_id", org_id).eq("is_default", True).execute()
    if not result.data:
        raise HTTPException(404, "Pipeline not found")
    return {"pipeline": result.data[0], "message": "Pipeline updated"}


@router.get("/dashboard")
async def crm_dashboard(org_id: str):
    await check_crm_access(org_id)
    supabase = get_supabase()
    
    contacts = supabase.table("crm_contacts").select("type, stage", count="exact").eq("organization_id", org_id).eq("is_deleted", False).execute()
    
    by_type = {}
    by_stage = {}
    for c in contacts.data:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1
        by_stage[c["stage"]] = by_stage.get(c["stage"], 0) + 1
    
    return {
        "total_contacts": contacts.count,
        "by_type": by_type,
        "by_stage": by_stage
    }
