from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/org/{org_id}/property", tags=["property"])


async def check_property_access(org_id: str):
    supabase = get_supabase()
    result = supabase.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "property").single().execute()
    if not result.data or not result.data.get("enabled"):
        raise HTTPException(403, "Property module not enabled for this organization")


@router.get("/buildings")
async def list_buildings(org_id: str):
    await check_property_access(org_id)
    db = get_supabase()
    result = db.table("property_buildings").select("*").eq("organization_id", org_id).execute()
    return {"buildings": result.data}


@router.post("/buildings")
async def create_building(org_id: str, data: dict):
    await check_property_access(org_id)
    db = get_supabase()
    result = db.table("property_buildings").insert({
        "organization_id": org_id,
        "name": data["name"],
        "address": data.get("address"),
        "type": data.get("type", "pg"),
        "total_rooms": data.get("total_rooms", 0),
        "amenities": data.get("amenities", []),
    }).execute()
    return {"building": result.data[0], "message": "Building created"}


@router.get("/rooms")
async def list_rooms(org_id: str, building_id: Optional[str] = None, status: Optional[str] = None):
    await check_property_access(org_id)
    db = get_supabase()
    query = db.table("property_rooms").select("*, property_buildings(name)").eq("organization_id", org_id)
    if building_id:
        query = query.eq("building_id", building_id)
    if status:
        query = query.eq("status", status)
    result = query.order("name").execute()
    return {"rooms": result.data}


@router.post("/rooms")
async def create_room(org_id: str, data: dict):
    await check_property_access(org_id)
    db = get_supabase()
    result = db.table("property_rooms").insert({
        "organization_id": org_id,
        "building_id": data["building_id"],
        "name": data["name"],
        "floor": data.get("floor"),
        "room_type": data.get("room_type", "single"),
        "capacity": data.get("capacity", 1),
        "rent_amount": data.get("rent_amount", 0),
        "deposit_amount": data.get("deposit_amount", 0),
        "amenities": data.get("amenities", []),
    }).execute()
    return {"room": result.data[0], "message": "Room created"}


@router.put("/rooms/{room_id}")
async def update_room(org_id: str, room_id: str, data: dict):
    await check_property_access(org_id)
    db = get_supabase()
    allowed = ["name", "floor", "room_type", "capacity", "rent_amount", "deposit_amount", "status", "amenities"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    result = db.table("property_rooms").update(update_data).eq("id", room_id).eq("organization_id", org_id).execute()
    return {"room": result.data[0] if result.data else None, "message": "Updated"}


@router.get("/tenants")
async def list_tenants(org_id: str, status: Optional[str] = None):
    await check_property_access(org_id)
    db = get_supabase()
    query = db.table("property_tenants").select("*, property_rooms(name, property_buildings(name))").eq("organization_id", org_id)
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return {"tenants": result.data}


@router.post("/tenants")
async def create_tenant(org_id: str, data: dict):
    await check_property_access(org_id)
    db = get_supabase()
    
    tenant = db.table("property_tenants").insert({
        "organization_id": org_id,
        "room_id": data.get("room_id"),
        "name": data["name"],
        "phone": data.get("phone"),
        "email": data.get("email"),
        "id_proof_type": data.get("id_proof_type"),
        "id_proof_number": data.get("id_proof_number"),
        "emergency_contact": data.get("emergency_contact"),
        "move_in_date": data.get("move_in_date"),
        "rent_amount": data.get("rent_amount"),
        "deposit_paid": data.get("deposit_paid", 0),
    }).execute()
    
    # Mark room as occupied
    if data.get("room_id"):
        db.table("property_rooms").update({"status": "occupied"}).eq("id", data["room_id"]).execute()
    
    return {"tenant": tenant.data[0], "message": "Tenant added"}


@router.post("/rent-payments")
async def record_rent(org_id: str, data: dict):
    await check_property_access(org_id)
    db = get_supabase()
    result = db.table("property_rent_payments").insert({
        "organization_id": org_id,
        "tenant_id": data["tenant_id"],
        "amount": data["amount"],
        "month": data["month"],
        "year": data["year"],
        "status": data.get("status", "paid"),
        "payment_date": data.get("payment_date"),
        "method": data.get("method"),
    }).execute()
    return {"payment": result.data[0], "message": "Rent recorded"}


@router.get("/rent-payments")
async def list_rent_payments(org_id: str, tenant_id: Optional[str] = None, month: Optional[str] = None):
    await check_property_access(org_id)
    db = get_supabase()
    query = db.table("property_rent_payments").select("*, property_tenants(name, phone)").eq("organization_id", org_id)
    if tenant_id:
        query = query.eq("tenant_id", tenant_id)
    if month:
        query = query.eq("month", month)
    result = query.order("created_at", desc=True).execute()
    return {"payments": result.data}


@router.get("/complaints")
async def list_complaints(org_id: str, status: Optional[str] = None):
    await check_property_access(org_id)
    db = get_supabase()
    query = db.table("property_complaints").select("*, property_tenants(name), property_rooms(name)").eq("organization_id", org_id)
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return {"complaints": result.data}


@router.post("/complaints")
async def create_complaint(org_id: str, data: dict):
    await check_property_access(org_id)
    db = get_supabase()
    result = db.table("property_complaints").insert({
        "organization_id": org_id,
        "tenant_id": data.get("tenant_id"),
        "room_id": data.get("room_id"),
        "title": data["title"],
        "description": data.get("description"),
        "category": data.get("category", "general"),
        "priority": data.get("priority", "medium"),
    }).execute()
    return {"complaint": result.data[0], "message": "Complaint registered"}


@router.get("/dashboard")
async def property_dashboard(org_id: str):
    await check_property_access(org_id)
    db = get_supabase()
    
    rooms = db.table("property_rooms").select("status").eq("organization_id", org_id).execute()
    tenants = db.table("property_tenants").select("id", count="exact").eq("organization_id", org_id).eq("status", "active").execute()
    complaints = db.table("property_complaints").select("status").eq("organization_id", org_id).execute()
    
    total_rooms = len(rooms.data)
    occupied = sum(1 for r in rooms.data if r["status"] == "occupied")
    available = sum(1 for r in rooms.data if r["status"] == "available")
    open_complaints = sum(1 for c in complaints.data if c["status"] in ("open", "in_progress"))
    
    return {
        "total_rooms": total_rooms,
        "occupied": occupied,
        "available": available,
        "occupancy_rate": round(occupied / total_rooms * 100, 1) if total_rooms > 0 else 0,
        "active_tenants": tenants.count,
        "open_complaints": open_complaints,
    }
