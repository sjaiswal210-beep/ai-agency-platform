from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.core.supabase import get_supabase
import json

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("/")
async def list_organizations(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0
):
    supabase = get_supabase()
    query = supabase.table("organizations").select("*, organization_modules(module_id, enabled)")
    
    if status:
        query = query.eq("status", status)
    if plan:
        query = query.eq("plan", plan)
    if search:
        query = query.ilike("name", f"%{search}%")
    
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"organizations": result.data, "count": len(result.data)}


@router.post("/")
async def create_organization(data: dict):
    supabase = get_supabase()
    
    # Create org
    org_data = {
        "name": data["name"],
        "slug": data["slug"],
        "plan": data.get("plan", "starter"),
        "phone": data.get("phone"),
        "email": data.get("email"),
        "owner_id": data.get("owner_id"),
    }
    
    result = supabase.table("organizations").insert(org_data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create organization")
    
    org = result.data[0]
    
    # If template provided, apply it
    if data.get("template_id"):
        await apply_template_to_org(org["id"], data["template_id"])
    else:
        # Enable core modules by default
        core_modules = supabase.table("modules").select("id").eq("is_core", True).execute()
        for mod in core_modules.data:
            supabase.table("organization_modules").insert({
                "organization_id": org["id"],
                "module_id": mod["id"],
                "enabled": True
            }).execute()
    
    return {"organization": org, "message": "Organization created"}


@router.get("/{org_id}")
async def get_organization(org_id: str):
    supabase = get_supabase()
    result = supabase.table("organizations").select("*").eq("id", org_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Organization not found")
    return result.data


@router.put("/{org_id}")
async def update_organization(org_id: str, data: dict):
    supabase = get_supabase()
    allowed = ["name", "logo_url", "brand_color", "plan", "phone", "email", "address", "city", "settings", "status"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    
    result = supabase.table("organizations").update(update_data).eq("id", org_id).execute()
    if not result.data:
        raise HTTPException(404, "Organization not found")
    return {"organization": result.data[0], "message": "Updated"}


@router.get("/{org_id}/modules")
async def get_org_modules(org_id: str):
    supabase = get_supabase()
    result = supabase.table("organization_modules").select("*, modules(*)").eq("organization_id", org_id).execute()
    return {"modules": result.data}


@router.post("/{org_id}/modules")
async def enable_module(org_id: str, data: dict):
    supabase = get_supabase()
    module_id = data["module_id"]
    
    # Check module exists
    mod = supabase.table("modules").select("*").eq("id", module_id).single().execute()
    if not mod.data:
        raise HTTPException(404, f"Module '{module_id}' not found")
    
    # Check dependencies
    deps = mod.data.get("dependencies", [])
    if deps:
        enabled = supabase.table("organization_modules").select("module_id").eq("organization_id", org_id).eq("enabled", True).execute()
        enabled_ids = [m["module_id"] for m in enabled.data]
        missing = [d for d in deps if d not in enabled_ids]
        if missing:
            raise HTTPException(400, f"Missing dependencies: {missing}")
    
    # Upsert
    result = supabase.table("organization_modules").upsert({
        "organization_id": org_id,
        "module_id": module_id,
        "enabled": True,
        "config": data.get("config", {})
    }).execute()
    
    # Audit log
    supabase.table("audit_log").insert({
        "organization_id": org_id,
        "action": "module_enabled",
        "entity_type": "module",
        "entity_id": module_id,
        "new_value": {"module_id": module_id, "enabled": True}
    }).execute()
    
    return {"message": f"Module '{module_id}' enabled", "data": result.data}


@router.delete("/{org_id}/modules/{module_id}")
async def disable_module(org_id: str, module_id: str):
    supabase = get_supabase()
    
    # Check if it's a core module
    mod = supabase.table("modules").select("is_core").eq("id", module_id).single().execute()
    if mod.data and mod.data.get("is_core"):
        raise HTTPException(400, "Cannot disable core modules")
    
    result = supabase.table("organization_modules").update({"enabled": False}).eq("organization_id", org_id).eq("module_id", module_id).execute()
    
    # Audit log
    supabase.table("audit_log").insert({
        "organization_id": org_id,
        "action": "module_disabled",
        "entity_type": "module",
        "entity_id": module_id
    }).execute()
    
    return {"message": f"Module '{module_id}' disabled"}


@router.post("/{org_id}/apply-template")
async def apply_template(org_id: str, data: dict):
    template_id = data["template_id"]
    await apply_template_to_org(org_id, template_id)
    return {"message": f"Template '{template_id}' applied"}


async def apply_template_to_org(org_id: str, template_id: str):
    supabase = get_supabase()
    template = supabase.table("industry_templates").select("*").eq("id", template_id).single().execute()
    if not template.data:
        raise HTTPException(404, f"Template '{template_id}' not found")
    
    module_ids = template.data["module_ids"]
    for mod_id in module_ids:
        supabase.table("organization_modules").upsert({
            "organization_id": org_id,
            "module_id": mod_id,
            "enabled": True
        }).execute()
    
    # Audit
    supabase.table("audit_log").insert({
        "organization_id": org_id,
        "action": "template_applied",
        "entity_type": "template",
        "entity_id": template_id,
        "new_value": {"template_id": template_id, "modules": module_ids}
    }).execute()
