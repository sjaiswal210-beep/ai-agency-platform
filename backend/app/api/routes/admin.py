from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/modules")
async def list_all_modules():
    supabase = get_supabase()
    result = supabase.table("modules").select("*").order("sort_order").execute()
    return {"modules": result.data}


@router.get("/organizations")
async def admin_list_organizations(
    search: Optional[str] = None,
    plan: Optional[str] = None,
    limit: int = Query(default=200, le=500),
    offset: int = 0
):
    supabase = get_supabase()
    query = supabase.table("organizations").select("*, organization_modules(module_id, enabled)")
    
    if search:
        query = query.ilike("name", f"%{search}%")
    if plan:
        query = query.eq("plan", plan)
    
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    
    # Add module count to each org
    orgs = []
    for org in result.data:
        modules = org.pop("organization_modules", [])
        org["enabled_modules_count"] = len([m for m in modules if m.get("enabled")])
        org["enabled_modules"] = [m["module_id"] for m in modules if m.get("enabled")]
        orgs.append(org)
    
    return {"organizations": orgs, "count": len(orgs)}


@router.put("/organizations/{org_id}/modules")
async def bulk_update_modules(org_id: str, data: dict):
    supabase = get_supabase()
    module_ids = data.get("enabled_modules", [])
    
    # Get all available modules
    all_modules = supabase.table("modules").select("id, is_core").execute()
    core_ids = [m["id"] for m in all_modules.data if m.get("is_core")]
    
    # Ensure core modules are always included
    final_modules = list(set(module_ids + core_ids))
    
    # Delete existing and re-insert
    supabase.table("organization_modules").delete().eq("organization_id", org_id).execute()
    
    for mod_id in final_modules:
        supabase.table("organization_modules").insert({
            "organization_id": org_id,
            "module_id": mod_id,
            "enabled": True
        }).execute()
    
    # Audit
    supabase.table("audit_log").insert({
        "organization_id": org_id,
        "action": "modules_bulk_updated",
        "entity_type": "organization",
        "entity_id": org_id,
        "new_value": {"enabled_modules": final_modules}
    }).execute()
    
    return {"message": "Modules updated", "enabled_modules": final_modules}


@router.get("/templates")
async def list_templates():
    supabase = get_supabase()
    result = supabase.table("industry_templates").select("*").order("sort_order").execute()
    return {"templates": result.data}


@router.post("/templates")
async def create_template(data: dict):
    supabase = get_supabase()
    template_data = {
        "id": data["id"],
        "name": data["name"],
        "description": data.get("description", ""),
        "icon": data.get("icon", "Briefcase"),
        "category": data.get("category", "general"),
        "module_ids": data["module_ids"],
        "default_config": data.get("default_config", {}),
        "sort_order": data.get("sort_order", 99)
    }
    result = supabase.table("industry_templates").insert(template_data).execute()
    return {"template": result.data[0], "message": "Template created"}


@router.put("/templates/{template_id}")
async def update_template(template_id: str, data: dict):
    supabase = get_supabase()
    allowed = ["name", "description", "icon", "category", "module_ids", "default_config", "sort_order", "is_active"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    
    result = supabase.table("industry_templates").update(update_data).eq("id", template_id).execute()
    if not result.data:
        raise HTTPException(404, "Template not found")
    return {"template": result.data[0], "message": "Template updated"}


@router.get("/audit-log")
async def get_audit_log(
    org_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(default=200, le=500),
    offset: int = 0
):
    supabase = get_supabase()
    query = supabase.table("audit_log").select("*")
    
    if org_id:
        query = query.eq("organization_id", org_id)
    if action:
        query = query.eq("action", action)
    
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"logs": result.data, "count": len(result.data)}
