from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase
import httpx
import asyncio
from datetime import date

router = APIRouter(tags=["health-check"])


@router.get("/api/health-check", response_class=HTMLResponse)
async def full_health_check(pwd: str = ""):
    """Complete platform health check - tests every endpoint and module."""
    if pwd != "kalpdev2024":
        return HTMLResponse('<html><body style="font-family:sans-serif;background:#0f172a;color:#fff;padding:40px;text-align:center"><h2>Health Check</h2><form method="GET"><input name="pwd" type="password" placeholder="Password" style="padding:10px;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#fff;margin-right:8px"><button style="padding:10px 20px;background:#6366f1;color:#fff;border:none;border-radius:8px;cursor:pointer">Run Check</button></form></body></html>')
    
    db = get_supabase()
    BASE = "https://ai-agency-platform.onrender.com"
    results = []
    
    # Test org for module checks
    test_org_id = ""
    test_slug = ""
    try:
        orgs = db.table("organizations").select("id, slug").limit(1).execute()
        if orgs.data:
            test_org_id = orgs.data[0]["id"]
            test_slug = orgs.data[0]["slug"]
    except:
        pass

    async def check_url(name, url, method="GET", expect_html=False, body=None):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if method == "POST":
                    r = await client.post(url, json=body or {})
                else:
                    r = await client.get(url)
                
                status = r.status_code
                is_html = "<!DOCTYPE" in r.text[:100] or "<html" in r.text[:100]
                is_json = r.text.strip().startswith("{") or r.text.strip().startswith("[")
                
                if status == 200:
                    if expect_html and is_html:
                        return (name, "OK", "HTML page loads", status)
                    elif not expect_html and is_json:
                        return (name, "OK", "JSON response", status)
                    elif status == 200:
                        return (name, "OK", "200 response", status)
                elif status == 403:
                    return (name, "WARN", "Module not enabled (403)", status)
                else:
                    return (name, "FAIL", f"HTTP {status}", status)
        except Exception as e:
            return (name, "FAIL", str(e)[:50], 0)

    # === ADMIN PAGES ===
    tests = []
    tests.append(await check_url("Admin Portal", f"{BASE}/api/admin/manage?pwd=kalpdev2024", expect_html=True))
    tests.append(await check_url("Platform Overview", f"{BASE}/api/platform-overview", expect_html=True))
    tests.append(await check_url("Admin - List Modules", f"{BASE}/api/admin/modules"))
    tests.append(await check_url("Admin - List Organizations", f"{BASE}/api/admin/organizations?limit=5"))
    tests.append(await check_url("Admin - List Templates", f"{BASE}/api/admin/templates"))
    tests.append(await check_url("Admin - Audit Log", f"{BASE}/api/admin/audit-log?limit=5"))
    tests.append(await check_url("Admin - Panel Tools", f"{BASE}/api/admin/panel-tools/"))
    
    # === ORGANIZATION APIs ===
    if test_org_id:
        tests.append(await check_url("Org - Get Modules", f"{BASE}/api/organizations/{test_org_id}/modules"))
        tests.append(await check_url("Org - Get Details", f"{BASE}/api/organizations/{test_org_id}"))
    
    # === MODULE APIs (JSON) ===
    if test_org_id:
        module_apis = [
            ("CRM Dashboard", f"/api/org/{test_org_id}/crm/dashboard"),
            ("CRM Contacts", f"/api/org/{test_org_id}/crm/contacts"),
            ("Billing Dashboard", f"/api/org/{test_org_id}/billing/dashboard"),
            ("Billing Invoices", f"/api/org/{test_org_id}/billing/invoices"),
            ("Booking Appointments", f"/api/org/{test_org_id}/booking/appointments"),
            ("Booking Services", f"/api/org/{test_org_id}/booking/services"),
            ("Subscriptions", f"/api/org/{test_org_id}/subscriptions"),
            ("Subscriptions Today", f"/api/org/{test_org_id}/subscriptions/today"),
            ("Job Cards", f"/api/org/{test_org_id}/job-cards"),
            ("Job Cards Dashboard", f"/api/org/{test_org_id}/job-cards/dashboard"),
            ("Custom Orders", f"/api/org/{test_org_id}/custom-orders"),
            ("Catalog Items", f"/api/org/{test_org_id}/catalog/items"),
            ("Clinic Patients", f"/api/org/{test_org_id}/clinic/patients"),
            ("Students", f"/api/org/{test_org_id}/students"),
            ("Students Batches", f"/api/org/{test_org_id}/students/batches"),
            ("Events Bookings", f"/api/org/{test_org_id}/events/bookings"),
            ("Fleet Vehicles", f"/api/org/{test_org_id}/fleet/vehicles"),
            ("Fleet Dashboard", f"/api/org/{test_org_id}/fleet/dashboard"),
            ("Reminders", f"/api/org/{test_org_id}/reminders"),
            ("Reminders Due", f"/api/org/{test_org_id}/reminders/due-soon"),
            ("Inventory Products", f"/api/org/{test_org_id}/inventory/products"),
            ("Inventory Dashboard", f"/api/org/{test_org_id}/inventory/dashboard"),
            ("Assets", f"/api/org/{test_org_id}/assets"),
            ("Assets Dashboard", f"/api/org/{test_org_id}/assets/dashboard"),
            ("Projects", f"/api/org/{test_org_id}/projects"),
            ("Projects Dashboard", f"/api/org/{test_org_id}/projects/dashboard"),
            ("Documents", f"/api/org/{test_org_id}/documents"),
            ("WhatsApp Dashboard", f"/api/org/{test_org_id}/whatsapp/dashboard"),
            ("WhatsApp Config", f"/api/org/{test_org_id}/whatsapp/config"),
            ("AI Employee Suggestions", f"/api/org/{test_org_id}/ai/suggestions"),
        ]
        for name, path in module_apis:
            tests.append(await check_url(f"API: {name}", f"{BASE}{path}"))
    
    # === UI PAGES (HTML) ===
    if test_slug:
        ui_pages = [
            ("UI: CRM", f"/api/biz/{test_slug}/crm"),
            ("UI: Billing", f"/api/biz/{test_slug}/billing"),
            ("UI: Booking", f"/api/biz/{test_slug}/booking"),
            ("UI: Subscriptions", f"/api/biz/{test_slug}/subscriptions"),
            ("UI: Job Cards", f"/api/biz/{test_slug}/job_cards"),
            ("UI: Custom Orders", f"/api/biz/{test_slug}/custom_orders"),
            ("UI: Clinic", f"/api/biz/{test_slug}/clinic"),
            ("UI: Students", f"/api/biz/{test_slug}/students"),
            ("UI: Events", f"/api/biz/{test_slug}/events"),
            ("UI: Fleet", f"/api/biz/{test_slug}/fleet"),
            ("UI: Reminders", f"/api/biz/{test_slug}/reminders"),
            ("UI: Inventory", f"/api/biz/{test_slug}/inventory"),
            ("UI: Assets", f"/api/biz/{test_slug}/assets"),
            ("UI: Projects", f"/api/biz/{test_slug}/projects"),
            ("UI: Documents", f"/api/biz/{test_slug}/documents"),
            ("UI: AI Employee", f"/api/biz/{test_slug}/ai_employee"),
            ("UI: WhatsApp", f"/api/biz/{test_slug}/whatsapp"),
            ("UI: Delivery Board", f"/api/biz/{test_slug}/subscriptions/deliver"),
        ]
        for name, path in ui_pages:
            tests.append(await check_url(name, f"{BASE}{path}", expect_html=True))
    
    # === PUBLIC PAGES ===
    if test_slug:
        tests.append(await check_url("Public: Catalog", f"{BASE}/api/menu/{test_slug}", expect_html=True))
        tests.append(await check_url("Public: Booking", f"{BASE}/api/book/{test_slug}", expect_html=True))
    
    # === DATABASE TABLES ===
    db_tables = ["organizations", "modules", "organization_modules", "industry_templates", "crm_contacts", "billing_invoices", "booking_appointments", "subscriptions", "job_cards", "custom_orders", "patients", "students", "batches", "event_bookings", "fleet_vehicles", "reminders", "assets", "projects", "documents", "whatsapp_config"]
    for table in db_tables:
        try:
            r = db.table(table).select("id", count="exact").limit(1).execute()
            tests.append((f"DB: {table}", "OK", f"{r.count} rows", 200))
        except Exception as e:
            tests.append((f"DB: {table}", "FAIL", str(e)[:40], 0))
    
    # === BUILD RESULTS HTML ===
    ok_count = sum(1 for t in tests if t[1] == "OK")
    warn_count = sum(1 for t in tests if t[1] == "WARN")
    fail_count = sum(1 for t in tests if t[1] == "FAIL")
    total = len(tests)
    
    rows = ""
    for (name, status, detail, code) in tests:
        color = "#22c55e" if status == "OK" else "#f59e0b" if status == "WARN" else "#ef4444"
        icon = "&#10003;" if status == "OK" else "&#9888;" if status == "WARN" else "&#10007;"
        fix = ""
        if status == "FAIL":
            if "DB:" in name:
                fix = f"Run SQL schema in Supabase for this table. Check scripts/ folder."
            elif "API:" in name:
                if "403" in detail:
                    fix = "Enable this module for the org in Admin Portal."
                else:
                    fix = "Check Render logs. Module router may have import error."
            elif "UI:" in name:
                fix = "Check business_ui.py syntax. Module page may be misconfigured."
            elif "Public" in name:
                fix = "Module not enabled OR public page route broken."
            else:
                fix = "Check Render deploy logs."
        elif status == "WARN":
            fix = "Enable module via Admin Portal for this org."
        fix_html = f'<div style="font-size:.55rem;color:#fbbf24;margin-top:2px;font-style:italic">Fix: {fix}</div>' if fix else ""
        rows += f'<tr><td style="color:{color};font-weight:700">{icon} {status}</td><td>{name}{fix_html}</td><td style="color:#94a3b8">{detail}</td></tr>'
    
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Platform Health Check</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;max-width:900px;margin:0 auto}}
h1{{font-size:1.3rem;font-weight:800;margin-bottom:4px}}
.sub{{font-size:.75rem;color:#64748b;margin-bottom:20px}}
.stats{{display:flex;gap:12px;margin-bottom:20px}}
.stat{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px 20px;text-align:center;flex:1}}
.stat .n{{font-size:1.5rem;font-weight:800}}
.stat .l{{font-size:.6rem;color:#64748b;margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:.75rem}}
th{{text-align:left;padding:8px 10px;background:#1e293b;color:#64748b;font-size:.65rem;text-transform:uppercase;border-bottom:1px solid #334155}}
td{{padding:8px 10px;border-bottom:1px solid #1e293b}}
tr:hover td{{background:rgba(99,102,241,.05)}}
.score{{font-size:2rem;font-weight:900;background:linear-gradient(135deg,{"#22c55e" if fail_count==0 else "#f59e0b" if fail_count<5 else "#ef4444"},{"#06b6d4" if fail_count==0 else "#eab308" if fail_count<5 else "#f97316"});-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.refresh{{position:fixed;bottom:20px;right:20px;padding:10px 16px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.8rem}}
</style></head><body>
<h1>&#128994; Platform Health Check</h1>
<p class="sub">Testing {total} endpoints | {date.today().strftime("%B %d, %Y")}</p>

<div class="stats">
<div class="stat"><div class="n score">{ok_count}/{total}</div><div class="l">Health Score</div></div>
<div class="stat"><div class="n" style="color:#22c55e">{ok_count}</div><div class="l">Passing</div></div>
<div class="stat"><div class="n" style="color:#f59e0b">{warn_count}</div><div class="l">Warnings</div></div>
<div class="stat"><div class="n" style="color:#ef4444">{fail_count}</div><div class="l">Failing</div></div>
</div>

<table>
<thead><tr><th>Status</th><th>Endpoint</th><th>Detail</th></tr></thead>
<tbody>{rows}</tbody>
</table>

<button class="refresh" onclick="location.reload()">&#128260; Re-run Check</button>
</body></html>'''
    return HTMLResponse(content=html)