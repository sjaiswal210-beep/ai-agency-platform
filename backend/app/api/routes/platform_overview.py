from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase

router = APIRouter(tags=["platform-overview"])


@router.get("/api/platform-overview", response_class=HTMLResponse)
async def platform_overview():
    """Complete platform overview - what we built, how it works."""
    db = get_supabase()
    
    # Get live stats
    try:
        orgs = db.table("organizations").select("id", count="exact").execute()
        modules = db.table("modules").select("id", count="exact").execute()
        templates = db.table("industry_templates").select("id", count="exact").execute()
        websites = db.table("websites").select("id", count="exact").execute()
        leads = db.table("leads").select("id", count="exact").execute()
        org_count = orgs.count or 0
        mod_count = modules.count or 0
        tmpl_count = templates.count or 0
        web_count = websites.count or 0
        lead_count = leads.count or 0
    except:
        org_count = mod_count = tmpl_count = web_count = lead_count = 0

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City-Maps Business OS - Platform Overview</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {{ --p: #6366f1; --g: #22c55e; --b: #3b82f6; --o: #f59e0b; --r: #ef4444; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: Inter, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
.container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}

/* Hero */
.hero {{ text-align: center; padding: 60px 20px 40px; background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%); }}
.hero h1 {{ font-size: 2.2rem; font-weight: 900; background: linear-gradient(135deg, #6366f1, #06b6d4, #22c55e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }}
.hero .sub {{ font-size: 1rem; color: #94a3b8; max-width: 600px; margin: 0 auto 24px; }}
.hero .stats {{ display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; }}
.hero .stat {{ text-align: center; }}
.hero .stat .n {{ font-size: 2rem; font-weight: 900; color: #fff; }}
.hero .stat .l {{ font-size: .7rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }}

/* Sections */
.section {{ padding: 40px 0; border-top: 1px solid #1e293b; }}
.section-title {{ font-size: 1.3rem; font-weight: 800; margin-bottom: 6px; color: #fff; }}
.section-sub {{ font-size: .85rem; color: #64748b; margin-bottom: 20px; }}

/* Cards */
.card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }}
.card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; transition: border-color .2s; }}
.card:hover {{ border-color: #6366f1; }}
.card h3 {{ font-size: .9rem; font-weight: 700; color: #fff; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }}
.card p {{ font-size: .75rem; color: #94a3b8; }}
.card .features {{ margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px; }}
.card .features span {{ font-size: .6rem; padding: 2px 8px; background: rgba(99,102,241,.15); color: #a5b4fc; border-radius: 6px; }}

/* Tables */
table {{ width: 100%; border-collapse: collapse; font-size: .8rem; }}
th {{ text-align: left; padding: 10px 12px; background: #1e293b; color: #94a3b8; font-size: .7rem; text-transform: uppercase; letter-spacing: .5px; border-bottom: 1px solid #334155; }}
td {{ padding: 10px 12px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }}
tr:hover td {{ background: rgba(99,102,241,.05); }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: .6rem; font-weight: 600; }}
.b-green {{ background: rgba(34,197,94,.15); color: #4ade80; }}
.b-blue {{ background: rgba(59,130,246,.15); color: #60a5fa; }}
.b-purple {{ background: rgba(139,92,246,.15); color: #a78bfa; }}
.b-orange {{ background: rgba(245,158,11,.15); color: #fbbf24; }}

/* Flow */
.flow {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 16px 0; }}
.flow-step {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 12px 16px; text-align: center; min-width: 120px; }}
.flow-step .icon {{ font-size: 1.5rem; margin-bottom: 4px; }}
.flow-step .text {{ font-size: .7rem; color: #94a3b8; }}
.flow-arrow {{ color: #475569; font-size: 1.2rem; }}

/* URL box */
.url-box {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; font-family: monospace; font-size: .75rem; color: #06b6d4; margin: 6px 0; word-break: break-all; }}

/* Pricing */
.pricing {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; }}
.price-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center; }}
.price-card.featured {{ border-color: #6366f1; background: linear-gradient(180deg, #1e1b4b, #1e293b); }}
.price-card .plan {{ font-size: .7rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }}
.price-card .amount {{ font-size: 2rem; font-weight: 900; color: #fff; margin: 8px 0 4px; }}
.price-card .amount small {{ font-size: .8rem; color: #64748b; }}
.price-card .modules {{ font-size: .7rem; color: #94a3b8; margin-top: 8px; text-align: left; }}
.price-card .modules li {{ margin: 4px 0; list-style: none; }}
.price-card .modules li::before {{ content: "\\2713 "; color: #22c55e; }}

/* Two col */
.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media(max-width: 768px) {{ .two-col {{ grid-template-columns: 1fr; }} .pricing {{ grid-template-columns: 1fr; }} }}

/* Links */
a {{ color: #6366f1; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.link-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; }}
.link-item {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px; }}
.link-item .label {{ font-size: .65rem; color: #64748b; text-transform: uppercase; margin-bottom: 4px; }}
.link-item .url {{ font-size: .72rem; color: #06b6d4; word-break: break-all; }}
</style>
</head>
<body>

<!-- HERO -->
<div class="hero">
<h1>City-Maps Business OS</h1>
<p class="sub">Multi-Tenant AI-Powered Business Operating System serving every local business category in India</p>
<div class="stats">
<div class="stat"><div class="n">{org_count}</div><div class="l">Organizations</div></div>
<div class="stat"><div class="n">{mod_count}</div><div class="l">Modules</div></div>
<div class="stat"><div class="n">{tmpl_count}</div><div class="l">Templates</div></div>
<div class="stat"><div class="n">{web_count}</div><div class="l">Websites</div></div>
<div class="stat"><div class="n">{lead_count}</div><div class="l">Leads</div></div>
</div>
</div>

<div class="container">

<!-- WHAT IT IS -->
<div class="section">
<div class="section-title">What We Built</div>
<p class="section-sub">A platform where ANY local business gets a professional website + a complete dashboard with operational tools — all controlled by you.</p>

<div class="two-col">
<div class="card">
<h3>&#128084; Your Side (Platform Owner)</h3>
<p>You discover businesses, generate websites, onboard them, and control which tools they get access to based on their plan. You monetize by offering more tools at higher plans.</p>
</div>
<div class="card">
<h3>&#127970; Business Owner's Side</h3>
<p>They get a professional website + a dashboard with tools specific to their industry. A gym gets Membership + Booking. A dairy gets Subscriptions + Delivery. They run their entire business from one place.</p>
</div>
</div>
</div>

<!-- HOW IT WORKS - FLOW -->
<div class="section">
<div class="section-title">How It Works</div>
<p class="section-sub">End-to-end flow from discovery to running business</p>

<div class="flow">
<div class="flow-step"><div class="icon">&#128269;</div><div class="text">Discover Business<br>(Google Maps)</div></div>
<span class="flow-arrow">&rarr;</span>
<div class="flow-step"><div class="icon">&#127760;</div><div class="text">Generate Website<br>(AI + Templates)</div></div>
<span class="flow-arrow">&rarr;</span>
<div class="flow-step"><div class="icon">&#128172;</div><div class="text">WhatsApp Outreach<br>("We built you a site")</div></div>
<span class="flow-arrow">&rarr;</span>
<div class="flow-step"><div class="icon">&#128176;</div><div class="text">Business Subscribes<br>(Razorpay)</div></div>
<span class="flow-arrow">&rarr;</span>
<div class="flow-step"><div class="icon">&#9881;</div><div class="text">Create Org +<br>Apply Template</div></div>
<span class="flow-arrow">&rarr;</span>
<div class="flow-step"><div class="icon">&#128187;</div><div class="text">Business Gets<br>Dashboard + Tools</div></div>
</div>
</div>

<!-- MODULES -->
<div class="section">
<div class="section-title">22 Modules Available</div>
<p class="section-sub">Each module is a self-contained tool with database, API, and interactive UI</p>

<table>
<thead><tr><th>#</th><th>Module</th><th>What It Does</th><th>For</th><th>Status</th></tr></thead>
<tbody>
<tr><td>1</td><td><b>CRM</b></td><td>Contacts, pipeline, activities, lead scoring</td><td>All businesses</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>2</td><td><b>Billing</b></td><td>Invoices, quotations, payments, expenses</td><td>All businesses</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>3</td><td><b>Booking</b></td><td>Appointments, services, staff, online booking</td><td>Salon, Doctor, Spa</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>4</td><td><b>Subscriptions</b></td><td>Recurring deliveries, routes, auto-billing</td><td>Dairy, Tiffin, Water</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>5</td><td><b>Job Cards</b></td><td>Service tickets, status pipeline, parts, reminders</td><td>Garage, Electrician, Plumber</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>6</td><td><b>Custom Orders</b></td><td>Made-to-order tracking, measurements, designs</td><td>Tailor, Furniture, Bakery</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>7</td><td><b>Catalog/Menu</b></td><td>Digital product catalog, shareable via WhatsApp</td><td>Restaurant, Fashion, Gift Shop</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>8</td><td><b>Clinic/Patient</b></td><td>Patient records, consultations, prescriptions</td><td>Doctor, Dentist, Vet</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>9</td><td><b>Students/Batch</b></td><td>Enrollment, attendance, fee collection</td><td>Coaching, School, Dance</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>10</td><td><b>Events/Venue</b></td><td>Event booking, venues, vendors, checklist</td><td>Marriage Hall, Event Planner</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>11</td><td><b>Fleet/Vehicle</b></td><td>Vehicles, drivers, trips, fuel, maintenance</td><td>Cab, Transport, Movers</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>12</td><td><b>Reminders</b></td><td>Renewal alerts, auto-recurrence, overdue tracking</td><td>Insurance, Optical, AMC</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>13</td><td><b>Inventory</b></td><td>Products, stock, suppliers, movements</td><td>Kirana, Retail, Hardware</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>14</td><td><b>Property</b></td><td>Buildings, rooms, tenants, rent, complaints</td><td>PG, Hostel, Hotel</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>15</td><td><b>Membership</b></td><td>Plans, subscriptions, attendance</td><td>Gym, Yoga, Club</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>16</td><td><b>WhatsApp</b></td><td>Connect own API, send/broadcast, templates, automation</td><td>All businesses</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>17</td><td><b>Photographer</b></td><td>Portfolio, shoots, client delivery, packages</td><td>Photographer</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>18</td><td><b>Website</b></td><td>AI-generated business website</td><td>All businesses</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>19</td><td><b>Analytics</b></td><td>Visitors, calls, WhatsApp clicks</td><td>All businesses</td><td><span class="badge b-green">Live</span></td></tr>
<tr><td>20</td><td><b>Assets</b></td><td>Equipment, warranty, AMC tracking</td><td>Solar, Contractor</td><td><span class="badge b-blue">API Ready</span></td></tr>
<tr><td>21</td><td><b>Projects</b></td><td>Milestones, tasks, budgets</td><td>Interior, Freelancer</td><td><span class="badge b-blue">API Ready</span></td></tr>
<tr><td>22</td><td><b>Documents</b></td><td>File management, templates</td><td>Lawyer, CA</td><td><span class="badge b-blue">API Ready</span></td></tr>
</tbody>
</table>
</div>

<!-- INDUSTRY TEMPLATES -->
<div class="section">
<div class="section-title">46 Industry Templates</div>
<p class="section-sub">One-click applies the right modules for any business type</p>

<div class="card-grid">
<div class="card"><h3>&#127968; PG / Hostel</h3><div class="features"><span>CRM</span><span>Property</span><span>Billing</span><span>WhatsApp</span><span>Website</span><span>Analytics</span></div></div>
<div class="card"><h3>&#127860; Restaurant</h3><div class="features"><span>CRM</span><span>Billing</span><span>Inventory</span><span>Booking</span><span>Website</span><span>WhatsApp</span></div></div>
<div class="card"><h3>&#9986; Salon / Spa</h3><div class="features"><span>CRM</span><span>Booking</span><span>Billing</span><span>Membership</span><span>Website</span><span>WhatsApp</span></div></div>
<div class="card"><h3>&#127947; Gym / Fitness</h3><div class="features"><span>CRM</span><span>Membership</span><span>Billing</span><span>Booking</span><span>Website</span><span>WhatsApp</span></div></div>
<div class="card"><h3>&#128248; Photographer</h3><div class="features"><span>CRM</span><span>Booking</span><span>Billing</span><span>Projects</span><span>Documents</span><span>Website</span></div></div>
<div class="card"><h3>&#129480; Dairy / Milk</h3><div class="features"><span>CRM</span><span>Subscriptions</span><span>Billing</span><span>WhatsApp</span><span>Website</span></div></div>
<div class="card"><h3>&#128295; Garage / Bike</h3><div class="features"><span>CRM</span><span>Job Cards</span><span>Inventory</span><span>Billing</span><span>WhatsApp</span></div></div>
<div class="card"><h3>&#129658; Doctor / Clinic</h3><div class="features"><span>CRM</span><span>Clinic</span><span>Booking</span><span>Billing</span><span>WhatsApp</span></div></div>
<div class="card"><h3>&#127891; Coaching Center</h3><div class="features"><span>CRM</span><span>Students</span><span>Billing</span><span>WhatsApp</span><span>Website</span></div></div>
<div class="card"><h3>&#9985; Tailor</h3><div class="features"><span>CRM</span><span>Custom Orders</span><span>Billing</span><span>WhatsApp</span><span>Website</span></div></div>
<div class="card"><h3>&#127881; Marriage Hall</h3><div class="features"><span>CRM</span><span>Events</span><span>Billing</span><span>WhatsApp</span><span>Website</span></div></div>
<div class="card"><h3>&#128663; Cab / Transport</h3><div class="features"><span>CRM</span><span>Fleet</span><span>Billing</span><span>WhatsApp</span><span>Website</span></div></div>
</div>
<p style="font-size:.75rem;color:#64748b;margin-top:12px;text-align:center">+ 34 more templates (Insurance, Optical, Laundry, Pest Control, Furniture, Jewellery, Bakery, etc.)</p>
</div>

<!-- PRICING MODEL -->
<div class="section">
<div class="section-title">Revenue Model</div>
<p class="section-sub">More modules = higher plan = more revenue</p>

<div class="pricing">
<div class="price-card">
<div class="plan">Starter</div>
<div class="amount">&#8377;79<small>/mo</small></div>
<ul class="modules"><li>CRM (basic)</li><li>Billing</li><li>Website</li><li>Analytics</li><li>4 modules</li></ul>
</div>
<div class="price-card featured">
<div class="plan">Pro (Popular)</div>
<div class="amount">&#8377;299<small>/mo</small></div>
<ul class="modules"><li>Everything in Starter</li><li>Booking / Subscriptions</li><li>Job Cards / Custom Orders</li><li>Inventory / WhatsApp</li><li>Catalog + Public Pages</li><li>12+ modules</li></ul>
</div>
<div class="price-card">
<div class="plan">Enterprise</div>
<div class="amount">&#8377;999<small>/mo</small></div>
<ul class="modules"><li>All 22 modules</li><li>Clinic / Students</li><li>Events / Fleet</li><li>Photographer toolkit</li><li>AI Employee</li><li>Priority support</li></ul>
</div>
</div>
</div>

<!-- KEY URLS -->
<div class="section">
<div class="section-title">Key URLs</div>
<p class="section-sub">All access points for admin and business owners</p>

<div class="link-grid">
<div class="link-item"><div class="label">Admin Portal</div><div class="url">/api/admin/manage?pwd=kalpdev2024</div></div>
<div class="link-item"><div class="label">Business Panel</div><div class="url">/api/panel/{{website_id}}</div></div>
<div class="link-item"><div class="label">Module UI</div><div class="url">/api/biz/{{slug}}/{{module_id}}</div></div>
<div class="link-item"><div class="label">Public Catalog</div><div class="url">/api/menu/{{slug}}</div></div>
<div class="link-item"><div class="label">Public Booking</div><div class="url">/api/book/{{slug}}</div></div>
<div class="link-item"><div class="label">Daily Content</div><div class="url">/api/daily/{{website_id}}</div></div>
<div class="link-item"><div class="label">WhatsApp Settings</div><div class="url">/api/biz/{{slug}}/whatsapp</div></div>
<div class="link-item"><div class="label">Delivery Board</div><div class="url">/api/biz/{{slug}}/subscriptions/deliver</div></div>
</div>
</div>

<!-- TECH STACK -->
<div class="section">
<div class="section-title">Tech Stack</div>
<table>
<tr><td><b>Backend</b></td><td>FastAPI (Python) on Render</td></tr>
<tr><td><b>Database</b></td><td>Supabase (PostgreSQL) with Row Level Security</td></tr>
<tr><td><b>Frontend</b></td><td>Server-rendered HTML (works on subdomains directly)</td></tr>
<tr><td><b>Websites</b></td><td>AI-generated, deployed at *.city-maps.online</td></tr>
<tr><td><b>WhatsApp</b></td><td>Business owner's own API (Meta/WATI/AiSensy)</td></tr>
<tr><td><b>AI</b></td><td>OpenRouter (Claude/GPT-4) for content generation</td></tr>
<tr><td><b>DNS</b></td><td>Cloudflare (wildcard subdomains)</td></tr>
<tr><td><b>Payments</b></td><td>Razorpay integration</td></tr>
</table>
</div>

<!-- ARCHITECTURE -->
<div class="section">
<div class="section-title">Architecture Principle</div>
<div class="card" style="border-color:#6366f1">
<h3 style="color:#a5b4fc">BUILD CAPABILITIES, NOT BUSINESS TYPES</h3>
<p style="margin-top:8px">We never built a "Dairy Module" or "Salon Module". Instead we built universal capabilities (Subscriptions, Booking, Job Cards) that combine differently per business type. A dairy = CRM + Subscriptions + Billing. A salon = CRM + Booking + Membership. This means unlimited industries without code rewrites.</p>
</div>
</div>

</div>
</body>
</html>'''
    return HTMLResponse(content=html)
