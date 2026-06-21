from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/org/{org_id}/inventory", tags=["inventory"])


async def check_inventory_access(org_id: str):
    supabase = get_supabase()
    result = supabase.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "inventory").single().execute()
    if not result.data or not result.data.get("enabled"):
        raise HTTPException(403, "Inventory module not enabled for this organization")


@router.get("/products")
async def list_products(
    org_id: str,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    low_stock: Optional[bool] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0
):
    await check_inventory_access(org_id)
    db = get_supabase()
    query = db.table("inventory_products").select("*, inventory_categories(name)").eq("organization_id", org_id).eq("is_active", True)
    
    if category_id:
        query = query.eq("category_id", category_id)
    if search:
        query = query.or_(f"name.ilike.%{search}%,sku.ilike.%{search}%")
    if low_stock:
        query = query.lt("stock_quantity", 5)  # Will use threshold later
    
    result = query.order("name").range(offset, offset + limit - 1).execute()
    return {"products": result.data, "count": len(result.data)}


@router.post("/products")
async def create_product(org_id: str, data: dict):
    await check_inventory_access(org_id)
    db = get_supabase()
    
    product_data = {
        "organization_id": org_id,
        "name": data["name"],
        "sku": data.get("sku"),
        "description": data.get("description"),
        "category_id": data.get("category_id"),
        "price": data.get("price", 0),
        "cost_price": data.get("cost_price", 0),
        "unit": data.get("unit", "pcs"),
        "stock_quantity": data.get("stock_quantity", 0),
        "low_stock_threshold": data.get("low_stock_threshold", 5),
        "barcode": data.get("barcode"),
        "image_url": data.get("image_url"),
    }
    
    result = db.table("inventory_products").insert(product_data).execute()
    return {"product": result.data[0], "message": "Product created"}


@router.put("/products/{product_id}")
async def update_product(org_id: str, product_id: str, data: dict):
    await check_inventory_access(org_id)
    db = get_supabase()
    allowed = ["name", "sku", "description", "category_id", "price", "cost_price", "unit", "stock_quantity", "low_stock_threshold", "barcode", "image_url", "is_active"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    
    result = db.table("inventory_products").update(update_data).eq("id", product_id).eq("organization_id", org_id).execute()
    if not result.data:
        raise HTTPException(404, "Product not found")
    return {"product": result.data[0], "message": "Updated"}


@router.post("/products/{product_id}/stock")
async def adjust_stock(org_id: str, product_id: str, data: dict):
    """Add or remove stock. type: purchase/sale/adjustment/return"""
    await check_inventory_access(org_id)
    db = get_supabase()
    
    quantity = data["quantity"]
    move_type = data.get("type", "adjustment")
    
    # Record movement
    db.table("inventory_movements").insert({
        "organization_id": org_id,
        "product_id": product_id,
        "type": move_type,
        "quantity": quantity,
        "unit_price": data.get("unit_price"),
        "supplier_id": data.get("supplier_id"),
        "reference": data.get("reference"),
        "notes": data.get("notes"),
    }).execute()
    
    # Update stock
    product = db.table("inventory_products").select("stock_quantity").eq("id", product_id).eq("organization_id", org_id).single().execute()
    if not product.data:
        raise HTTPException(404, "Product not found")
    
    current = product.data["stock_quantity"] or 0
    if move_type in ("purchase", "return"):
        new_qty = current + abs(quantity)
    elif move_type == "sale":
        new_qty = current - abs(quantity)
    else:
        new_qty = current + quantity  # adjustment can be +/-
    
    db.table("inventory_products").update({"stock_quantity": max(0, new_qty)}).eq("id", product_id).execute()
    
    return {"message": f"Stock updated: {current} -> {new_qty}", "new_quantity": max(0, new_qty)}


@router.get("/categories")
async def list_categories(org_id: str):
    await check_inventory_access(org_id)
    db = get_supabase()
    result = db.table("inventory_categories").select("*").eq("organization_id", org_id).order("sort_order").execute()
    return {"categories": result.data}


@router.post("/categories")
async def create_category(org_id: str, data: dict):
    await check_inventory_access(org_id)
    db = get_supabase()
    result = db.table("inventory_categories").insert({
        "organization_id": org_id,
        "name": data["name"],
        "parent_id": data.get("parent_id"),
    }).execute()
    return {"category": result.data[0], "message": "Category created"}


@router.get("/suppliers")
async def list_suppliers(org_id: str):
    await check_inventory_access(org_id)
    db = get_supabase()
    result = db.table("inventory_suppliers").select("*").eq("organization_id", org_id).execute()
    return {"suppliers": result.data}


@router.post("/suppliers")
async def create_supplier(org_id: str, data: dict):
    await check_inventory_access(org_id)
    db = get_supabase()
    result = db.table("inventory_suppliers").insert({
        "organization_id": org_id,
        "name": data["name"],
        "phone": data.get("phone"),
        "email": data.get("email"),
        "address": data.get("address"),
        "gst_number": data.get("gst_number"),
        "notes": data.get("notes"),
    }).execute()
    return {"supplier": result.data[0], "message": "Supplier created"}


@router.get("/movements")
async def list_movements(org_id: str, product_id: Optional[str] = None, limit: int = Query(default=50, le=200)):
    await check_inventory_access(org_id)
    db = get_supabase()
    query = db.table("inventory_movements").select("*, inventory_products(name), inventory_suppliers(name)").eq("organization_id", org_id)
    if product_id:
        query = query.eq("product_id", product_id)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return {"movements": result.data}


@router.get("/dashboard")
async def inventory_dashboard(org_id: str):
    await check_inventory_access(org_id)
    db = get_supabase()
    
    products = db.table("inventory_products").select("stock_quantity, price, cost_price, low_stock_threshold").eq("organization_id", org_id).eq("is_active", True).execute()
    
    total_products = len(products.data)
    total_stock_value = sum(float(p["stock_quantity"] or 0) * float(p["cost_price"] or 0) for p in products.data)
    low_stock_count = sum(1 for p in products.data if (p["stock_quantity"] or 0) <= (p["low_stock_threshold"] or 5))
    out_of_stock = sum(1 for p in products.data if (p["stock_quantity"] or 0) == 0)
    
    return {
        "total_products": total_products,
        "total_stock_value": total_stock_value,
        "low_stock_count": low_stock_count,
        "out_of_stock": out_of_stock,
    }
