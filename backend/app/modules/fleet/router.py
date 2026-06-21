from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date, datetime

router = APIRouter(prefix="/api/org/{org_id}/fleet", tags=["fleet"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "fleet").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "Fleet module not enabled")

@router.get("/vehicles")
async def list_vehicles(org_id: str, status: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("fleet_vehicles").select("*").eq("organization_id", org_id)
    if status: query = query.eq("status", status)
    return {"vehicles": query.execute().data}

@router.post("/vehicles")
async def add_vehicle(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("fleet_vehicles").insert({
        "organization_id": org_id, "vehicle_number": data["vehicle_number"],
        "type": data.get("type", "car"), "make": data.get("make"), "model": data.get("model"),
        "year": data.get("year"), "color": data.get("color"), "fuel_type": data.get("fuel_type", "petrol"),
        "insurance_expiry": data.get("insurance_expiry"), "puc_expiry": data.get("puc_expiry"),
        "odometer": data.get("odometer", 0),
    }).execute()
    return {"vehicle": result.data[0], "message": "Vehicle added"}

@router.get("/drivers")
async def list_drivers(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    return {"drivers": db.table("fleet_drivers").select("*").eq("organization_id", org_id).execute().data}

@router.post("/drivers")
async def add_driver(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("fleet_drivers").insert({
        "organization_id": org_id, "name": data["name"], "phone": data.get("phone"),
        "license_number": data.get("license_number"), "license_expiry": data.get("license_expiry"),
    }).execute()
    return {"driver": result.data[0], "message": "Driver added"}

@router.get("/trips")
async def list_trips(org_id: str, status: Optional[str] = None, limit: int = Query(default=50)):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("fleet_trips").select("*, fleet_vehicles(vehicle_number), fleet_drivers(name)").eq("organization_id", org_id)
    if status: query = query.eq("status", status)
    return {"trips": query.order("created_at", desc=True).limit(limit).execute().data}

@router.post("/trips")
async def create_trip(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("fleet_trips").insert({
        "organization_id": org_id, "vehicle_id": data.get("vehicle_id"),
        "driver_id": data.get("driver_id"), "customer_name": data.get("customer_name"),
        "customer_phone": data.get("customer_phone"),
        "pickup_location": data.get("pickup_location"), "drop_location": data.get("drop_location"),
        "scheduled_at": data.get("scheduled_at"), "fare": data.get("fare"),
    }).execute()
    # Update vehicle/driver status
    if data.get("vehicle_id"): db.table("fleet_vehicles").update({"status": "on_trip"}).eq("id", data["vehicle_id"]).execute()
    if data.get("driver_id"): db.table("fleet_drivers").update({"status": "on_trip"}).eq("id", data["driver_id"]).execute()
    return {"trip": result.data[0], "message": "Trip created"}

@router.put("/trips/{trip_id}/complete")
async def complete_trip(org_id: str, trip_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    trip = db.table("fleet_trips").select("vehicle_id, driver_id").eq("id", trip_id).single().execute()
    db.table("fleet_trips").update({"status": "completed", "completed_at": datetime.utcnow().isoformat(), "distance_km": data.get("distance_km"), "fare": data.get("fare"), "payment_status": data.get("payment_status", "paid")}).eq("id", trip_id).execute()
    if trip.data:
        if trip.data.get("vehicle_id"): db.table("fleet_vehicles").update({"status": "available"}).eq("id", trip.data["vehicle_id"]).execute()
        if trip.data.get("driver_id"): db.table("fleet_drivers").update({"status": "available"}).eq("id", trip.data["driver_id"]).execute()
    return {"message": "Trip completed"}

@router.post("/maintenance")
async def add_maintenance(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("fleet_maintenance").insert({
        "organization_id": org_id, "vehicle_id": data["vehicle_id"],
        "type": data.get("type", "service"), "description": data.get("description"),
        "cost": data.get("cost", 0), "vendor": data.get("vendor"),
        "odometer_at_service": data.get("odometer"), "next_service_due_date": data.get("next_service_due_date"),
    }).execute()
    return {"maintenance": result.data[0], "message": "Maintenance logged"}

@router.post("/fuel")
async def add_fuel(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("fleet_fuel").insert({
        "organization_id": org_id, "vehicle_id": data["vehicle_id"],
        "liters": data["liters"], "amount": data["amount"],
        "odometer": data.get("odometer"), "fuel_station": data.get("fuel_station"),
    }).execute()
    return {"fuel": result.data[0], "message": "Fuel entry added"}

@router.get("/dashboard")
async def fleet_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    vehicles = db.table("fleet_vehicles").select("status").eq("organization_id", org_id).execute()
    trips = db.table("fleet_trips").select("status, fare").eq("organization_id", org_id).execute()
    total_vehicles = len(vehicles.data)
    available = sum(1 for v in vehicles.data if v["status"] == "available")
    on_trip = sum(1 for v in vehicles.data if v["status"] == "on_trip")
    total_revenue = sum(float(t.get("fare", 0) or 0) for t in trips.data if t["status"] == "completed")
    return {"total_vehicles": total_vehicles, "available": available, "on_trip": on_trip, "total_trips": len(trips.data), "revenue": total_revenue}
