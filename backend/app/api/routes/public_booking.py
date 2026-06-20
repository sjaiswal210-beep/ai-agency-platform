from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase

router = APIRouter(tags=["public-booking"])


@router.get("/book/{org_slug}", response_class=HTMLResponse)
async def public_booking_page(org_slug: str):
    """Public booking page for customers - no auth required."""
    db = get_supabase()
    
    # Get org
    org = db.table("organizations").select("*").eq("slug", org_slug).single().execute()
    if not org.data:
        raise HTTPException(404, "Business not found")
    
    org_data = org.data
    org_id = org_data["id"]
    
    # Check if booking module is enabled
    mod = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "booking").single().execute()
    if not mod.data or not mod.data.get("enabled"):
        raise HTTPException(404, "Online booking not available for this business")
    
    # Get services
    services = db.table("booking_services").select("id, name, duration_minutes, price").eq("organization_id", org_id).eq("is_active", True).order("sort_order").execute()
    
    # Build services JSON for the page
    import json
    services_json = json.dumps(services.data or [])
    brand_color = org_data.get("brand_color", "#6366f1")
    biz_name = org_data["name"]
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Book Appointment - {biz_name}</title>
<meta name="description" content="Book an appointment with {biz_name} online. Quick, easy, and free.">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;min-height:100vh;padding:16px}}
.container{{max-width:480px;margin:0 auto}}
.header{{text-align:center;margin-bottom:24px;padding:20px 0}}
.header h1{{font-size:1.3rem;color:#1e293b;margin-bottom:4px}}
.header p{{font-size:.8rem;color:#64748b}}
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:20px;margin-bottom:12px}}
.card h2{{font-size:.9rem;font-weight:600;color:#334155;margin-bottom:12px}}
label{{display:block;font-size:.75rem;font-weight:500;color:#64748b;margin-bottom:4px}}
input,select{{width:100%;padding:10px 12px;border:1px solid #e2e8f0;border-radius:10px;font-size:.85rem;outline:none;transition:border .2s}}
input:focus,select:focus{{border-color:{brand_color}}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.service-grid{{display:grid;gap:8px}}
.service-btn{{padding:12px;border:2px solid #e2e8f0;border-radius:12px;text-align:left;cursor:pointer;transition:all .2s;background:#fff}}
.service-btn:hover{{border-color:#cbd5e1}}
.service-btn.active{{border-color:{brand_color};background:{brand_color}10}}
.service-btn .name{{font-size:.85rem;font-weight:600;color:#1e293b}}
.service-btn .meta{{font-size:.7rem;color:#64748b;margin-top:2px}}
.submit-btn{{width:100%;padding:14px;background:{brand_color};color:#fff;border:none;border-radius:12px;font-size:.9rem;font-weight:600;cursor:pointer;transition:opacity .2s}}
.submit-btn:hover{{opacity:.9}}
.submit-btn:disabled{{opacity:.5;cursor:not-allowed}}
.success{{text-align:center;padding:40px 20px}}
.success .check{{width:64px;height:64px;background:#dcfce7;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:28px}}
.success h2{{font-size:1.2rem;color:#166534;margin-bottom:8px}}
.success p{{font-size:.8rem;color:#64748b}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{biz_name}</h1>
    <p>Book an appointment online</p>
  </div>

  <div id="bookingForm">
    <div class="card">
      <h2>Choose a Service</h2>
      <div class="service-grid" id="serviceGrid"></div>
    </div>

    <div class="card">
      <h2>Your Details</h2>
      <div style="margin-bottom:10px">
        <label>Name *</label>
        <input type="text" id="custName" placeholder="Your full name">
      </div>
      <div style="margin-bottom:10px">
        <label>Phone *</label>
        <input type="tel" id="custPhone" placeholder="9876543210">
      </div>
      <div class="row" style="margin-bottom:10px">
        <div>
          <label>Date *</label>
          <input type="date" id="custDate">
        </div>
        <div>
          <label>Time *</label>
          <input type="time" id="custTime" value="10:00">
        </div>
      </div>
      <div>
        <label>Notes (optional)</label>
        <input type="text" id="custNotes" placeholder="Any special requests...">
      </div>
    </div>

    <button class="submit-btn" id="submitBtn" onclick="submitBooking()">Book Appointment</button>
  </div>

  <div id="successMsg" style="display:none">
    <div class="success">
      <div class="check">&#10003;</div>
      <h2>Booking Confirmed!</h2>
      <p>We'll contact you shortly to confirm your appointment.</p>
      <button onclick="location.reload()" style="margin-top:16px;padding:10px 24px;border:1px solid #e2e8f0;border-radius:10px;background:#fff;font-size:.8rem;cursor:pointer">Book Another</button>
    </div>
  </div>
</div>

<script>
var services = {services_json};
var selectedService = null;
var orgId = "{org_id}";
var orgSlug = "{org_slug}";

// Set minimum date to today
document.getElementById("custDate").min = new Date().toISOString().split("T")[0];
document.getElementById("custDate").value = new Date().toISOString().split("T")[0];

// Render services
var grid = document.getElementById("serviceGrid");
if (services.length === 0) {{
  grid.innerHTML = "<p style='font-size:.8rem;color:#94a3b8;text-align:center;padding:12px'>No services available</p>";
}} else {{
  services.forEach(function(s) {{
    var btn = document.createElement("div");
    btn.className = "service-btn";
    btn.innerHTML = "<div class='name'>" + s.name + "</div><div class='meta'>" + s.duration_minutes + " min" + (s.price > 0 ? " &middot; &#8377;" + s.price : "") + "</div>";
    btn.onclick = function() {{
      document.querySelectorAll(".service-btn").forEach(function(b){{ b.classList.remove("active"); }});
      btn.classList.add("active");
      selectedService = s.id;
    }};
    grid.appendChild(btn);
  }});
}}

async function submitBooking() {{
  var name = document.getElementById("custName").value.trim();
  var phone = document.getElementById("custPhone").value.trim();
  var date = document.getElementById("custDate").value;
  var time = document.getElementById("custTime").value;
  var notes = document.getElementById("custNotes").value.trim();

  if (!name || !phone || !date || !time) {{
    alert("Please fill in name, phone, date and time");
    return;
  }}

  var btn = document.getElementById("submitBtn");
  btn.disabled = true;
  btn.textContent = "Booking...";

  // Calculate end time
  var duration = 60;
  if (selectedService) {{
    var svc = services.find(function(s){{ return s.id === selectedService; }});
    if (svc) duration = svc.duration_minutes;
  }}
  var parts = time.split(":");
  var endH = parseInt(parts[0]) + Math.floor((parseInt(parts[1]) + duration) / 60);
  var endM = (parseInt(parts[1]) + duration) % 60;
  var endTime = String(endH).padStart(2,"0") + ":" + String(endM).padStart(2,"0");

  try {{
    var res = await fetch("/api/org/" + orgId + "/booking/appointments", {{
      method: "POST",
      headers: {{"Content-Type": "application/json"}},
      body: JSON.stringify({{
        customer_name: name,
        customer_phone: phone,
        date: date,
        start_time: time,
        end_time: endTime,
        service_id: selectedService || undefined,
        notes: notes,
        source: "online"
      }})
    }});
    if (res.ok) {{
      document.getElementById("bookingForm").style.display = "none";
      document.getElementById("successMsg").style.display = "block";
    }} else {{
      alert("Booking failed. Please try again.");
      btn.disabled = false;
      btn.textContent = "Book Appointment";
    }}
  }} catch(e) {{
    alert("Error. Please try again.");
    btn.disabled = false;
    btn.textContent = "Book Appointment";
  }}
}}
</script>
</body>
</html>'''
    return HTMLResponse(content=html)
