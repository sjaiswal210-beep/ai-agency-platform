from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date, datetime, timedelta

router = APIRouter(prefix="/api/org/{org_id}/subscriptions", tags=["subscriptions"])


async def check_access(org_id: str):
    db = get_supabase()
    result = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "subscriptions").single().execute()
    if not result.data or not result.data.get("enabled"):
        raise HTTPException(403, "Subscription module not enabled")


# ============ PRODUCTS ============

@router.get("/products")
async def list_products(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("subscription_products").select("*").eq("organization_id", org_id).execute()
    return {"products": result.data}


@router.post("/products")
async def create_product(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("subscription_products").insert({
        "organization_id": org_id,
        "name": data["name"],
        "unit": data.get("unit", "pcs"),
        "price": data["price"],
        "category": data.get("category"),
    }).execute()
    return {"product": result.data[0], "message": "Product created"}


# ============ SUBSCRIPTIONS ============

@router.get("/")
async def list_subscriptions(org_id: str, status: Optional[str] = None, route_id: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("subscriptions").select("*, subscription_products(name, unit)").eq("organization_id", org_id)
    if status:
        query = query.eq("status", status)
    if route_id:
        query = query.eq("route_id", route_id)
    result = query.order("route_sequence").execute()
    return {"subscriptions": result.data, "count": len(result.data)}


@router.post("/")
async def create_subscription(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    
    price = float(data.get("price_per_unit", 0))
    qty = float(data.get("quantity", 1))
    freq = data.get("frequency", "daily")
    days_per_month = 30 if freq == "daily" else 15 if freq == "alternate" else 22 if freq == "weekdays" else 30
    monthly = price * qty * days_per_month
    
    result = db.table("subscriptions").insert({
        "organization_id": org_id,
        "customer_name": data["customer_name"],
        "customer_phone": data["customer_phone"],
        "address": data.get("address"),
        "locality": data.get("locality"),
        "product_id": data.get("product_id"),
        "product_name": data.get("product_name"),
        "quantity": qty,
        "frequency": freq,
        "custom_days": data.get("custom_days", []),
        "price_per_unit": price,
        "monthly_estimate": monthly,
        "route_id": data.get("route_id"),
        "route_sequence": data.get("route_sequence", 0),
        "delivery_boy_id": data.get("delivery_boy_id"),
        "notes": data.get("notes"),
    }).execute()
    return {"subscription": result.data[0], "message": "Subscription created"}


@router.put("/{sub_id}")
async def update_subscription(org_id: str, sub_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    allowed = ["customer_name", "customer_phone", "address", "locality", "product_id", "product_name", "quantity", "frequency", "custom_days", "price_per_unit", "route_id", "route_sequence", "delivery_boy_id", "status", "notes"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    result = db.table("subscriptions").update(update_data).eq("id", sub_id).eq("organization_id", org_id).execute()
    return {"subscription": result.data[0] if result.data else None, "message": "Updated"}


@router.post("/{sub_id}/pause")
async def pause_subscription(org_id: str, sub_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    db.table("subscriptions").update({
        "status": "paused",
        "pause_from": data.get("from", str(date.today())),
        "pause_until": data.get("until"),
    }).eq("id", sub_id).eq("organization_id", org_id).execute()
    return {"message": "Subscription paused"}


@router.post("/{sub_id}/resume")
async def resume_subscription(org_id: str, sub_id: str):
    await check_access(org_id)
    db = get_supabase()
    db.table("subscriptions").update({
        "status": "active",
        "pause_from": None,
        "pause_until": None,
    }).eq("id", sub_id).eq("organization_id", org_id).execute()
    return {"message": "Subscription resumed"}


# ============ TODAY'S DELIVERIES ============

@router.get("/today")
async def todays_deliveries(org_id: str, route_id: Optional[str] = None):
    """Get today's delivery list based on active subscriptions and their frequency."""
    await check_access(org_id)
    db = get_supabase()
    today = date.today()
    day_name = today.strftime("%A").lower()  # monday, tuesday...
    
    query = db.table("subscriptions").select("*, subscription_products(name, unit)").eq("organization_id", org_id).eq("status", "active")
    if route_id:
        query = query.eq("route_id", route_id)
    
    subs = query.order("route_sequence").execute()
    
    # Check which have already been marked today
    delivered_today = db.table("subscription_deliveries").select("subscription_id, status").eq("organization_id", org_id).eq("date", str(today)).execute()
    delivered_map = {d["subscription_id"]: d["status"] for d in (delivered_today.data or [])}
    
    deliveries = []
    for sub in (subs.data or []):
        # Check if delivery is due today based on frequency
        freq = sub.get("frequency", "daily")
        should_deliver = False
        
        if freq == "daily":
            should_deliver = True
        elif freq == "alternate":
            # Simple: deliver on odd days of month
            should_deliver = today.day % 2 == 1
        elif freq == "weekdays":
            should_deliver = today.weekday() < 5  # Mon-Fri
        elif freq == "custom":
            custom_days = sub.get("custom_days", [])
            should_deliver = day_name in [d.lower() for d in custom_days]
        elif freq == "weekly":
            # Deliver on start day of week
            should_deliver = today.weekday() == 0  # Monday
        
        # Check if paused
        if sub.get("pause_from") and sub.get("pause_until"):
            pause_from = date.fromisoformat(sub["pause_from"]) if isinstance(sub["pause_from"], str) else sub["pause_from"]
            pause_until = date.fromisoformat(sub["pause_until"]) if isinstance(sub["pause_until"], str) else sub["pause_until"]
            if pause_from <= today <= pause_until:
                should_deliver = False
        
        if should_deliver:
            deliveries.append({
                **sub,
                "delivery_status": delivered_map.get(sub["id"], "pending"),
            })
    
    return {"date": str(today), "deliveries": deliveries, "total": len(deliveries)}


@router.post("/mark-delivery")
async def mark_delivery(org_id: str, data: dict):
    """Mark a delivery as done/skipped for today."""
    await check_access(org_id)
    db = get_supabase()
    
    db.table("subscription_deliveries").upsert({
        "organization_id": org_id,
        "subscription_id": data["subscription_id"],
        "date": data.get("date", str(date.today())),
        "quantity": data.get("quantity"),
        "status": data.get("status", "delivered"),
        "delivery_boy_id": data.get("delivery_boy_id"),
        "delivered_at": datetime.utcnow().isoformat() if data.get("status") == "delivered" else None,
        "notes": data.get("notes"),
    }).execute()
    
    return {"message": "Delivery marked"}


# ============ BILLING ============

@router.post("/generate-bills")
async def generate_monthly_bills(org_id: str, data: dict):
    """Generate bills for all active subscriptions for a given month."""
    await check_access(org_id)
    db = get_supabase()
    
    month = data.get("month", date.today().month)
    year = data.get("year", date.today().year)
    
    # Get all active subscriptions
    subs = db.table("subscriptions").select("*").eq("organization_id", org_id).neq("status", "cancelled").execute()
    
    generated = 0
    for sub in (subs.data or []):
        # Count deliveries for this month
        deliveries = db.table("subscription_deliveries").select("quantity, status").eq("subscription_id", sub["id"]).gte("date", f"{year}-{month:02d}-01").lte("date", f"{year}-{month:02d}-31").execute()
        
        total_delivered = sum(float(d.get("quantity", sub.get("quantity", 1)) or 1) for d in (deliveries.data or []) if d["status"] == "delivered")
        extras = sum(float(d.get("quantity", 0) or 0) for d in (deliveries.data or []) if d["status"] == "extra")
        
        rate = float(sub.get("price_per_unit", 0) or 0)
        subtotal = total_delivered * rate
        extras_amount = extras * rate
        final = subtotal + extras_amount
        
        if final > 0:
            db.table("subscription_bills").upsert({
                "organization_id": org_id,
                "subscription_id": sub["id"],
                "customer_name": sub["customer_name"],
                "customer_phone": sub["customer_phone"],
                "month": month,
                "year": year,
                "total_deliveries": int(total_delivered),
                "total_quantity": total_delivered,
                "rate": rate,
                "subtotal": subtotal,
                "extras_amount": extras_amount,
                "deductions": 0,
                "final_amount": final,
                "status": "generated",
            }).execute()
            generated += 1
    
    return {"message": f"Bills generated for {month}/{year}", "generated": generated}


@router.get("/bills")
async def list_bills(org_id: str, month: Optional[int] = None, year: Optional[int] = None, status: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("subscription_bills").select("*").eq("organization_id", org_id)
    if month:
        query = query.eq("month", month)
    if year:
        query = query.eq("year", year)
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return {"bills": result.data}


@router.post("/bills/{bill_id}/pay")
async def mark_bill_paid(org_id: str, bill_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    db.table("subscription_bills").update({
        "status": "paid",
        "paid_amount": data.get("amount"),
        "paid_date": data.get("date", str(date.today())),
        "payment_method": data.get("method", "cash"),
    }).eq("id", bill_id).eq("organization_id", org_id).execute()
    return {"message": "Bill marked as paid"}


# ============ ROUTES ============

@router.get("/routes")
async def list_routes(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("subscription_routes").select("*").eq("organization_id", org_id).execute()
    return {"routes": result.data}


@router.post("/routes")
async def create_route(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("subscription_routes").insert({
        "organization_id": org_id,
        "name": data["name"],
        "area": data.get("area"),
        "delivery_boy_name": data.get("delivery_boy_name"),
        "delivery_boy_phone": data.get("delivery_boy_phone"),
    }).execute()
    return {"route": result.data[0], "message": "Route created"}


# ============ DASHBOARD ============

@router.get("/dashboard")
async def subscription_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    
    subs = db.table("subscriptions").select("status, monthly_estimate").eq("organization_id", org_id).execute()
    bills = db.table("subscription_bills").select("status, final_amount, paid_amount").eq("organization_id", org_id).execute()
    
    active = sum(1 for s in subs.data if s["status"] == "active")
    paused = sum(1 for s in subs.data if s["status"] == "paused")
    monthly_revenue = sum(float(s.get("monthly_estimate", 0) or 0) for s in subs.data if s["status"] == "active")
    pending_bills = sum(float(b.get("final_amount", 0) or 0) - float(b.get("paid_amount", 0) or 0) for b in bills.data if b["status"] not in ("paid",))
    
    return {
        "active_subscriptions": active,
        "paused_subscriptions": paused,
        "monthly_revenue_estimate": monthly_revenue,
        "pending_collections": pending_bills,
        "total_customers": active + paused,
    }
