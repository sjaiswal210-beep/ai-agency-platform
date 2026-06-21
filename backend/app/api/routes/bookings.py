from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/bookings", tags=["bookings"])


class BookingCreate(BaseModel):
    website_id: str
    customer_name: str
    customer_phone: str
    service: Optional[str] = ""
    date: Optional[str] = ""
    time: Optional[str] = ""
    notes: Optional[str] = ""


@router.post("/create")
def create_booking(req: BookingCreate):
    """Create a new booking from a website visitor."""
    db = get_supabase()
    service = WebsiteService()

    website = service.get(req.website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead_id = website.get("lead_id")

    booking = {
        "website_id": req.website_id,
        "lead_id": lead_id,
        "customer_name": req.customer_name,
        "customer_phone": req.customer_phone,
        "service": req.service,
        "date": req.date,
        "time": req.time,
        "notes": req.notes,
        "status": "pending",
    }

    try:
        result = db.table("bookings").insert(booking).execute()
        booking_id = result.data[0]["id"] if result.data else None
    except Exception as e:
        raise HTTPException(500, f"Failed to create booking: {str(e)}")

    # Track as analytics event
    try:
        db.table("analytics_events").insert({
            "website_id": req.website_id,
            "event_type": "booking",
            "page": "/booking",
        }).execute()
    except Exception:
        pass

    return {
        "status": "confirmed",
        "booking_id": booking_id,
        "message": "Booking received! We will confirm shortly via WhatsApp/call.",
    }


@router.get("/website/{website_id}")
def list_bookings(website_id: str, status: str = ""):
    """List all bookings for a website (business owner view)."""
    db = get_supabase()
    query = db.table("bookings").select("*").eq("website_id", website_id).order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    result = query.limit(50).execute()
    return result.data or []


@router.patch("/{booking_id}/status")
def update_booking_status(booking_id: str, status: str = "confirmed"):
    """Update booking status (pending/confirmed/cancelled/completed)."""
    db = get_supabase()
    valid = ["pending", "confirmed", "cancelled", "completed"]
    if status not in valid:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid}")

    db.table("bookings").update({"status": status}).eq("id", booking_id).execute()
    return {"booking_id": booking_id, "status": status, "updated": True}


@router.get("/stats/{website_id}")
def booking_stats(website_id: str):
    """Get booking statistics for a website."""
    db = get_supabase()
    all_bookings = db.table("bookings").select("status").eq("website_id", website_id).execute()

    stats = {"total": 0, "pending": 0, "confirmed": 0, "completed": 0, "cancelled": 0}
    for b in (all_bookings.data or []):
        stats["total"] += 1
        s = b.get("status", "pending")
        stats[s] = stats.get(s, 0) + 1

    return stats


@router.get("/{website_id}/book", response_class=HTMLResponse)
def booking_page(website_id: str):
    """Customer-facing booking page for a business."""
    from app.services.website_service import WebsiteService
    from app.services.lead_service import LeadService
    ws = WebsiteService()
    ls = LeadService()
    website = ws.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = ls.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""
    slug = website.get("slug", "")

    html = f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Book Appointment - {business_name}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:450px;margin:0 auto}}input,select,textarea{{font-size:16px!important}}.card{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px;margin-bottom:12px}}label{{display:block;font-size:.7rem;color:#94a3b8;margin-bottom:4px;font-weight:600}}input,select,textarea{{width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;margin-bottom:10px;outline:none}}.btn{{width:100%;padding:14px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.9rem;cursor:pointer}}.btn:disabled{{opacity:.5}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px">Book Appointment</h1>
<p style="font-size:.72rem;color:#64748b;text-align:center;margin-bottom:16px">{business_name}</p>
<form id="bookForm" onsubmit="submitBooking(event)">
<div class="card">
<label>Your Name *</label>
<input id="bName" required placeholder="Full name">
<label>Phone Number *</label>
<input id="bPhone" type="tel" required placeholder="WhatsApp number">
<label>Service</label>
<input id="bService" placeholder="e.g., Haircut, Consultation">
<label>Preferred Date *</label>
<input id="bDate" type="date" required>
<label>Preferred Time *</label>
<select id="bTime" required>
<option value="">Select time</option>
<option>9:00 AM</option><option>9:30 AM</option><option>10:00 AM</option><option>10:30 AM</option>
<option>11:00 AM</option><option>11:30 AM</option><option>12:00 PM</option><option>12:30 PM</option>
<option>2:00 PM</option><option>2:30 PM</option><option>3:00 PM</option><option>3:30 PM</option>
<option>4:00 PM</option><option>4:30 PM</option><option>5:00 PM</option><option>5:30 PM</option>
<option>6:00 PM</option><option>6:30 PM</option><option>7:00 PM</option><option>7:30 PM</option>
</select>
<label>Notes (optional)</label>
<textarea id="bNotes" rows="2" placeholder="Any special requests..."></textarea>
</div>
<button type="submit" class="btn" id="submitBtn">Confirm Booking</button>
</form>
<div id="result" style="display:none;text-align:center;padding:20px"></div>
<script>
async function submitBooking(e){{
  e.preventDefault();
  var btn=document.getElementById('submitBtn');btn.disabled=true;btn.textContent='Booking...';
  var data={{
    name:document.getElementById('bName').value,
    phone:document.getElementById('bPhone').value,
    service:document.getElementById('bService').value,
    date:document.getElementById('bDate').value,
    time:document.getElementById('bTime').value,
    notes:document.getElementById('bNotes').value
  }};
  try{{
    var r=await fetch('/api/bookings/{website_id}/create',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
    var d=await r.json();
    document.getElementById('bookForm').style.display='none';
    document.getElementById('result').style.display='block';
    document.getElementById('result').innerHTML='<div style="font-size:2rem;margin-bottom:8px">&#9989;</div><h2 style="font-size:1rem;margin-bottom:8px">Booking Confirmed!</h2><p style="font-size:.8rem;color:#94a3b8">'+data.date+' at '+data.time+'</p><p style="font-size:.72rem;color:#64748b;margin-top:8px">You will receive confirmation on WhatsApp</p>';
  }}catch(err){{btn.disabled=false;btn.textContent='Confirm Booking';alert('Failed. Try again.');}}
}}
</script>
</body></html>"""
    return HTMLResponse(content=html)


@router.post("/{website_id}/create")
async def create_booking(website_id: str, data: dict):
    """Create a new booking and notify business owner."""
    from app.core.supabase import get_supabase
    from app.services.website_service import WebsiteService
    from app.services.lead_service import LeadService
    from datetime import datetime
    
    db = get_supabase()
    ws = WebsiteService()
    ls = LeadService()
    website = ws.get(website_id)
    lead = ls.get(website["lead_id"]) if website and website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    owner_phone = lead.get("phone", "") if lead else ""
    
    booking = {
        "website_id": website_id,
        "customer_name": data.get("name", ""),
        "customer_phone": data.get("phone", ""),
        "service": data.get("service", ""),
        "booking_date": data.get("date", ""),
        "booking_time": data.get("time", ""),
        "notes": data.get("notes", ""),
        "status": "confirmed",
        "created_at": datetime.utcnow().isoformat(),
    }
    
    try:
        db.table("bookings").insert(booking).execute()
    except Exception:
        pass
    
    # Send WhatsApp notification to business owner
    if owner_phone:
        import urllib.parse
        msg = f"New Booking!\nCustomer: {data.get('name')}\nPhone: {data.get('phone')}\nService: {data.get('service')}\nDate: {data.get('date')} {data.get('time')}\nNotes: {data.get('notes', '-')}"
        # Try WhatsApp API
        try:
            import httpx, os
            wa_token = os.environ.get("WHATSAPP_TOKEN", "")
            wa_phone_id = os.environ.get("WHATSAPP_PHONE_ID", "")
            if wa_token and wa_phone_id:
                clean_phone = owner_phone.replace("+", "").replace(" ", "").replace("-", "")
                if not clean_phone.startswith("91"):
                    clean_phone = "91" + clean_phone
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://graph.facebook.com/v18.0/{wa_phone_id}/messages",
                        headers={"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"},
                        json={"messaging_product": "whatsapp", "to": clean_phone, "type": "text", "text": {"body": msg}}
                    )
        except Exception:
            pass
    
    return {"status": "confirmed", "booking": booking}


@router.get("/{website_id}/manage-bookings", response_class=HTMLResponse)
def manage_bookings_page(website_id: str):
    """Owner view - see all bookings."""
    from app.core.supabase import get_supabase
    from app.services.website_service import WebsiteService
    from app.services.lead_service import LeadService
    db = get_supabase()
    ws = WebsiteService()
    ls = LeadService()
    website = ws.get(website_id)
    lead = ls.get(website["lead_id"]) if website and website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    
    bookings = []
    try:
        result = db.table("bookings").select("*").eq("website_id", website_id).order("booking_date", desc=True).limit(50).execute()
        bookings = result.data or []
    except Exception:
        pass
    
    rows = ""
    for b in bookings:
        status_color = "#22c55e" if b.get("status") == "confirmed" else "#f59e0b" if b.get("status") == "pending" else "#64748b"
        rows += f'<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px;margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:.8rem">{b.get("customer_name","")}</b><span style="font-size:.6rem;color:{status_color};font-weight:600">{b.get("status","").upper()}</span></div><p style="font-size:.7rem;color:#94a3b8;margin-top:4px">{b.get("service","")} | {b.get("booking_date","")} {b.get("booking_time","")}</p><p style="font-size:.65rem;color:#64748b;margin-top:2px">Phone: {b.get("customer_phone","")}</p></div>'
    
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Bookings - {business_name}</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;margin-bottom:4px">Bookings</h1>
<p style="font-size:.72rem;color:#64748b;margin-bottom:16px">{business_name} &bull; {len(bookings)} total</p>
{rows or '<p style="text-align:center;color:#475569;font-size:.8rem;padding:20px">No bookings yet. Share your booking link with customers!</p>'}
<div style="margin-top:16px;padding:12px;background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);border-radius:10px;text-align:center"><p style="font-size:.7rem;color:#a78bfa;margin-bottom:6px">Your booking link:</p><input value="https://{website.get('slug','')}.city-maps.online/api/bookings/{website_id}/book" readonly onclick="this.select();navigator.clipboard.writeText(this.value)" style="width:100%;padding:8px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.1);border-radius:6px;color:#00e5ff;font-size:11px;text-align:center"></div>
</body></html>"""
    return HTMLResponse(content=html)
