from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/org/{org_id}/catalog", tags=["catalog"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "catalog").single().execute()
    if not r.data or not r.data.get("enabled"):
        raise HTTPException(403, "Catalog module not enabled")

@router.get("/categories")
async def list_categories(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("catalog_categories").select("*").eq("organization_id", org_id).eq("is_active", True).order("sort_order").execute()
    return {"categories": result.data}

@router.post("/categories")
async def create_category(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("catalog_categories").insert({
        "organization_id": org_id, "name": data["name"],
        "image_url": data.get("image_url"), "sort_order": data.get("sort_order", 0),
    }).execute()
    return {"category": result.data[0], "message": "Category created"}

@router.get("/items")
async def list_items(org_id: str, category_id: Optional[str] = None, search: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("catalog_items").select("*, catalog_categories(name)").eq("organization_id", org_id).eq("is_active", True)
    if category_id: query = query.eq("category_id", category_id)
    if search: query = query.ilike("name", f"%{search}%")
    result = query.order("sort_order").execute()
    return {"items": result.data}

@router.post("/items")
async def create_item(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("catalog_items").insert({
        "organization_id": org_id, "category_id": data.get("category_id"),
        "name": data["name"], "description": data.get("description"),
        "price": data.get("price"), "compare_price": data.get("compare_price"),
        "images": data.get("images", []), "variants": data.get("variants", []),
        "tags": data.get("tags", []), "in_stock": data.get("in_stock", True),
    }).execute()
    return {"item": result.data[0], "message": "Item added"}

@router.put("/items/{item_id}")
async def update_item(org_id: str, item_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    allowed = ["name", "description", "price", "compare_price", "images", "variants", "tags", "in_stock", "category_id", "sort_order", "is_active"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    db.table("catalog_items").update(update_data).eq("id", item_id).eq("organization_id", org_id).execute()
    return {"message": "Updated"}
