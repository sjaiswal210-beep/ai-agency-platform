from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date

router = APIRouter(prefix="/api/org/{org_id}/assets", tags=["assets"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "assets").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "Assets module not enabled")

@router.get("/")
async def list_assets(org_id: str, type: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("assets").select("*").eq("organization_id", org_id)
    if type: query = query.eq("type", type)
    return {"assets": query.order("created_at", desc=True).execute().data}

@router.post("/")
async def create_asset(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("assets").insert({
        "organization_id": org_id, "name": data["name"],
        "type": data.get("type", "equipment"), "brand": data.get("brand"),
        "model": data.get("model"), "serial_number": data.get("serial_number"),
        "purchase_date": data.get("purchase_date"), "purchase_price": data.get("purchase_price"),
        "warranty_expiry": data.get("warranty_expiry"), "amc_expiry": data.get("amc_expiry"),
        "location": data.get("location"), "assigned_to": data.get("assigned_to"),
        "condition": data.get("condition", "good"), "notes": data.get("notes"),
    }).execute()
    return {"asset": result.data[0], "message": "Asset added"}

@router.get("/{asset_id}/history")
async def asset_history(org_id: str, asset_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("asset_service_history").select("*").eq("asset_id", asset_id).order("date", desc=True).execute()
    return {"history": result.data}

@router.post("/{asset_id}/service")
async def add_service(org_id: str, asset_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("asset_service_history").insert({
        "asset_id": asset_id, "organization_id": org_id,
        "type": data.get("type", "maintenance"), "description": data.get("description"),
        "cost": data.get("cost", 0), "vendor": data.get("vendor"),
        "date": data.get("date", str(date.today())), "next_due_date": data.get("next_due_date"),
    }).execute()
    return {"service": result.data[0], "message": "Service logged"}

@router.get("/dashboard")
async def assets_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    assets = db.table("assets").select("condition, purchase_price, warranty_expiry, amc_expiry").eq("organization_id", org_id).execute()
    total = len(assets.data)
    total_value = sum(float(a.get("purchase_price", 0) or 0) for a in assets.data)
    warranty_expiring = sum(1 for a in assets.data if a.get("warranty_expiry") and a["warranty_expiry"] <= str(date.today()))
    needs_repair = sum(1 for a in assets.data if a.get("condition") == "needs_repair")
    return {"total_assets": total, "total_value": total_value, "warranty_expired": warranty_expiring, "needs_repair": needs_repair}