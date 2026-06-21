from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/biz", tags=["business-ui"])


MODULE_CONFIG = {
    "crm": {"name": "CRM", "emoji": "&#128101;", "color": "#6366f1", "features": ["Contacts", "Pipeline", "Activities"]},
    "billing": {"name": "Billing", "emoji": "&#129534;", "color": "#10b981", "features": ["Invoices", "Payments", "Expenses"]},
    "booking": {"name": "Booking", "emoji": "&#128197;", "color": "#f59e0b", "features": ["Appointments", "Services", "Staff"]},
    "subscriptions": {"name": "Subscriptions", "emoji": "&#128257;", "color": "#8b5cf6", "features": ["Customers", "Deliveries", "Bills"]},
    "job_cards": {"name": "Job Cards", "emoji": "&#128295;", "color": "#ef4444", "features": ["Jobs", "Parts", "Reminders"]},
    "custom_orders": {"name": "Custom Orders", "emoji": "&#128203;", "color": "#f97316", "features": ["Orders", "Measurements", "Designs"]},
    "catalog": {"name": "Catalog", "emoji": "&#128722;", "color": "#06b6d4", "features": ["Items", "Categories"]},
    "clinic": {"name": "Clinic", "emoji": "&#129657;", "color": "#ec4899", "features": ["Patients", "Consultations", "Prescriptions"]},
    "students": {"name": "Students", "emoji": "&#127891;", "color": "#14b8a6", "features": ["Batches", "Attendance", "Fees"]},
    "events": {"name": "Events", "emoji": "&#127881;", "color": "#a855f7", "features": ["Bookings", "Venues", "Vendors"]},
    "fleet": {"name": "Fleet", "emoji": "&#128663;", "color": "#3b82f6", "features": ["Vehicles", "Drivers", "Trips"]},
    "reminders": {"name": "Reminders", "emoji": "&#128276;", "color": "#eab308", "features": ["Active", "Due Soon", "Overdue"]},
    "inventory": {"name": "Inventory", "emoji": "&#128230;", "color": "#22c55e", "features": ["Products", "Stock", "Suppliers"]},
}


def build_module_page(org_id: str, module_id: str, org_name: str = "Business"):
    config = MODULE_CONFIG.get(module_id, {"name": module_id, "emoji": "&#128188;", "color": "#6366f1", "features": []})
    api_base = f"/api/org/{org_id}/{module_id.replace('_', '-')}"
    
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{config["name"]} - {org_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#f8fafc;color:#1e293b;min-height:100vh}}
.header{{background:#fff;border-bottom:1px solid #e2e8f0;padding:12px 16px;position:sticky;top:0;z-index:10}}
.header-inner{{max-width:600px;margin:0 auto;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:1rem;font-weight:700;display:flex;align-items:center;gap:8px}}
.back{{color:#64748b;text-decoration:none;font-size:1.2rem}}
.main{{max-width:600px;margin:0 auto;padding:16px}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}}
.stat{{background:#fff;border:1px solid #f1f5f9;border-radius:12px;padding:14px;text-align:center}}
.stat .n{{font-size:1.5rem;font-weight:800;color:{config["color"]}}}
.stat .l{{font-size:.65rem;color:#64748b;margin-top:2px}}
.card{{background:#fff;border:1px solid #f1f5f9;border-radius:12px;padding:16px;margin-bottom:10px}}
.card h3{{font-size:.8rem;font-weight:700;margin-bottom:8px;color:#475569}}
.list-item{{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f8fafc}}
.list-item:last-child{{border:none}}
.list-item .name{{font-size:.8rem;font-weight:500}}
.list-item .meta{{font-size:.65rem;color:#94a3b8}}
.badge{{font-size:.6rem;padding:2px 8px;border-radius:10px;font-weight:600}}
.empty{{text-align:center;padding:30px;color:#94a3b8;font-size:.8rem}}
.btn{{display:block;width:100%;padding:12px;background:{config["color"]};color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer;text-align:center;text-decoration:none;margin-top:12px}}
.btn:hover{{opacity:.9}}
.tabs{{display:flex;gap:4px;background:#f1f5f9;border-radius:8px;padding:3px;margin-bottom:12px}}
.tab{{flex:1;padding:8px;border-radius:6px;font-size:.7rem;font-weight:600;text-align:center;cursor:pointer;color:#64748b}}
.tab.active{{background:#fff;color:#1e293b;box-shadow:0 1px 2px rgba(0,0,0,.05)}}
#loading{{text-align:center;padding:40px;color:#94a3b8}}
</style></head><body>
<div class="header"><div class="header-inner">
<h1><span>{config["emoji"]}</span> {config["name"]}</h1>
<a href="javascript:history.back()" class="back">&times;</a>
</div></div>

<div class="main">
<div id="loading">Loading...</div>
<div id="content" style="display:none">
<div class="stats" id="statsGrid"></div>
<div class="tabs" id="tabs"></div>
<div id="listArea"></div>
<a class="btn" id="addBtn" href="#">+ Add New</a>
</div>
</div>

<script>
var ORG_ID = "{org_id}";
var MODULE = "{module_id}";
var API = "{api_base}";
var features = {str(config["features"])};

async function loadDashboard() {{
  try {{
    var r = await fetch(API + "/dashboard");
    var data = await r.json();
    var statsHtml = "";
    var entries = Object.entries(data);
    entries.slice(0, 4).forEach(function(e) {{
      var label = e[0].replace(/_/g, " ").replace(/\b\w/g, function(c){{ return c.toUpperCase(); }});
      var val = typeof e[1] === "number" ? (e[1] > 999 ? "\\u20B9" + e[1].toLocaleString("en-IN") : e[1]) : e[1];
      statsHtml += '<div class="stat"><div class="n">' + val + '</div><div class="l">' + label + '</div></div>';
    }});
    document.getElementById("statsGrid").innerHTML = statsHtml;
    document.getElementById("loading").style.display = "none";
    document.getElementById("content").style.display = "block";
    
    // Tabs
    var tabsHtml = "";
    features.forEach(function(f, i) {{
      tabsHtml += '<div class="tab' + (i===0?' active':'') + '" onclick="switchTab(this)">' + f + '</div>';
    }});
    document.getElementById("tabs").innerHTML = tabsHtml;
    
    document.getElementById("listArea").innerHTML = '<div class="card"><div class="empty">No data yet. Start adding records!</div></div>';
  }} catch(e) {{
    document.getElementById("loading").innerHTML = '<p style="color:#ef4444">Error loading. Please try again.</p>';
  }}
}}

function switchTab(el) {{
  document.querySelectorAll(".tab").forEach(function(t){{ t.classList.remove("active"); }});
  el.classList.add("active");
}}

loadDashboard();
</script>
</body></html>'''




