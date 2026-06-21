from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date

router = APIRouter(prefix="/api/org/{org_id}/custom-orders", tags=["custom-orders"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "custom_orders").single().execute()
    if not r.data or not r.data.get("enabled"):
        raise HTTPException(403, "Custom Orders module not enabled")

@router.get("/")
async def list_orders(org_id: str, status: Optional[str] = None, limit: int = Query(default=50, le=200)):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("custom_orders").select("*").eq("organization_id", org_id)
    if status: query = query.eq("status", status)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return {"orders": result.data, "count": len(result.data)}

@router.post("/")
async def create_order(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    count = db.table("custom_orders").select("id", count="exact").eq("organization_id", org_id).execute()
    order_number = f"ORD-{(count.count or 0) + 1:04d}"
    total = float(data.get("material_cost", 0)) + float(data.get("making_charges", 0))
    advance = float(data.get("advance_paid", 0))
    result = db.table("custom_orders").insert({
        "organization_id": org_id, "order_number": order_number,
        "customer_name": data["customer_name"], "customer_phone": data.get("customer_phone"),
        "item_description": data["item_description"],
        "specifications": data.get("specifications", {}),
        "reference_images": data.get("reference_images", []),
        "measurements": data.get("measurements", {}),
        "material": data.get("material"),
        "material_cost": data.get("material_cost", 0),
        "making_charges": data.get("making_charges", 0),
        "total_price": total, "advance_paid": advance, "balance_due": total - advance,
        "assigned_to": data.get("assigned_to"),
        "promised_date": data.get("promised_date"),
        "notes": data.get("notes"),
    }).execute()
    return {"order": result.data[0], "message": f"Order {order_number} created"}

@router.put("/{order_id}/status")
async def update_order_status(org_id: str, order_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    update = {"status": data["status"]}
    if data.get("progress_percent"): update["progress_percent"] = data["progress_percent"]
    if data["status"] == "delivered": update["actual_delivery_date"] = str(date.today())
    db.table("custom_orders").update(update).eq("id", order_id).eq("organization_id", org_id).execute()
    return {"message": f"Status updated to {data['status']}"}

@router.get("/measurements/{phone}")
async def get_measurements(org_id: str, phone: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("customer_measurements").select("*").eq("organization_id", org_id).eq("customer_phone", phone).execute()
    return {"measurements": result.data}

@router.post("/measurements")
async def save_measurements(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    db.table("customer_measurements").upsert({
        "organization_id": org_id,
        "customer_name": data["customer_name"],
        "customer_phone": data["customer_phone"],
        "measurement_type": data.get("measurement_type", "body"),
        "data": data["data"],
        "notes": data.get("notes"),
        "updated_at": "now()",
    }).execute()
    return {"message": "Measurements saved"}

@router.get("/designs")
async def list_designs(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("design_catalog").select("*").eq("organization_id", org_id).eq("is_active", True).order("sort_order").execute()
    return {"designs": result.data}

@router.post("/designs")
async def add_design(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("design_catalog").insert({
        "organization_id": org_id, "name": data["name"],
        "category": data.get("category"), "images": data.get("images", []),
        "description": data.get("description"), "base_price": data.get("base_price"),
    }).execute()
    return {"design": result.data[0], "message": "Design added"}

@router.get("/dashboard")
async def custom_orders_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    orders = db.table("custom_orders").select("status, total_price, balance_due, promised_date").eq("organization_id", org_id).execute()
    total = len(orders.data)
    in_progress = sum(1 for o in orders.data if o["status"] not in ("delivered", "cancelled"))
    overdue = sum(1 for o in orders.data if o.get("promised_date") and o["promised_date"] < str(date.today()) and o["status"] not in ("delivered", "cancelled"))
    revenue = sum(float(o.get("total_price", 0) or 0) for o in orders.data if o["status"] == "delivered")
    pending_payment = sum(float(o.get("balance_due", 0) or 0) for o in orders.data if o["status"] not in ("cancelled",))
    return {"total_orders": total, "in_progress": in_progress, "overdue": overdue, "revenue": revenue, "pending_payment": pending_payment}
