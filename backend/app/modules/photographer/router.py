from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from app.core.supabase import get_supabase
import random, string

router = APIRouter(prefix="/api/photo/{website_id}", tags=["photographer"])


def get_org_id(website_id: str):
    db = get_supabase()
    website = db.table("websites").select("slug").eq("id", website_id).single().execute()
    if not website.data:
        raise HTTPException(404, "Website not found")
    slug = website.data.get("slug", "")
    org = db.table("organizations").select("id").eq("slug", slug).single().execute()
    if not org.data:
        raise HTTPException(404, "Organization not found")
    return org.data["id"]


# ============ PORTFOLIO ============

@router.get("/portfolio")
async def list_albums(website_id: str):
    org_id = get_org_id(website_id)
    db = get_supabase()
    albums = db.table("photo_albums").select("*, photo_portfolio(count)").eq("organization_id", org_id).order("sort_order").execute()
    return {"albums": albums.data}


@router.post("/portfolio/albums")
async def create_album(website_id: str, data: dict):
    org_id = get_org_id(website_id)
    db = get_supabase()
    result = db.table("photo_albums").insert({
        "organization_id": org_id,
        "title": data["title"],
        "description": data.get("description"),
        "category": data.get("category", "wedding"),
        "cover_url": data.get("cover_url"),
        "is_public": data.get("is_public", True),
    }).execute()
    return {"album": result.data[0], "message": "Album created"}


@router.post("/portfolio/photos")
async def add_photos(website_id: str, data: dict):
    org_id = get_org_id(website_id)
    db = get_supabase()
    photos = data.get("photos", [])
    album_id = data.get("album_id")
    added = 0
    for url in photos:
        if url and url.strip():
            db.table("photo_portfolio").insert({
                "organization_id": org_id,
                "album_id": album_id,
                "url": url.strip(),
                "is_featured": data.get("is_featured", False),
            }).execute()
            added += 1
    return {"message": f"{added} photos added"}


# ============ EVENTS/SHOOTS ============

@router.get("/calendar")
async def list_events(website_id: str, status: Optional[str] = None):
    org_id = get_org_id(website_id)
    db = get_supabase()
    query = db.table("photo_events").select("*").eq("organization_id", org_id)
    if status:
        query = query.eq("status", status)
    result = query.order("event_date", desc=True).execute()
    return {"events": result.data}


@router.post("/calendar")
async def create_event(website_id: str, data: dict):
    org_id = get_org_id(website_id)
    db = get_supabase()
    total = float(data.get("total_amount", 0))
    advance = float(data.get("advance_paid", 0))
    result = db.table("photo_events").insert({
        "organization_id": org_id,
        "client_name": data["client_name"],
        "client_phone": data.get("client_phone"),
        "client_email": data.get("client_email"),
        "event_type": data.get("event_type", "wedding"),
        "event_date": data["event_date"],
        "event_time": data.get("event_time"),
        "venue": data.get("venue"),
        "duration_hours": data.get("duration_hours", 4),
        "package_id": data.get("package_id"),
        "status": data.get("status", "confirmed"),
        "total_amount": total,
        "advance_paid": advance,
        "balance_due": total - advance,
        "notes": data.get("notes"),
        "crew_members": data.get("crew_members"),
        "equipment_needed": data.get("equipment_needed"),
    }).execute()
    return {"event": result.data[0], "message": "Shoot booked"}


@router.put("/calendar/{event_id}")
async def update_event(website_id: str, event_id: str, data: dict):
    org_id = get_org_id(website_id)
    db = get_supabase()
    allowed = ["client_name", "client_phone", "event_type", "event_date", "event_time", "venue", "duration_hours", "status", "total_amount", "advance_paid", "balance_due", "notes", "crew_members", "equipment_needed"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    if "total_amount" in update_data and "advance_paid" in update_data:
        update_data["balance_due"] = float(update_data["total_amount"]) - float(update_data["advance_paid"])
    result = db.table("photo_events").update(update_data).eq("id", event_id).eq("organization_id", org_id).execute()
    return {"event": result.data[0] if result.data else None, "message": "Updated"}


# ============ PACKAGES ============

@router.get("/packages")
async def list_packages(website_id: str):
    org_id = get_org_id(website_id)
    db = get_supabase()
    result = db.table("photo_packages").select("*").eq("organization_id", org_id).order("sort_order").execute()
    return {"packages": result.data}


@router.post("/packages")
async def create_package(website_id: str, data: dict):
    org_id = get_org_id(website_id)
    db = get_supabase()
    result = db.table("photo_packages").insert({
        "organization_id": org_id,
        "name": data["name"],
        "description": data.get("description"),
        "category": data.get("category", "wedding"),
        "price": data["price"],
        "duration_hours": data.get("duration_hours", 4),
        "deliverables": data.get("deliverables"),
        "includes": data.get("includes", []),
    }).execute()
    return {"package": result.data[0], "message": "Package created"}


# ============ CLIENT DELIVERY ============

@router.get("/delivery")
async def list_deliveries(website_id: str):
    org_id = get_org_id(website_id)
    db = get_supabase()
    result = db.table("photo_deliveries").select("*").eq("organization_id", org_id).order("created_at", desc=True).execute()
    return {"deliveries": result.data}


@router.post("/delivery")
async def create_delivery(website_id: str, data: dict):
    org_id = get_org_id(website_id)
    db = get_supabase()
    code = ''.join(random.choices(string.digits, k=6))
    result = db.table("photo_deliveries").insert({
        "organization_id": org_id,
        "event_id": data.get("event_id"),
        "client_name": data["client_name"],
        "client_phone": data.get("client_phone"),
        "access_code": code,
        "title": data["title"],
        "photos": data.get("photos", []),
        "photo_count": len(data.get("photos", [])),
        "download_enabled": data.get("download_enabled", True),
        "watermark_enabled": data.get("watermark_enabled", False),
    }).execute()
    return {"delivery": result.data[0], "access_code": code, "message": f"Gallery created. Share code: {code}"}


@router.get("/delivery/view/{access_code}", response_class=HTMLResponse)
async def view_delivery(website_id: str, access_code: str):
    """Public client gallery view - accessed via code."""
    db = get_supabase()
    result = db.table("photo_deliveries").select("*").eq("access_code", access_code).eq("is_active", True).single().execute()
    if not result.data:
        return HTMLResponse("<h1>Gallery not found or expired</h1>", status_code=404)
    
    delivery = result.data
    photos = delivery.get("photos", [])
    
    # Increment view count
    db.table("photo_deliveries").update({"view_count": (delivery.get("view_count", 0) or 0) + 1}).eq("id", delivery["id"]).execute()
    
    photo_grid = "".join([f'<div class="photo"><img src="{p}" loading="lazy" onclick="openFull(this.src)"></div>' for p in photos if p])
    
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{delivery['title']}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;background:#000;color:#fff;min-height:100vh}}
.header{{padding:20px;text-align:center;border-bottom:1px solid #222}}
.header h1{{font-size:1.2rem;margin-bottom:4px}}
.header p{{font-size:.75rem;color:#888}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:2px;padding:2px}}
.photo{{aspect-ratio:1;overflow:hidden;cursor:pointer}}
.photo img{{width:100%;height:100%;object-fit:cover;transition:transform .2s}}
.photo img:hover{{transform:scale(1.05)}}
.fullscreen{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.95);z-index:999;align-items:center;justify-content:center}}
.fullscreen img{{max-width:95%;max-height:90vh;object-fit:contain}}
.fullscreen .close{{position:absolute;top:16px;right:16px;color:#fff;font-size:2rem;cursor:pointer;background:none;border:none}}
.footer{{padding:16px;text-align:center;font-size:.7rem;color:#555}}
@media(min-width:768px){{.grid{{grid-template-columns:repeat(4,1fr)}}}}
</style></head><body>
<div class="header">
<h1>{delivery['title']}</h1>
<p>{delivery['client_name']} &middot; {delivery.get('photo_count', len(photos))} photos</p>
</div>
<div class="grid">{photo_grid}</div>
<div class="footer">Powered by City Maps</div>
<div class="fullscreen" id="fs" onclick="this.style.display='none'">
<button class="close">&times;</button>
<img id="fsImg">
</div>
<script>
function openFull(src){{document.getElementById('fsImg').src=src;document.getElementById('fs').style.display='flex';}}
</script>
</body></html>"""
    return HTMLResponse(content=html)


# ============ ENQUIRIES ============

@router.get("/enquiries")
async def list_enquiries(website_id: str, status: Optional[str] = None):
    org_id = get_org_id(website_id)
    db = get_supabase()
    query = db.table("photo_enquiries").select("*").eq("organization_id", org_id)
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return {"enquiries": result.data}


@router.post("/enquiries")
async def create_enquiry(website_id: str, data: dict):
    """Can be called from website contact form."""
    org_id = get_org_id(website_id)
    db = get_supabase()
    result = db.table("photo_enquiries").insert({
        "organization_id": org_id,
        "name": data["name"],
        "phone": data.get("phone"),
        "email": data.get("email"),
        "event_type": data.get("event_type"),
        "event_date": data.get("event_date"),
        "venue": data.get("venue"),
        "budget": data.get("budget"),
        "message": data.get("message"),
        "source": data.get("source", "website"),
    }).execute()
    return {"enquiry": result.data[0], "message": "Enquiry received"}


@router.put("/enquiries/{enquiry_id}")
async def update_enquiry(website_id: str, enquiry_id: str, data: dict):
    org_id = get_org_id(website_id)
    db = get_supabase()
    result = db.table("photo_enquiries").update({"status": data["status"]}).eq("id", enquiry_id).eq("organization_id", org_id).execute()
    return {"message": "Updated"}


# ============ EQUIPMENT ============

@router.get("/equipment")
async def list_equipment(website_id: str):
    org_id = get_org_id(website_id)
    db = get_supabase()
    result = db.table("photo_equipment").select("*").eq("organization_id", org_id).execute()
    return {"equipment": result.data}


@router.post("/equipment")
async def add_equipment(website_id: str, data: dict):
    org_id = get_org_id(website_id)
    db = get_supabase()
    result = db.table("photo_equipment").insert({
        "organization_id": org_id,
        "name": data["name"],
        "type": data.get("type", "camera"),
        "brand": data.get("brand"),
        "model": data.get("model"),
        "serial_number": data.get("serial_number"),
        "purchase_date": data.get("purchase_date"),
        "purchase_price": data.get("purchase_price"),
        "condition": data.get("condition", "good"),
        "notes": data.get("notes"),
    }).execute()
    return {"equipment": result.data[0], "message": "Equipment added"}


# ============ DASHBOARD ============

@router.get("/dashboard")
async def photo_dashboard(website_id: str):
    org_id = get_org_id(website_id)
    db = get_supabase()
    
    events = db.table("photo_events").select("status, total_amount, advance_paid, balance_due").eq("organization_id", org_id).execute()
    enquiries = db.table("photo_enquiries").select("status").eq("organization_id", org_id).execute()
    deliveries = db.table("photo_deliveries").select("view_count").eq("organization_id", org_id).execute()
    
    total_bookings = len(events.data)
    upcoming = sum(1 for e in events.data if e["status"] in ("confirmed",))
    total_revenue = sum(float(e.get("advance_paid", 0) or 0) for e in events.data)
    pending_payment = sum(float(e.get("balance_due", 0) or 0) for e in events.data if e["status"] != "cancelled")
    new_enquiries = sum(1 for e in enquiries.data if e["status"] == "new")
    total_views = sum(d.get("view_count", 0) or 0 for d in deliveries.data)
    
    return {
        "total_bookings": total_bookings,
        "upcoming_shoots": upcoming,
        "total_revenue": total_revenue,
        "pending_payment": pending_payment,
        "new_enquiries": new_enquiries,
        "gallery_views": total_views,
    }
