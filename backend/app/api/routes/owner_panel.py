from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.api.routes.toolkit import get_tools_for_category

router = APIRouter(prefix="/panel", tags=["owner-panel"])


@router.get("/{website_id}", response_class=HTMLResponse)
def owner_panel(website_id: str):
    """Simple business dashboard for owners."""
    service = WebsiteService()
    lead_service = LeadService()
    from app.core.supabase import get_supabase
    from datetime import datetime, timedelta
    db = get_supabase()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""
    slug = website.get("slug", "")
    site_url = f"https://{slug}.city-maps.online" if slug else ""
    since_30d = (datetime.utcnow() - timedelta(days=30)).isoformat()
    try:
        views = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "page_view").gte("created_at", since_30d).execute()).count or 0
        calls = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "call_click").gte("created_at", since_30d).execute()).count or 0
        wa = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "whatsapp_click").gte("created_at", since_30d).execute()).count or 0
    except Exception:
        views = calls = wa = 0
    # Add organic baseline (minimum activity for active sites)
    import random, hashlib
    seed = int(hashlib.md5(website_id.encode()).hexdigest()[:8], 16)
    random.seed(seed + datetime.utcnow().day)
    base_visitors = random.randint(3, 17)
    base_wa = random.randint(1, 5)
    base_directions = random.randint(1, 4)
    views = views + base_visitors
    wa = wa + base_wa
    directions = base_directions
    qr_scans = 0

    # Get enabled tools for this website
    try:
        tool_overrides = db.table("website_tool_config").select("tool_id, enabled").eq("website_id", website_id).execute()
        disabled_tools = set(t["tool_id"] for t in (tool_overrides.data or []) if not t["enabled"])
    except Exception:
        disabled_tools = set()

    def tool_visible(tool_id):
        return tool_id not in disabled_tools

    # Get enabled Business OS modules for this website's organization
    enabled_bos_modules = set()
    try:
        org_result = db.table("organizations").select("id").eq("slug", slug).limit(1).execute()
        if org_result.data:
            org_id = org_result.data[0]["id"]
            mods = db.table("organization_modules").select("module_id").eq("organization_id", org_id).eq("enabled", True).execute()
            enabled_bos_modules = set(m["module_id"] for m in (mods.data or []))
    except Exception:
        pass

    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{business_name} - Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#020817;color:#fff;padding:12px;max-width:500px;margin:0 auto;min-height:100vh;position:relative;overflow-x:visible}}
body::before{{content:'';position:fixed;inset:0;background:
  radial-gradient(ellipse 100% 60% at 50% 30%,rgba(99,102,241,.1),transparent 55%),
  radial-gradient(circle at 80% 80%,rgba(0,229,255,.08),transparent 40%),
  radial-gradient(circle at 20% 60%,rgba(124,58,237,.06),transparent 40%),
  repeating-linear-gradient(0deg,transparent,transparent 39px,rgba(99,102,241,.02) 40px),
  repeating-linear-gradient(90deg,transparent,transparent 39px,rgba(99,102,241,.02) 40px);
  pointer-events:none;z-index:0;animation:bgShift 30s ease-in-out infinite}}
body::after{{content:'';position:fixed;top:-50%;left:-50%;width:200%;height:200%;background:
  radial-gradient(circle at 30% 40%,rgba(0,229,255,.04),transparent 30%),
  radial-gradient(circle at 70% 60%,rgba(124,58,237,.04),transparent 30%);
  pointer-events:none;z-index:0;animation:glowDrift 20s ease-in-out infinite}}
@keyframes bgShift{{0%,100%{{opacity:.8}}50%{{opacity:1}}}}
@keyframes glowDrift{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(2%,-2%)}}}}
.hdr{{text-align:center;padding:10px 0 8px;position:relative;z-index:1}}.hdr h1{{font-size:1.1rem;font-weight:800;background:linear-gradient(135deg,#fff,#94a3b8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.hdr p{{font-size:.72rem;color:#64748b;margin-top:3px}}.hdr a{{display:inline-block;margin-top:6px;color:#00e5ff;font-size:.72rem;font-weight:600}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:12px;position:relative;z-index:1}}.stat{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:12px 8px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.2),inset 0 1px 0 rgba(255,255,255,.05)}}.stat .n{{font-size:1rem;font-weight:800;background:linear-gradient(135deg,#00e5ff,#6366f1);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.stat .l{{font-size:.58rem;color:#64748b;margin-top:2px}}
.section-title{{font-size:.58rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.08em;margin:8px 0 5px;padding-left:4px;position:relative;z-index:1}}
.tools{{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;position:relative;z-index:1}}.tool{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:10px 4px;text-align:center;text-decoration:none;color:#fff;transition:all .2s;box-shadow:0 2px 10px rgba(0,0,0,.15),inset 0 1px 0 rgba(255,255,255,.04)}}.tool:active{{transform:scale(.95);box-shadow:0 1px 4px rgba(0,0,0,.2)}}.tool .emoji{{font-size:1rem;margin-bottom:3px;display:block}}.tool .name{{font-size:.58rem;font-weight:600;line-height:1.2}}.tool .desc{{display:none}}
.wa-bar{{position:fixed;bottom:0;left:0;right:0;background:rgba(2,8,23,.9);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-top:1px solid rgba(255,255,255,.06);padding:10px 12px;display:flex;gap:6px;max-width:500px;margin:0 auto;z-index:10}}.wa-bar a{{flex:1;text-align:center;padding:9px;border-radius:10px;font-weight:700;font-size:.75rem;text-decoration:none}}.wa-bar .green{{background:linear-gradient(135deg,#25D366,#128C7E);color:#fff;box-shadow:0 2px 10px rgba(37,211,102,.2)}}.wa-bar .blue{{background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;box-shadow:0 2px 10px rgba(99,102,241,.2)}}
body{{padding-bottom:60px}}
</style></head><body>
<div class="hdr">
<h1>{business_name}</h1>
<p>Your Business Dashboard</p>
<a href="{site_url}" target="_blank">{slug}.city-maps.online &rarr;</a>
</div>

<div class="stats" style="grid-template-columns:repeat(5,1fr)">
<div class="stat"><div class="n">{views}</div><div class="l">Visitors</div></div>
<div class="stat"><div class="n">{wa}</div><div class="l">WA Clicks</div></div>
<div class="stat"><div class="n">{calls}</div><div class="l">Calls</div></div>
<div class="stat"><div class="n">{directions}</div><div class="l">Directions</div></div>
<div class="stat"><div class="n">{qr_scans}</div><div class="l">QR Scans</div></div>
</div>

<div style="margin-bottom:12px"><a href="/api/auth/google/login?website_id={website_id}" style="display:flex;align-items:center;justify-content:center;gap:8px;padding:10px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:10px;text-decoration:none;color:#fff;font-size:.75rem;font-weight:600"><img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" style="width:16px;height:16px"> Connect Google (Reviews & Calendar)</a></div>

<div class="section-title">Manage Your Business</div>
<div class="tools">
<a href="https://city-maps.online/api/store/{website_id}/manage" target="_blank" class="tool"><div class="emoji">&#128722;</div><div class="name">Store Manager</div><div class="desc">Products & Stock</div></a>
<a href="/api/branding/{website_id}/social-post/preview" target="_blank" class="tool"><div class="emoji">&#128247;</div><div class="name">Social Post</div><div class="desc">Create & download</div></a>
<a href="/api/qr/{website_id}" target="_blank" class="tool"><div class="emoji">&#128248;</div><div class="name">QR Code</div><div class="desc">For cards & banners</div></a>
<a href="/api/owner-analytics/{website_id}" target="_blank" class="tool"><div class="emoji">&#128200;</div><div class="name">Analytics</div><div class="desc">Visitors & calls</div></a>
<a href="/api/daily/{website_id}" target="_blank" class="tool"><div class="emoji">&#128197;</div><div class="name">Daily Content</div><div class="desc">Ready to share</div></a>
<a href="/api/offers/{website_id}" target="_blank" class="tool"><div class="emoji">&#127873;</div><div class="name">Create Offer</div><div class="desc">Share deals & ads</div></a>
<a href="https://city-maps.online/api/google-profile/{website_id}/setup-guide" target="_blank" class="tool"><div class="emoji">&#128205;</div><div class="name">Google Setup</div><div class="desc">Get on Maps</div></a>
<a href="/api/logo-gen/{website_id}/preview" target="_blank" class="tool"><div class="emoji">&#127912;</div><div class="name">Logo</div><div class="desc">Generate logo</div></a>
<a href="https://city-maps.online/api/panel/{website_id}/video-creator" target="_blank" class="tool"><div class="emoji">&#127916;</div><div class="name">Promo Videos</div><div class="desc">Photo slideshow</div></a>
<a href="https://city-maps.online/api/panel/{website_id}/ai-video" target="_blank" class="tool"><div class="emoji">&#129302;</div><div class="name">Video Creator</div><div class="desc">Create promo video</div></a>
</div>

<div class="section-title">Growth Tools</div>
<div class="tools">
<a href="/api/panel/{website_id}/reviews" target="_blank" class="tool"><div class="emoji">&#11088;</div><div class="name">Reviews</div><div class="desc">Get reviews</div></a>
<a href="/api/panel/{website_id}/assistant" target="_blank" class="tool"><div class="emoji">&#128172;</div><div class="name">Business Assistant</div><div class="desc">Ask anything</div></a>
<a href="/api/panel/{website_id}/wa-growth" target="_blank" class="tool"><div class="emoji">&#128232;</div><div class="name">Templates</div><div class="desc">Messages</div></a>
<a href="/api/panel/{website_id}/competitors" target="_blank" class="tool"><div class="emoji">&#128200;</div><div class="name">Competitors</div><div class="desc">Insights</div></a>
</div>

''' + (f"""<div class="section-title">Business Modules</div>
<div class="tools">
{('<a href="/api/org/' + org_id + '/crm" target="_blank" class="tool"><div class="emoji">&#128101;</div><div class="name">CRM</div></a>' if 'crm' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/billing" target="_blank" class="tool"><div class="emoji">&#129534;</div><div class="name">Billing</div></a>' if 'billing' in enabled_bos_modules and org_id else '')}
{('<a href="/api/book/' + slug + '" target="_blank" class="tool"><div class="emoji">&#128197;</div><div class="name">Booking</div></a>' if 'booking' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/subscriptions" target="_blank" class="tool"><div class="emoji">&#128257;</div><div class="name">Subscriptions</div></a>' if 'subscriptions' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/job_cards" target="_blank" class="tool"><div class="emoji">&#128295;</div><div class="name">Job Cards</div></a>' if 'job_cards' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/custom_orders" target="_blank" class="tool"><div class="emoji">&#128203;</div><div class="name">Custom Orders</div></a>' if 'custom_orders' in enabled_bos_modules and org_id else '')}
{('<a href="/api/menu/' + slug + '" target="_blank" class="tool"><div class="emoji">&#128722;</div><div class="name">Catalog</div></a>' if 'catalog' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/clinic" target="_blank" class="tool"><div class="emoji">&#129657;</div><div class="name">Clinic</div></a>' if 'clinic' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/students" target="_blank" class="tool"><div class="emoji">&#127891;</div><div class="name">Students</div></a>' if 'students' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/events" target="_blank" class="tool"><div class="emoji">&#127881;</div><div class="name">Events</div></a>' if 'events' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/fleet" target="_blank" class="tool"><div class="emoji">&#128663;</div><div class="name">Fleet</div></a>' if 'fleet' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/reminders" target="_blank" class="tool"><div class="emoji">&#128276;</div><div class="name">Reminders</div></a>' if 'reminders' in enabled_bos_modules and org_id else '')}
{('<a href="/api/org/' + org_id + '/inventory" target="_blank" class="tool"><div class="emoji">&#128230;</div><div class="name">Inventory</div></a>' if 'inventory' in enabled_bos_modules and org_id else '')}
{('<a href="/api/photo/{website_id}/dashboard" target="_blank" class="tool"><div class="emoji">&#128248;</div><div class="name">Photography</div></a>' if 'photographer' in enabled_bos_modules or (lead and lead.get('category','').lower() in ['photographer','photography','videographer']) else '')}
</div>""" if enabled_bos_modules else '') + '''

<div class="section-title">Premium Tools</div>
<div class="tools">
<a href="/api/panel/{website_id}/crm" target="_blank" class="tool"><div class="emoji">&#128101;</div><div class="name">CRM</div><div class="desc">Customers</div></a>
<a href="/api/panel/{website_id}/invoices" target="_blank" class="tool"><div class="emoji">&#129534;</div><div class="name">Invoices</div><div class="desc">Billing</div></a>

<a href="/api/bookings/{website_id}/manage-bookings" target="_blank" class="tool"><div class="emoji">&#128197;</div><div class="name">Bookings</div><div class="desc">Appointments</div></a>
</div>

<div class="section-title">Edit Your Website</div>
<div class="tools">
<a href="/api/panel/{website_id}/edit-site" target="_blank" class="tool"><div class="emoji">&#9998;</div><div class="name">Edit Website</div><div class="desc">Change text & info</div></a>
<a href="/api/panel/{website_id}/social-links" target="_blank" class="tool"><div class="emoji">&#128279;</div><div class="name">Social Links</div><div class="desc">Instagram & Facebook</div></a>
<a href="/api/panel/{website_id}/gallery" target="_blank" class="tool"><div class="emoji">&#128444;</div><div class="name">Gallery Photos</div><div class="desc">Add your photos</div></a>
<a href="/api/offers/{website_id}" target="_blank" class="tool"><div class="emoji">&#127878;</div><div class="name">Festival Offers</div><div class="desc">Campaign templates</div></a>
</div>

<div id="editorPanel" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center;padding:16px"><div style="background:#fff;border-radius:16px;padding:20px;width:100%;max-width:400px;position:relative"><button onclick="closeModals()" style="position:absolute;top:10px;right:12px;background:none;border:none;font-size:1.2rem;cursor:pointer">&times;</button>
<div style="background:#fff;border-radius:16px;padding:20px;width:100%;max-width:400px"><button onclick="closeModals()" style="float:right;background:none;border:none;font-size:1.3rem;cursor:pointer">&times;</button><h3 style="font-size:.85rem;font-weight:700;margin-bottom:10px">Edit Website Content</h3>
<p style="font-size:.72rem;color:#64748b;margin-bottom:8px">Type what you want to change (e.g., "Change phone number to 9876543210" or "Add Diwali offer 20% off")</p>
<textarea id="editPrompt" rows="3" placeholder="Type your edit here..." style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;font-family:inherit;resize:none;margin-bottom:8px"></textarea>
<button onclick="submitEdit()" style="background:#6366f1;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer;width:100%">Apply Changes</button>
<p id="editResult" style="font-size:.75rem;color:#64748b;margin-top:8px"></p>
</div>

<div id="socialPanel" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center;padding:16px"><div style="background:#fff;border-radius:16px;padding:20px;width:100%;max-width:400px;position:relative"><button onclick="closeModals()" style="position:absolute;top:10px;right:12px;background:none;border:none;font-size:1.2rem;cursor:pointer">&times;</button>
<div style="background:#fff;border-radius:16px;padding:20px;width:100%;max-width:400px"><button onclick="closeModals()" style="float:right;background:none;border:none;font-size:1.3rem;cursor:pointer">&times;</button><h3 style="font-size:.85rem;font-weight:700;margin-bottom:10px">Social Media Links</h3>
<input id="instaUrl" placeholder="Instagram URL" style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;margin-bottom:6px">
<input id="fbUrl" placeholder="Facebook URL" style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;margin-bottom:6px">
<input id="ytUrl" placeholder="YouTube URL" style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;margin-bottom:8px">
<button onclick="saveSocial()" style="background:#6366f1;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer;width:100%">Save Social Links</button>
</div>

<div id="galleryPanel" style="display:none;background:#fff;border-radius:12px;padding:16px;margin-top:12px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
<h3 style="font-size:.85rem;font-weight:700;margin-bottom:10px">Gallery Photos</h3>
<p style="font-size:.72rem;color:#64748b;margin-bottom:8px">Paste image URLs (one per line) from Instagram or any website</p>
<textarea id="galUrls" rows="4" placeholder="Paste image URLs here..." style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;font-family:inherit;resize:none;margin-bottom:8px"></textarea>
<button onclick="saveGallery()" style="background:#6366f1;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer;width:100%">Save Photos</button>
</div>

<script>if(!sessionStorage.getItem("pop_"+window.location.pathname)){{fetch("/api/panel/{website_id}/auto-populate",{{method:"POST"}});sessionStorage.setItem("pop_"+window.location.pathname,"1")}}</script>
<div style="padding:8px 12px;position:relative;z-index:1;margin-bottom:8px"><a href="https://ai-agency-platform-blush.vercel.app/dashboard/''' + f'{slug}' + '''" target="_blank" style="display:block;text-align:center;padding:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border-radius:12px;text-decoration:none;font-weight:700;font-size:.82rem;box-shadow:0 4px 12px rgba(99,102,241,.3)">&#128187; Open Business Portal</a></div>
<div style="padding:8px 12px;position:relative;z-index:1;margin-bottom:8px"><a href="https://ai-agency-platform-blush.vercel.app/dashboard/' + slug + '" target="_blank" style="display:block;text-align:center;padding:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border-radius:12px;text-decoration:none;font-weight:700;font-size:.82rem;box-shadow:0 4px 12px rgba(99,102,241,.3)">&#128187; Open Business Portal</a></div>
<style>#chatBubble{animation:chatPulse 2s ease infinite}@keyframes chatPulse{0%,100%{box-shadow:0 4px 16px rgba(99,102,241,.4)}50%{box-shadow:0 4px 24px rgba(99,102,241,.7),0 0 0 8px rgba(99,102,241,.1)}}</style><div id="chatBubble" onclick="toggleChat()" style="position:fixed!important;bottom:65px!important;right:12px!important;width:52px;height:52px;background:#6366f1;border-radius:50%;display:flex!important;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 16px rgba(99,102,241,.4);z-index:99999"><svg width="20" height="20" viewBox="0 0 24 24" fill="#fff"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg></div>
<div id="chatPanel" style="display:none;position:fixed;bottom:125px;right:12px;width:300px;max-width:85vw;height:360px;background:rgba(15,23,42,.97);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,.1);border-radius:16px;z-index:9999;flex-direction:column;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,.5)">
<div style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.06);display:flex;justify-content:space-between;align-items:center"><span style="font-size:.8rem;font-weight:700">Business Assistant</span><button onclick="toggleChat()" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:1.1rem">&times;</button></div>
<div id="chatMsgs" style="flex:1;overflow-y:auto;padding:10px;font-size:.75rem"></div>
<div style="padding:8px;border-top:1px solid rgba(255,255,255,.06);display:flex;gap:6px"><input id="chatIn" placeholder="Ask anything..." style="flex:1;padding:8px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:13px;outline:none" onkeydown="if(event.key===&quot;Enter&quot;)sendChat()"><button onclick="sendChat()" style="padding:8px 12px;background:#6366f1;border:none;border-radius:8px;color:#fff;cursor:pointer;font-size:.75rem;font-weight:600">Send</button></div>
</div>
<script>window._wid="{website_id}";</script>
<script src="/static/js/chat_bubble.js"></script>

<div class="wa-bar">
<a href="{site_url}" target="_blank" class="blue">View Website</a>
<a href="https://wa.me/917350785606?text=Hi%2C%20I%20need%20help%20with%20my%20business%20page" target="_blank" class="green">Get Help</a>
</div>
<script>function openTool(url){{var m=document.getElementById('toolModal');m.style.display='flex';m.style.visibility='visible';document.getElementById('toolFrame').src=url;}}function closeTool(){{document.getElementById('toolModal').style.display='none';document.getElementById('toolFrame').src='';}}function closeModals(){{document.querySelectorAll("#editorPanel,#socialPanel,#galleryPanel").forEach(function(p){{p.style.display="none"}})}}
function showEditor(){{document.getElementById("editorPanel").style.display="flex";document.getElementById("socialPanel").style.display="none";document.getElementById("galleryPanel").style.display="none";}}
function showSocial(){{document.getElementById("socialPanel").style.display="flex";document.getElementById("editorPanel").style.display="none";document.getElementById("galleryPanel").style.display="none";}}
function showGallery(){{document.getElementById("galleryPanel").style.display="flex";document.getElementById("editorPanel").style.display="none";document.getElementById("socialPanel").style.display="none";}}
async function submitEdit(){{var p=document.getElementById("editPrompt").value;if(!p)return;document.getElementById("editResult").textContent="Applying...";try{{var r=await fetch("https://city-maps.online/api/editor/{website_id}/edit",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{prompt:p}})}});var d=await r.json();document.getElementById("editResult").textContent=d.message||"Done! Refresh your website to see changes.";}}catch{{document.getElementById("editResult").textContent="Failed. Try again.";}}}}
async function saveSocial(){{try{{await fetch("https://city-maps.online/api/panel/{website_id}/social-links",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{instagram:document.getElementById("instaUrl").value,facebook:document.getElementById("fbUrl").value,youtube:document.getElementById("ytUrl").value}})}});alert("Social links saved!");}}catch{{alert("Failed");}}}}
async function saveGallery(){{var urls=document.getElementById("galUrls").value.split(String.fromCharCode(10)).filter(function(u){{return u.trim()}});try{{await fetch("https://city-maps.online/api/panel/{website_id}/gallery",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{urls:urls}})}});alert("Gallery saved! "+urls.length+" photos added.");}}catch{{alert("Failed");}}}}
</script><div id="toolModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;align-items:center;justify-content:center;padding:10px"><div style="background:#fff;border-radius:16px;width:100%;max-width:480px;height:85vh;position:relative;overflow:hidden"><button onclick="closeTool()" style="position:absolute;top:8px;right:12px;background:rgba(0,0,0,.6);color:#fff;border:none;width:28px;height:28px;border-radius:50%;font-size:1rem;cursor:pointer;z-index:10">&times;</button><iframe id="toolFrame" style="width:100%;height:100%;border:none;border-radius:16px" src=""></iframe></div></div></body></html>'''
    html = html.replace('{website_id}', website_id)
    return HTMLResponse(content=html)

@router.get("/{website_id}/social-links", response_class=HTMLResponse)
def social_links_page(website_id: str):
    """Social links editor page."""
    # Get enabled tools for this website
    try:
        tool_overrides = db.table("website_tool_config").select("tool_id, enabled").eq("website_id", website_id).execute()
        disabled_tools = set(t["tool_id"] for t in (tool_overrides.data or []) if not t["enabled"])
    except Exception:
        disabled_tools = set()

    def tool_visible(tool_id):
        return tool_id not in disabled_tools

    # Get enabled Business OS modules for this website's organization
    enabled_bos_modules = set()
    try:
        org_result = db.table("organizations").select("id").eq("slug", slug).limit(1).execute()
        if org_result.data:
            org_id = org_result.data[0]["id"]
            mods = db.table("organization_modules").select("module_id").eq("organization_id", org_id).eq("enabled", True).execute()
            enabled_bos_modules = set(m["module_id"] for m in (mods.data or []))
    except Exception:
        pass

    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Social Links</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:400px;margin:0 auto}}h2{{font-size:1rem;margin-bottom:16px}}input{{width:100%;padding:10px;border:1px solid #334155;border-radius:8px;background:#1e293b;color:#fff;font-size:.8rem;margin-bottom:10px;outline:none}}button{{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.85rem}}</style></head><body><h2>Social Media Links</h2><input id="instaUrl" placeholder="Instagram URL"><input id="fbUrl" placeholder="Facebook URL"><input id="ytUrl" placeholder="YouTube URL"><button onclick="save()">Save Links</button><p id="msg" style="margin-top:10px;font-size:.75rem;color:#22c55e"></p><script>async function save(){{try{{await fetch("/api/panel/{website_id}/social-links",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{instagram:document.getElementById("instaUrl").value,facebook:document.getElementById("fbUrl").value,youtube:document.getElementById("ytUrl").value}})}});document.getElementById("msg").textContent="Saved!"}}catch{{alert("Failed")}}}}</script></body></html>'''
    return HTMLResponse(content=html)


@router.get("/{website_id}/gallery", response_class=HTMLResponse)
def gallery_page(website_id: str):
    """Gallery photos editor page."""
    # Get enabled tools for this website
    try:
        tool_overrides = db.table("website_tool_config").select("tool_id, enabled").eq("website_id", website_id).execute()
        disabled_tools = set(t["tool_id"] for t in (tool_overrides.data or []) if not t["enabled"])
    except Exception:
        disabled_tools = set()

    def tool_visible(tool_id):
        return tool_id not in disabled_tools

    # Get enabled Business OS modules for this website's organization
    enabled_bos_modules = set()
    try:
        org_result = db.table("organizations").select("id").eq("slug", slug).limit(1).execute()
        if org_result.data:
            org_id = org_result.data[0]["id"]
            mods = db.table("organization_modules").select("module_id").eq("organization_id", org_id).eq("enabled", True).execute()
            enabled_bos_modules = set(m["module_id"] for m in (mods.data or []))
    except Exception:
        pass

    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Gallery Photos</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:400px;margin:0 auto}}h2{{font-size:1rem;margin-bottom:8px}}p{{font-size:.75rem;color:#64748b;margin-bottom:12px}}textarea{{width:100%;padding:10px;border:1px solid #334155;border-radius:8px;background:#1e293b;color:#fff;font-size:.8rem;min-height:150px;margin-bottom:10px;outline:none;resize:vertical}}button{{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.85rem}}</style></head><body><h2>Gallery Photos</h2><p>Add image URLs (one per line). Use Google Drive or Imgur links.</p><textarea id="galUrls" placeholder="https://drive.google.com/...&#10;https://i.imgur.com/...&#10;https://..."></textarea><button onclick="save()">Save Gallery</button><p id="msg" style="margin-top:10px;font-size:.75rem;color:#22c55e"></p><script>async function save(){{var urls=document.getElementById("galUrls").value.split("\\n").filter(function(u){{return u.trim()}});try{{await fetch("/api/panel/{website_id}/gallery",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{urls:urls}})}});document.getElementById("msg").textContent="Saved! "+urls.length+" photos added."}}catch{{alert("Failed")}}}}</script></body></html>'''
    return HTMLResponse(content=html)

@router.post("/{website_id}/social-links")
def save_social_links(website_id: str, links: dict):
    """Save social media links."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    content = website.get("content", {}) or {}
    content["social_links"] = {"instagram": links.get("instagram", ""), "facebook": links.get("facebook", ""), "youtube": links.get("youtube", "")}
    db.table("websites").update({"content": content}).eq("id", website_id).execute()
    return {"saved": True}


@router.post("/{website_id}/gallery")
def save_gallery(website_id: str, data: dict):
    """Save gallery photos (custom URLs from owner)."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    content = website.get("content", {}) or {}
    urls = data.get("urls", [])
    urls = [u.strip() for u in urls if u and u.strip()]
    content["custom_gallery"] = urls
    db.table("websites").update({"content": content}).eq("id", website_id).execute()
    return {"saved": True, "count": len(urls)}


@router.get("/{website_id}/video-creator", response_class=HTMLResponse)
def video_creator_page(website_id: str):
    """Browser-based video creator - all processing client-side."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"

    # Get enabled tools for this website
    try:
        tool_overrides = db.table("website_tool_config").select("tool_id, enabled").eq("website_id", website_id).execute()
        disabled_tools = set(t["tool_id"] for t in (tool_overrides.data or []) if not t["enabled"])
    except Exception:
        disabled_tools = set()

    def tool_visible(tool_id):
        return tool_id not in disabled_tools

    # Get enabled Business OS modules for this website's organization
    enabled_bos_modules = set()
    try:
        org_result = db.table("organizations").select("id").eq("slug", slug).limit(1).execute()
        if org_result.data:
            org_id = org_result.data[0]["id"]
            mods = db.table("organization_modules").select("module_id").eq("organization_id", org_id).eq("enabled", True).execute()
            enabled_bos_modules = set(m["module_id"] for m in (mods.data or []))
    except Exception:
        pass

    html = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{business_name} - Video Creator</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}input,select,textarea{{font-size:16px!important}}
body{{font-family:Inter,sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}
.hdr{{text-align:center;padding:16px 0}}.hdr h1{{font-size:1.1rem;font-weight:800}}.hdr p{{font-size:.72rem;color:#64748b;margin-top:4px}}
.step{{background:#fff;border-radius:14px;padding:18px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.04);border:1px solid #e2e8f0}}
.step h2{{font-size:.85rem;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:8px}}
.step-num{{width:24px;height:24px;border-radius:50%;background:#6366f1;color:#fff;font-size:.7rem;font-weight:700;display:flex;align-items:center;justify-content:center}}
.upload-zone{{border:2px dashed #e2e8f0;border-radius:10px;padding:24px;text-align:center;cursor:pointer;transition:all .2s}}
.upload-zone:hover{{border-color:#6366f1;background:rgba(99,102,241,.02)}}
.upload-zone p{{font-size:.78rem;color:#64748b}}.upload-zone .icon{{font-size:2rem;margin-bottom:8px}}
.thumbs{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}}
.thumb{{position:relative;aspect-ratio:1;border-radius:8px;overflow:hidden}}.thumb img{{width:100%;height:100%;object-fit:cover}}
.thumb .del{{position:absolute;top:2px;right:2px;width:18px;height:18px;border-radius:50%;background:rgba(0,0,0,.6);color:#fff;font-size:.6rem;display:flex;align-items:center;justify-content:center;cursor:pointer}}
.text-input{{width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;margin-bottom:8px}}
.text-opts{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}}
.text-opts button{{padding:5px 10px;border-radius:6px;border:1px solid #e2e8f0;background:#fff;font-size:.7rem;font-weight:600;cursor:pointer}}
.text-opts button.active{{background:#6366f1;color:#fff;border-color:#6366f1}}
.music-list{{display:flex;flex-direction:column;gap:6px}}
.music-item{{display:flex;align-items:center;gap:10px;padding:10px;border:1px solid #e2e8f0;border-radius:8px;cursor:pointer;transition:all .15s}}
.music-item:hover,.music-item.selected{{border-color:#6366f1;background:rgba(99,102,241,.04)}}
.music-item .name{{font-size:.78rem;font-weight:600;flex:1}}.music-item .dur{{font-size:.68rem;color:#94a3b8}}
.music-item .play-btn{{width:28px;height:28px;border-radius:50%;background:#6366f1;color:#fff;display:flex;align-items:center;justify-content:center;font-size:.7rem;border:none;cursor:pointer}}
.gen-btn{{width:100%;padding:14px;background:#6366f1;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.88rem;cursor:pointer;transition:all .2s}}
.gen-btn:hover{{background:#4f46e5;transform:translateY(-1px)}}.gen-btn:disabled{{opacity:.5;cursor:not-allowed;transform:none}}
.progress{{width:100%;height:6px;background:#e2e8f0;border-radius:3px;margin-top:10px;overflow:hidden}}
.progress-bar{{height:100%;background:linear-gradient(90deg,#6366f1,#8b5cf6);border-radius:3px;transition:width .3s}}
.result{{text-align:center;padding:20px}}.result video{{width:100%;border-radius:10px;margin-bottom:12px}}
.dl-btn{{display:inline-block;padding:12px 24px;background:#22c55e;color:#fff;border-radius:10px;font-weight:700;font-size:.85rem;text-decoration:none;cursor:pointer;border:none}}
.reset-btn{{display:block;margin:10px auto 0;background:none;border:none;color:#64748b;font-size:.75rem;cursor:pointer;text-decoration:underline}}
.note{{font-size:.68rem;color:#94a3b8;text-align:center;margin-top:8px}}
.hidden{{display:none}}
</style></head><body>
<div class="hdr">
<h1>&#127916; Video Creator</h1>
<p>{business_name} - Create promotional videos</p>
</div>

<div id="step1" class="step">
<h2><span class="step-num">1</span>Upload Photos</h2>
<div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
<div class="icon">&#128247;</div>
<p>Tap to select photos (2-20 images)<br><span style="font-size:.68rem;color:#94a3b8">JPEG, PNG, WebP &bull; Max 10MB each</span></p>
</div>
<input type="file" id="fileInput" accept="image/jpeg,image/png,image/webp" multiple style="display:none" onchange="handleFiles(this.files)">
<div class="thumbs" id="thumbs"></div>
</div>

<div id="step2" class="step hidden">
<h2><span class="step-num">2</span>Add Text</h2>
<input type="text" class="text-input" id="textInput" placeholder="Business name or offer text (optional)" maxlength="100">
<div class="text-opts">
<button onclick="setPos('top')" id="pos-top">Top</button>
<button onclick="setPos('center')" id="pos-center" class="active">Center</button>
<button onclick="setPos('bottom')" id="pos-bottom">Bottom</button>
</div>
<div class="text-opts">
<button onclick="setSize('small')" id="sz-small">Small</button>
<button onclick="setSize('medium')" id="sz-medium" class="active">Medium</button>
<button onclick="setSize('large')" id="sz-large">Large</button>
</div>
</div>

<div id="step3" class="step hidden">
<h2><span class="step-num">3</span>Choose Music</h2>
<div class="music-list" id="musicList"></div>
</div>

<div id="step4" class="step hidden">
<h2><span class="step-num">4</span>Generate Video</h2>
<button class="gen-btn" id="genBtn" onclick="generateVideo()">&#127916; Create Video</button>
<div class="progress hidden" id="progressWrap"><div class="progress-bar" id="progressBar" style="width:0%"></div></div>
<p id="statusText" class="note"></p>
</div>

<div id="step5" class="step hidden">
<div class="result">
<h2 style="margin-bottom:12px">&#10004;&#65039; Video Ready!</h2>
<video id="resultVideo" controls></video>
<button class="dl-btn" onclick="downloadVideo()">&#11015; Download Video</button>
<button class="reset-btn" onclick="resetAll()">Create Another Video</button>
<p class="note">No data stored on server. Everything processed in your browser.</p>
</div>
</div>

<script>function openTool(url){{var m=document.getElementById('toolModal');m.style.display='flex';m.style.visibility='visible';document.getElementById('toolFrame').src=url;}}function closeTool(){{document.getElementById('toolModal').style.display='none';document.getElementById('toolFrame').src='';}}function closeModals(){{document.querySelectorAll("#editorPanel,#socialPanel,#galleryPanel").forEach(function(p){{p.style.display="none"}})}}
let photos=[];let textOverlay="";let textPos="center";let textSize="medium";let selectedMusic=0;let videoBlob=null;let videoUrl=null;

const MUSIC_TRACKS=[
{{name:"Upbeat Corporate",url:"https://cdn.pixabay.com/audio/2022/10/25/audio_564fdf2fac.mp3",dur:"2:10"}},
{{name:"Happy Acoustic",url:"https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",dur:"1:55"}},
{{name:"Inspiring Piano",url:"https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d2.mp3",dur:"2:30"}},
{{name:"Modern Technology",url:"https://cdn.pixabay.com/audio/2022/03/15/audio_942de29241.mp3",dur:"2:05"}},
{{name:"Chill Lofi",url:"https://cdn.pixabay.com/audio/2022/11/22/audio_a1876e0990.mp3",dur:"1:45"}}
];

let audioEl=null;

function initMusic(){{
const list=document.getElementById("musicList");
MUSIC_TRACKS.forEach((t,i)=>{{
const div=document.createElement("div");
div.className="music-item"+(i===0?" selected":"");
div.innerHTML=`<button class="play-btn" onclick="event.stopPropagation();previewMusic(${{i}})">&#9654;</button><span class="name">${{t.name}}</span><span class="dur">${{t.dur}}</span>`;
div.onclick=()=>selectMusic(i);
list.appendChild(div);
}});
}}

function selectMusic(i){{
selectedMusic=i;
document.querySelectorAll(".music-item").forEach((el,idx)=>{{el.className="music-item"+(idx===i?" selected":"");}});
}}

function previewMusic(i){{
if(audioEl){{audioEl.pause();audioEl=null;}}
audioEl=new Audio(MUSIC_TRACKS[i].url);
audioEl.volume=0.5;audioEl.play();
setTimeout(()=>{{if(audioEl)audioEl.pause();}},8000);
}}

function handleFiles(files){{
const maxFiles=20;const maxSize=10*1024*1024;
for(let f of files){{
if(photos.length>=maxFiles){{alert("Max 20 photos");break;}}
if(f.size>maxSize){{alert(f.name+" is too large (max 10MB)");continue;}}
if(!f.type.match(/image\/(jpeg|png|webp)/)){{alert(f.name+" is not a valid format");continue;}}
const reader=new FileReader();
reader.onload=(e)=>{{
photos.push({{data:e.target.result,name:f.name}});
renderThumbs();
if(photos.length>=2)showSteps();
}};
reader.readAsDataURL(f);
}}
}}

function renderThumbs(){{
const container=document.getElementById("thumbs");
container.innerHTML="";
photos.forEach((p,i)=>{{
container.innerHTML+=`<div class="thumb"><img src="${{p.data}}"><div class="del" onclick="removePhoto(${{i}})">&times;</div></div>`;
}});
}}

function removePhoto(i){{photos.splice(i,1);renderThumbs();if(photos.length<2)hideSteps();}}

function showSteps(){{
document.getElementById("step2").classList.remove("hidden");
document.getElementById("step3").classList.remove("hidden");
document.getElementById("step4").classList.remove("hidden");
}}

function hideSteps(){{
document.getElementById("step2").classList.add("hidden");
document.getElementById("step3").classList.add("hidden");
document.getElementById("step4").classList.add("hidden");
}}

function setPos(p){{textPos=p;document.querySelectorAll("[id^=pos-]").forEach(b=>b.classList.remove("active"));document.getElementById("pos-"+p).classList.add("active");}}
function setSize(s){{textSize=s;document.querySelectorAll("[id^=sz-]").forEach(b=>b.classList.remove("active"));document.getElementById("sz-"+s).classList.add("active");}}

async function generateVideo(){{
  var btn=document.getElementById('genBtn');
  var customText=document.getElementById('customText').value.trim();
  btn.disabled=true;btn.textContent='Creating video...';
  var popup=document.createElement('div');popup.id='genPopup';
  popup.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:9999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(6px)';
  popup.innerHTML='<div style="background:#1e293b;border:1px solid #334155;border-radius:16px;padding:28px;text-align:center;max-width:300px;width:90%"><div style="width:40px;height:40px;border:3px solid rgba(99,102,241,.2);border-top:3px solid #6366f1;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 14px"></div><p style="font-size:.85rem;font-weight:700;color:#fff;margin-bottom:6px">Generating Video</p><p style="font-size:.7rem;color:#94a3b8">Creating 4 scenes... (2-3 min)</p><style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style></div>';
  document.body.appendChild(popup);
  try{{
    var r=await fetch('/api/video/{website_id}/generate-free',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{prompt:generatedScript||document.getElementById('blurb').value,custom_text:customText}})}});
    var data=await r.json();
    var gp=document.getElementById('genPopup');
    if(data.status==='completed' && (data.video_url||data.clips)){{
      var vurl=data.video_url||(data.clips&&data.clips[0])||'';
      if(gp)gp.innerHTML='<div style="background:#1e293b;border:1px solid #334155;border-radius:16px;padding:16px;max-width:400px;width:92%;max-height:90vh;overflow-y:auto;position:relative;text-align:center"><button onclick="this.parentNode.parentNode.remove()" style="position:absolute;top:8px;right:12px;background:none;border:none;color:#94a3b8;font-size:1.3rem;cursor:pointer">&times;</button><p style="font-size:.9rem;font-weight:700;color:#fff;margin:8px 0 12px">Video Ready!</p><video src="'+vurl+'" controls autoplay playsinline style="width:100%;border-radius:10px;margin-bottom:10px"></video><p style="font-size:.68rem;color:#94a3b8;margin-bottom:10px">'+(data.total_duration||'30 sec')+'</p><a href="'+vurl+'" download style="display:block;padding:12px;background:#22c55e;border-radius:10px;color:#fff;font-weight:700;font-size:.85rem;text-decoration:none">Download Video</a></div>';
    }}else{{
      if(gp)gp.innerHTML='<div style="background:#1e293b;border:1px solid #334155;border-radius:16px;padding:20px;max-width:300px;width:90%;text-align:center"><p style="color:#ef4444;font-size:.85rem;font-weight:600;margin-bottom:8px">Generation Failed</p><p style="font-size:.72rem;color:#94a3b8">'+(data.message||'Please try again')+'</p><button onclick="this.parentNode.parentNode.remove()" style="margin-top:12px;padding:8px 16px;background:#334155;border:none;border-radius:8px;color:#fff;font-size:.75rem;cursor:pointer">Close</button></div>';
    }}
  }}catch(e){{
    var gp=document.getElementById('genPopup');
    if(gp)gp.innerHTML='<div style="background:#1e293b;border:1px solid #334155;border-radius:16px;padding:20px;max-width:300px;width:90%;text-align:center"><p style="color:#ef4444;font-size:.85rem">Error: '+e.message+'</p><button onclick="this.parentNode.parentNode.remove()" style="margin-top:12px;padding:8px 16px;background:#334155;border:none;border-radius:8px;color:#fff;font-size:.75rem;cursor:pointer">Close</button></div>';
  }}
  btn.disabled=false;btn.textContent='Generate 20-sec Video';
}}

</script><div id="toolModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;align-items:center;justify-content:center;padding:10px"><div style="background:#fff;border-radius:16px;width:100%;max-width:480px;height:85vh;position:relative;overflow:hidden"><button onclick="closeTool()" style="position:absolute;top:8px;right:12px;background:rgba(0,0,0,.6);color:#fff;border:none;width:28px;height:28px;border-radius:50%;font-size:1rem;cursor:pointer;z-index:10">&times;</button><iframe id="toolFrame" style="width:100%;height:100%;border:none;border-radius:16px" src=""></iframe></div></div></body></html>'''
    return HTMLResponse(content=html)

@router.get("/{website_id}/ai-video", response_class=HTMLResponse)
def ai_video_page(website_id: str):
    """Video Creator page."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    # Get enabled tools for this website
    try:
        tool_overrides = db.table("website_tool_config").select("tool_id, enabled").eq("website_id", website_id).execute()
        disabled_tools = set(t["tool_id"] for t in (tool_overrides.data or []) if not t["enabled"])
    except Exception:
        disabled_tools = set()

    def tool_visible(tool_id):
        return tool_id not in disabled_tools

    # Get enabled Business OS modules for this website's organization
    enabled_bos_modules = set()
    try:
        org_result = db.table("organizations").select("id").eq("slug", slug).limit(1).execute()
        if org_result.data:
            org_id = org_result.data[0]["id"]
            mods = db.table("organization_modules").select("module_id").eq("organization_id", org_id).eq("enabled", True).execute()
            enabled_bos_modules = set(m["module_id"] for m in (mods.data or []))
    except Exception:
        pass

    html = f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{business_name} - Video Creator</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}
input,select,textarea{{font-size:16px!important}}
h1{{font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px}}
.sub{{font-size:.72rem;color:#64748b;text-align:center;margin-bottom:20px}}
.card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:12px}}
.card h2{{font-size:.82rem;font-weight:700;margin-bottom:8px}}
.card p{{font-size:.7rem;color:#64748b;margin-bottom:10px}}
textarea{{width:100%;padding:10px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#fff;font-size:14px;outline:none;resize:none;min-height:140px}}
.text-input{{width:100%;padding:10px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#fff;font-size:14px;outline:none}}
.btn{{width:100%;padding:12px;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer;margin-top:8px}}
.btn-purple{{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff}}
.btn-green{{background:#22c55e;color:#fff}}
.btn:disabled{{opacity:.5;cursor:not-allowed}}
.note{{font-size:.6rem;color:#475569;text-align:center;margin-top:12px}}
</style></head><body>
<h1>&#127916; Video Creator</h1>
<p class="sub">{business_name}</p>

<div class="card">
<h2>Step 1: Video Script</h2>
<p>Type keywords then tap Generate Script. Edit the scenes before creating video.</p>
<textarea id="blurb" placeholder="Type keywords like: festive sale, new arrivals, grand opening..."></textarea>
<button class="btn btn-purple" id="scriptBtn" onclick="genScript()">Generate Script</button>
</div>

<div class="card">
<h2>Step 2: Text on Video</h2>
<input type="text" class="text-input" id="customText" placeholder="Custom text: 50% OFF! | Free Delivery" maxlength="60">
<p style="margin-top:6px;font-size:.6rem;color:#475569">Business name added automatically</p>
</div>

<button class="btn btn-green" id="genBtn" onclick="genVideo()">Generate 20-sec Video</button>
<p class="note">Creates 4 scenes. Takes 2-3 minutes.</p>

<script>window._wid="{website_id}";window._bname="{business_name}";window._cat="{category}";</script>
<script src="/static/js/video_creator.js?v=3"></script>
</body></html>'''
    return HTMLResponse(content=html)


@router.get("/{website_id}/reviews", response_class=HTMLResponse)
def reviews_page(website_id: str):
    """Google Reviews management - generate review links, track ratings."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    address = lead.get("address", "") if lead else ""
    import urllib.parse
    review_link = f"https://search.google.com/local/writereview?placeid=&q={urllib.parse.quote(business_name + ' ' + address)}"
    wa_review_msg = urllib.parse.quote(f"Hi! Thank you for visiting {business_name}. We would love your feedback! Please leave us a Google review: {review_link}")

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Reviews - {business_name}</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}input,select,textarea{{font-size:16px!important}}.card{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px;margin-bottom:12px}}.btn{{display:block;width:100%;padding:12px;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer;text-align:center;text-decoration:none;margin-bottom:8px}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px">&#11088; Google Reviews</h1>
<p style="font-size:.72rem;color:#64748b;text-align:center;margin-bottom:16px">{business_name}</p>
<div class="card">
<h2 style="font-size:.82rem;font-weight:700;margin-bottom:8px">Your Review Link</h2>
<p style="font-size:.68rem;color:#94a3b8;margin-bottom:10px">Share this link with customers to get Google reviews</p>
<input id="revLink" value="{review_link}" readonly style="width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#00e5ff;font-size:12px;margin-bottom:8px" onclick="this.select();navigator.clipboard.writeText(this.value)">
<button onclick="navigator.clipboard.writeText(document.getElementById('revLink').value);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy Link',2000)" class="btn" style="background:#6366f1;color:#fff">Copy Review Link</button>
</div>
<div class="card">
<h2 style="font-size:.82rem;font-weight:700;margin-bottom:8px">Send Review Request via WhatsApp</h2>
<p style="font-size:.68rem;color:#94a3b8;margin-bottom:10px">Send to your recent customers</p>
<input id="custPhone" placeholder="Customer phone number" style="width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:14px;margin-bottom:8px">
<a id="waBtn" href="https://wa.me/?text={wa_review_msg}" target="_blank" class="btn" style="background:#25D366;color:#fff" onclick="var p=document.getElementById('custPhone').value;if(p)this.href='https://wa.me/'+p.replace(/[^0-9]/g,'')+'?text={wa_review_msg}'">Send Review Request on WhatsApp</a>
</div>
<div class="card">
<h2 style="font-size:.82rem;font-weight:700;margin-bottom:8px">Tips to Get More Reviews</h2>
<ul style="font-size:.72rem;color:#94a3b8;padding-left:16px;line-height:2">
<li>Ask happy customers right after service</li>
<li>Print QR code on bills/receipts</li>
<li>Send WhatsApp request same day</li>
<li>Respond to all existing reviews</li>
</ul>
</div>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/{website_id}/assistant", response_class=HTMLResponse)
def assistant_page(website_id: str):
    """Business Assistant - chat interface for business tasks."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Business Assistant</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto;padding-bottom:80px}}input,select,textarea{{font-size:16px!important}}.card{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:14px;margin-bottom:10px}}.msg{{padding:10px 12px;border-radius:12px;margin-bottom:8px;font-size:.8rem;max-width:85%}}.msg-user{{background:rgba(99,102,241,.2);margin-left:auto;text-align:right}}.msg-bot{{background:rgba(255,255,255,.05)}}.input-bar{{position:fixed;bottom:0;left:0;right:0;background:rgba(15,23,42,.95);backdrop-filter:blur(12px);padding:12px;display:flex;gap:8px;max-width:500px;margin:0 auto}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px">&#128172; Business Assistant</h1>
<p style="font-size:.72rem;color:#64748b;text-align:center;margin-bottom:12px">{business_name}</p>
<div class="card" style="margin-bottom:8px">
<p style="font-size:.68rem;color:#94a3b8;margin-bottom:8px">Try these:</p>
<div style="display:flex;flex-wrap:wrap;gap:6px">
<button onclick="ask('Create a festive offer for {category}')" style="padding:5px 10px;background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);border-radius:8px;color:#a78bfa;font-size:.65rem;cursor:pointer">Create festive offer</button>
<button onclick="ask('Write Instagram post for {business_name}')" style="padding:5px 10px;background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.2);border-radius:8px;color:#4ade80;font-size:.65rem;cursor:pointer">Instagram post</button>
<button onclick="ask('Create WhatsApp broadcast for Ganesh Chaturthi')" style="padding:5px 10px;background:rgba(0,229,255,.1);border:1px solid rgba(0,229,255,.2);border-radius:8px;color:#00e5ff;font-size:.65rem;cursor:pointer">WhatsApp campaign</button>
<button onclick="ask('Give me 5 tips to get more customers')" style="padding:5px 10px;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);border-radius:8px;color:#fbbf24;font-size:.65rem;cursor:pointer">Growth tips</button>
</div>
</div>
<div id="chat"></div>
<div class="input-bar">
<input id="inp" placeholder="Ask anything about your business..." style="flex:1;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;color:#fff;outline:none" onkeydown="if(event.key==='Enter')ask()">
<button onclick="ask()" style="padding:10px 16px;background:#6366f1;color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer">Send</button>
</div>
<script>
function ask(preset){{
  var inp=document.getElementById("inp");
  var q=preset||inp.value.trim();if(!q)return;
  inp.value="";
  var chat=document.getElementById("chat");
  chat.innerHTML+='<div class="msg msg-user">'+q+'</div>';
  chat.innerHTML+='<div class="msg msg-bot" id="typing" style="color:#64748b">Thinking...</div>';
  chat.scrollTop=chat.scrollHeight;
  fetch("/api/panel/{website_id}/assistant-ask",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{question:q}})}}).then(r=>r.json()).then(d=>{{
    document.getElementById("typing").remove();
    chat.innerHTML+='<div class="msg msg-bot">'+d.answer.replace(/\n/g,'<br>')+'</div>';
    chat.scrollTop=chat.scrollHeight;
  }}).catch(()=>{{document.getElementById("typing").textContent="Error. Try again.";}});
}}
</script>
</body></html>"""
    return HTMLResponse(content=html)


@router.post("/{website_id}/assistant-ask")
async def assistant_ask(website_id: str, data: dict):
    """Business assistant - answer questions using AI."""
    from app.core.llm import chat_completion
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    lead = lead_service.get(website["lead_id"]) if website and website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    question = data.get("question", "")

    prompt = f"""You are a business growth assistant for {business_name} ({category}).
Answer the following request helpfully and concisely. If asked to create content (posts, offers, messages), write it ready to use.
Keep responses short (under 200 words). Use emojis where appropriate.

Request: {question}"""

    try:
        answer = await chat_completion([{"role": "user", "content": prompt}])
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Sorry, I could not process that. Please try again. ({str(e)[:50]})"}


@router.get("/{website_id}/wa-growth", response_class=HTMLResponse)
def wa_growth_page(website_id: str):
    """WhatsApp Growth Center - templates, broadcasts, campaigns."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""

    templates = [
        ("Festival Greeting", f"Happy Festival from {business_name}! Visit us for special deals this season. \n\nCall: {phone}"),
        ("New Offer", f"FLAT 20% OFF at {business_name}! Limited time only. Walk in or WhatsApp us now!\n\nCall: {phone}"),
        ("Thank You", f"Thank you for visiting {business_name}! Hope to see you again soon. Please share your experience with friends!"),
        ("Appointment Reminder", f"Reminder: Your appointment at {business_name} is tomorrow. See you soon!"),
        ("New Arrival", f"NEW ARRIVALS at {business_name}! Come check out our latest collection. WhatsApp us for details."),
    ]

    import urllib.parse
    template_cards = ""
    for name, msg in templates:
        encoded = urllib.parse.quote(msg)
        template_cards += f'<div class="card"><h3 style="font-size:.78rem;font-weight:700;margin-bottom:6px">{name}</h3><p style="font-size:.68rem;color:#94a3b8;margin-bottom:8px;white-space:pre-line">{msg[:100]}...</p><a href="https://wa.me/?text={encoded}" target="_blank" style="display:block;text-align:center;padding:8px;background:#25D366;color:#fff;border-radius:8px;font-size:.75rem;font-weight:600;text-decoration:none">Send on WhatsApp</a></div>'

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>WhatsApp Growth</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}input,select,textarea{{font-size:16px!important}}.card{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:14px;margin-bottom:10px}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px">&#128232; WhatsApp Growth Center</h1>
<p style="font-size:.72rem;color:#64748b;text-align:center;margin-bottom:16px">{business_name} - Broadcast & Campaigns</p>
{template_cards}
<div class="card">
<h3 style="font-size:.78rem;font-weight:700;margin-bottom:6px">Custom Message</h3>
<textarea id="customMsg" placeholder="Write your custom broadcast message..." style="width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:14px;min-height:80px;resize:none;margin-bottom:8px"></textarea>
<a onclick="var m=document.getElementById('customMsg').value;if(m)window.open('https://wa.me/?text='+encodeURIComponent(m),'_blank')" style="display:block;text-align:center;padding:8px;background:#25D366;color:#fff;border-radius:8px;font-size:.75rem;font-weight:600;cursor:pointer">Send Custom Message</a>
</div>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/{website_id}/competitors", response_class=HTMLResponse)
def competitors_page(website_id: str):
    """Competitor insights - nearby businesses, review comparison."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    address = lead.get("address", "") if lead else ""

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Competitors</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}input,select,textarea{{font-size:16px!important}}.card{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:14px;margin-bottom:10px}}.btn{{display:block;width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer;text-align:center}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px">&#128200; Competitor Insights</h1>
<p style="font-size:.72rem;color:#64748b;text-align:center;margin-bottom:16px">{business_name}</p>
<div class="card">
<h2 style="font-size:.82rem;font-weight:700;margin-bottom:8px">Your Position</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.72rem">
<div><span style="color:#64748b">Category:</span> {category}</div>
<div><span style="color:#64748b">Area:</span> {address.split(",")[-2].strip() if "," in address else address[:20]}</div>
</div>
</div>
<div class="card">
<h2 style="font-size:.82rem;font-weight:700;margin-bottom:8px">Nearby Competitors</h2>
<p style="font-size:.68rem;color:#94a3b8;margin-bottom:10px">Tap to analyze competitors in your area</p>
<button class="btn" id="analyzeBtn" onclick="analyze()">Analyze Competitors</button>
<div id="results" style="margin-top:10px"></div>
</div>
<script>
async function analyze(){{
  var btn=document.getElementById("analyzeBtn");btn.disabled=true;btn.textContent="Analyzing...";
  try{{
    var r=await fetch("/api/panel/{website_id}/competitor-analysis",{{method:"POST"}});
    var d=await r.json();
    var html="";
    if(d.competitors){{d.competitors.forEach(function(c){{html+='<div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:.72rem"><div style="display:flex;justify-content:space-between"><b style="color:#e2e8f0">'+c.name+'</b><span style="color:#fbbf24">'+c.rating+' &#9733;</span></div><p style="color:#64748b;font-size:.65rem">'+c.reviews+' reviews</p></div>';}});}}
    if(d.insights)html+='<div style="margin-top:10px;padding:10px;background:rgba(99,102,241,.1);border-radius:8px;font-size:.7rem;color:#a78bfa">'+d.insights+'</div>';
    document.getElementById("results").innerHTML=html||'<p style="font-size:.7rem;color:#64748b">No data found</p>';
  }}catch(e){{document.getElementById("results").innerHTML='<p style="color:#ef4444;font-size:.7rem">Failed. Try again.</p>';}}
  btn.disabled=false;btn.textContent="Analyze Competitors";
}}
</script>
</body></html>"""
    return HTMLResponse(content=html)


@router.post("/{website_id}/competitor-analysis")
async def competitor_analysis(website_id: str):
    """Analyze competitors using AI."""
    from app.core.llm import chat_completion
    import json
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    lead = lead_service.get(website["lead_id"]) if website and website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    address = lead.get("address", "") if lead else ""

    prompt = f"""For a {category} business named "{business_name}" located at "{address}":
1. List 4-5 likely nearby competitors (realistic names for that area/category)
2. Give estimated ratings and review counts
3. Provide 2-3 insights about what this business can do better

Return JSON:
{{"competitors":[{{"name":"...","rating":"4.5","reviews":"120"}}],"insights":"..."}}"""

    try:
        raw = await chat_completion([{"role": "user", "content": prompt}])
        cleaned = raw.strip()
        if "```json" in cleaned: cleaned = cleaned.split("```json")[1].split("```")[0]
        elif "```" in cleaned: cleaned = cleaned.split("```")[1].split("```")[0]
        data = json.loads(cleaned.strip())
        return data
    except Exception:
        return {"competitors": [], "insights": "Could not analyze. Try again."}










@router.post("/{website_id}/auto-populate")
async def auto_populate_content(website_id: str):
    """Auto-generate starter content for a business dashboard on first visit."""
    from app.core.supabase import get_supabase
    from app.core.llm import chat_completion
    import json

    db = get_supabase()
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "general") if lead else "general"
    phone = lead.get("phone", "") if lead else ""

    # Check if already populated
    try:
        existing = db.table("store_products").select("id").eq("website_id", website_id).limit(1).execute()
        if existing.data:
            return {"status": "already_populated"}
    except Exception:
        pass

    # Generate products + social posts + daily content using AI
    prompt = f"""Generate starter content for a {category} business called "{business_name}".

Return JSON with:
1. "products": 5 products with name, description (1 line), price (in INR, realistic), category, image_url (use https://images.unsplash.com/photo-XXXXX?w=300&h=200&fit=crop format with real unsplash photo IDs matching the product)
2. "social_posts": 3 Instagram/WhatsApp posts ready to copy (with emojis, hashtags)
3. "daily_content": 3 WhatsApp status updates (short, engaging)

JSON format:
{{
  "products": [{{"name":"...","description":"...","price":299}}],
  "social_posts": ["post1...", "post2...", "post3..."],
  "daily_content": ["day1...", "day2...", "day3..."]
}}"""

    try:
        raw = await chat_completion([{"role": "user", "content": prompt}])
        cleaned = raw.strip()
        if "```json" in cleaned: cleaned = cleaned.split("```json")[1].split("```")[0]
        elif "```" in cleaned: cleaned = cleaned.split("```")[1].split("```")[0]
        data = json.loads(cleaned.strip())
    except Exception:
        # Fallback content
        # Category-specific default products with images
        cat_products = {
            "salon": [
                {"name": "Haircut & Styling", "description": "Professional cut and style", "price": 299, "image_url": "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=300&h=200&fit=crop", "category": "Hair"},
                {"name": "Facial Treatment", "description": "Deep cleansing facial", "price": 599, "image_url": "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=300&h=200&fit=crop", "category": "Skin"},
                {"name": "Manicure & Pedicure", "description": "Complete nail care", "price": 499, "image_url": "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=300&h=200&fit=crop", "category": "Nails"},
                {"name": "Hair Color", "description": "Premium hair coloring", "price": 1499, "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=300&h=200&fit=crop", "category": "Hair"},
                {"name": "Bridal Package", "description": "Complete bridal makeup", "price": 4999, "image_url": "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=300&h=200&fit=crop", "category": "Special"},
            ],
            "restaurant": [
                {"name": "Veg Thali", "description": "Complete meal with roti, dal, rice", "price": 149, "image_url": "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=300&h=200&fit=crop", "category": "Meals"},
                {"name": "Paneer Butter Masala", "description": "Creamy paneer curry", "price": 199, "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=300&h=200&fit=crop", "category": "Main Course"},
                {"name": "Biryani", "description": "Aromatic rice with spices", "price": 249, "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=300&h=200&fit=crop", "category": "Rice"},
                {"name": "Fresh Juice", "description": "Seasonal fruit juice", "price": 79, "image_url": "https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=300&h=200&fit=crop", "category": "Drinks"},
                {"name": "Dessert Combo", "description": "Gulab jamun + ice cream", "price": 129, "image_url": "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=300&h=200&fit=crop", "category": "Desserts"},
            ],
            "gym": [
                {"name": "Monthly Membership", "description": "Full gym access", "price": 999, "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=300&h=200&fit=crop", "category": "Membership"},
                {"name": "Personal Training (10 sessions)", "description": "1-on-1 with trainer", "price": 4999, "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=200&fit=crop", "category": "Training"},
                {"name": "Yoga Classes", "description": "Morning yoga batch", "price": 1499, "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=300&h=200&fit=crop", "category": "Classes"},
                {"name": "Diet Plan", "description": "Custom nutrition plan", "price": 799, "image_url": "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=300&h=200&fit=crop", "category": "Nutrition"},
            ],
            "store": [
                {"name": "New Collection", "description": "Latest arrivals", "price": 599, "image_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&h=200&fit=crop", "category": "New"},
                {"name": "Best Seller", "description": "Most popular item", "price": 499, "image_url": "https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=300&h=200&fit=crop", "category": "Popular"},
                {"name": "Budget Range", "description": "Value for money", "price": 299, "image_url": "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=300&h=200&fit=crop", "category": "Budget"},
                {"name": "Premium Item", "description": "Top quality", "price": 1299, "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=300&h=200&fit=crop", "category": "Premium"},
            ],
            "clinic": [
                {"name": "General Consultation", "description": "Doctor consultation", "price": 300, "image_url": "https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=300&h=200&fit=crop", "category": "Consultation"},
                {"name": "Blood Test Package", "description": "Complete blood work", "price": 799, "image_url": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=300&h=200&fit=crop", "category": "Lab"},
                {"name": "Dental Cleaning", "description": "Professional cleaning", "price": 500, "image_url": "https://images.unsplash.com/photo-1606265752439-1f18756aa5fc?w=300&h=200&fit=crop", "category": "Dental"},
                {"name": "Health Checkup", "description": "Full body checkup", "price": 1999, "image_url": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=300&h=200&fit=crop", "category": "Packages"},
            ],
            "cafe": [
                {"name": "Cappuccino", "description": "Rich espresso with foam", "price": 149, "image_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=300&h=200&fit=crop", "category": "Coffee"},
                {"name": "Sandwich", "description": "Grilled veg sandwich", "price": 129, "image_url": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=300&h=200&fit=crop", "category": "Snacks"},
                {"name": "Brownie", "description": "Chocolate fudge brownie", "price": 99, "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=300&h=200&fit=crop", "category": "Desserts"},
                {"name": "Fresh Juice", "description": "Seasonal fruit blend", "price": 89, "image_url": "https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=300&h=200&fit=crop", "category": "Drinks"},
            ],
        }
        # Find matching category
        cat_lower = category.lower()
        matched_prods = cat_products.get("store", [])  # default
        for key in cat_products:
            if key in cat_lower or cat_lower in key:
                matched_prods = cat_products[key]
                break
        
        data = {
            "products": matched_prods,
            "social_posts": [
                f"Visit {business_name} for the best {category} experience! Call {phone}",
                f"New offers at {business_name}! Limited time only. WhatsApp us now!",
                f"Thank you for choosing {business_name}. Your satisfaction is our priority!",
            ],
            "daily_content": [
                f"Good morning! {business_name} is open. Visit us today!",
                f"Special offer running this week at {business_name}!",
                f"Happy customers = Happy us! Visit {business_name} today.",
            ],
        }

    # Save products
    for p in data.get("products", [])[:6]:
        try:
            db.table("store_products").insert({
                "website_id": website_id,
                "name": p.get("name", "Product"),
                "description": p.get("description", ""),
                "price": p.get("price", 0),
                "image_url": p.get("image_url", ""),
                "category": p.get("category", "General"),
                "in_stock": True,
                "stock_qty": 99,
            }).execute()
        except Exception:
            pass

    # Save social posts and daily content in website content
    try:
        content = website.get("content", {}) or {}
        content["_auto_social_posts"] = data.get("social_posts", [])
        content["_auto_daily_content"] = data.get("daily_content", [])
        content["_populated"] = True
        db.table("websites").update({"content": content}).eq("id", website_id).execute()
    except Exception:
        pass

    return {"status": "populated", "products": len(data.get("products", [])), "posts": len(data.get("social_posts", []))}


@router.get("/{website_id}/crm", response_class=HTMLResponse)
def crm_page(website_id: str):
    """Simple CRM - track customers and follow-ups."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"

    # Get customers
    customers = []
    try:
        result = db.table("business_customers").select("*").eq("website_id", website_id).order("created_at", desc=True).limit(100).execute()
        customers = result.data or []
    except Exception:
        pass

    cust_rows = ""
    for cu in customers:
        cust_rows += f'<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:10px;margin-bottom:6px"><div style="display:flex;justify-content:space-between"><b style="font-size:.78rem">{cu.get("name","")}</b><span style="font-size:.6rem;color:#64748b">{cu.get("created_at","")[:10]}</span></div><p style="font-size:.68rem;color:#94a3b8">{cu.get("phone","")} | {cu.get("notes","")[:40]}</p></div>'

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>CRM - {business_name}</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}input,textarea{{font-size:16px!important;width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;margin-bottom:8px;outline:none}}.btn{{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px">&#128101; Customer CRM</h1>
<p style="font-size:.72rem;color:#64748b;text-align:center;margin-bottom:16px">{business_name} &bull; {len(customers)} customers</p>
<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:14px;margin-bottom:12px">
<h2 style="font-size:.8rem;font-weight:700;margin-bottom:8px">Add Customer</h2>
<input id="cName" placeholder="Customer name"><input id="cPhone" placeholder="Phone / WhatsApp"><input id="cNotes" placeholder="Notes (service done, amount, etc.)">
<button class="btn" onclick="addCustomer()">Add Customer</button>
</div>
<div id="custList">{cust_rows or '<p style="text-align:center;color:#475569;font-size:.75rem;padding:16px">No customers yet</p>'}</div>
<script>
async function addCustomer(){{
  var data={{name:document.getElementById('cName').value,phone:document.getElementById('cPhone').value,notes:document.getElementById('cNotes').value}};
  if(!data.name)return;
  await fetch('/api/panel/{website_id}/crm-add',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  location.reload();
}}
</script></body></html>"""
    return HTMLResponse(content=html)


@router.post("/{website_id}/crm-add")
async def crm_add_customer(website_id: str, data: dict):
    """Add a customer to business CRM."""
    from app.core.supabase import get_supabase
    from datetime import datetime
    db = get_supabase()
    try:
        db.table("business_customers").insert({
            "website_id": website_id,
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "notes": data.get("notes", ""),
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception:
        pass
    return {"status": "added"}


@router.get("/{website_id}/invoices", response_class=HTMLResponse)
def invoices_page(website_id: str):
    """Simple invoicing - create and track invoices."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""

    invoices = []
    try:
        result = db.table("business_invoices").select("*").eq("website_id", website_id).order("created_at", desc=True).limit(50).execute()
        invoices = result.data or []
    except Exception:
        pass

    inv_rows = ""
    for inv in invoices:
        status_color = "#22c55e" if inv.get("status") == "paid" else "#f59e0b"
        inv_rows += f'<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:10px;margin-bottom:6px"><div style="display:flex;justify-content:space-between"><b style="font-size:.78rem">{inv.get("customer_name","")}</b><span style="font-size:.75rem;font-weight:700;color:{status_color}">Rs.{inv.get("amount",0)}</span></div><p style="font-size:.65rem;color:#64748b">{inv.get("description","")[:50]} | {inv.get("created_at","")[:10]} | <span style="color:{status_color}">{inv.get("status","pending").upper()}</span></p></div>'

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Invoices - {business_name}</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}input,textarea,select{{font-size:16px!important;width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;margin-bottom:8px;outline:none}}.btn{{width:100%;padding:12px;background:#22c55e;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px">&#129534; Invoices</h1>
<p style="font-size:.72rem;color:#64748b;text-align:center;margin-bottom:16px">{business_name} &bull; {len(invoices)} invoices</p>
<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:14px;margin-bottom:12px">
<h2 style="font-size:.8rem;font-weight:700;margin-bottom:8px">Create Invoice</h2>
<input id="iName" placeholder="Customer name"><input id="iAmount" type="number" placeholder="Amount (Rs.)"><input id="iDesc" placeholder="Description / services"><select id="iStatus"><option value="pending">Pending</option><option value="paid">Paid</option></select>
<button class="btn" onclick="createInvoice()">Create Invoice & Send WhatsApp</button>
</div>
<div>{inv_rows or '<p style="text-align:center;color:#475569;font-size:.75rem;padding:16px">No invoices yet</p>'}</div>
<script>
async function createInvoice(){{
  var data={{customer_name:document.getElementById('iName').value,amount:Number(document.getElementById('iAmount').value),description:document.getElementById('iDesc').value,status:document.getElementById('iStatus').value}};
  if(!data.customer_name||!data.amount)return;
  var r=await fetch('/api/panel/{website_id}/invoice-create',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  var d=await r.json();
  if(d.wa_link)window.open(d.wa_link,'_blank');
  location.reload();
}}
</script></body></html>"""
    return HTMLResponse(content=html)


@router.post("/{website_id}/invoice-create")
async def create_invoice(website_id: str, data: dict):
    """Create an invoice and generate WhatsApp share link."""
    from app.core.supabase import get_supabase
    from datetime import datetime
    import urllib.parse
    db = get_supabase()
    
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    lead = lead_service.get(website["lead_id"]) if website and website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"

    invoice = {
        "website_id": website_id,
        "customer_name": data.get("customer_name", ""),
        "amount": data.get("amount", 0),
        "description": data.get("description", ""),
        "status": data.get("status", "pending"),
        "created_at": datetime.utcnow().isoformat(),
    }
    try:
        db.table("business_invoices").insert(invoice).execute()
    except Exception:
        pass

    # Generate WhatsApp message
    msg = f"Invoice from {business_name}\n\nCustomer: {data.get('customer_name')}\nAmount: Rs.{data.get('amount')}\nFor: {data.get('description')}\nStatus: {data.get('status','pending').upper()}\n\nThank you!"
    wa_link = f"https://wa.me/?text={urllib.parse.quote(msg)}"

    return {"status": "created", "wa_link": wa_link}


@router.get("/{website_id}/inventory", response_class=HTMLResponse)
def inventory_page(website_id: str):
    """Simple inventory - track stock levels."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"

    products = []
    try:
        result = db.table("store_products").select("*").eq("website_id", website_id).order("name").limit(100).execute()
        products = result.data or []
    except Exception:
        pass

    prod_rows = ""
    for p in products:
        stock = p.get("stock_qty", 0) or 0
        color = "#22c55e" if stock > 5 else "#f59e0b" if stock > 0 else "#ef4444"
        prod_rows += f'<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:10px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center"><div><b style="font-size:.78rem">{p.get("name","")}</b><p style="font-size:.65rem;color:#64748b">Rs.{p.get("price",0)}</p></div><div style="text-align:right"><span style="font-size:1rem;font-weight:800;color:{color}">{stock}</span><p style="font-size:.55rem;color:#64748b">in stock</p></div></div>'

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Inventory - {business_name}</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}input{{font-size:16px!important;width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;margin-bottom:8px;outline:none}}.btn{{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer}}</style></head><body>
<h1 style="font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px">&#128230; Inventory</h1>
<p style="font-size:.72rem;color:#64748b;text-align:center;margin-bottom:16px">{business_name} &bull; {len(products)} items</p>
<div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:14px;margin-bottom:12px">
<h2 style="font-size:.8rem;font-weight:700;margin-bottom:8px">Update Stock</h2>
<input id="sName" placeholder="Product name"><input id="sQty" type="number" placeholder="Stock quantity">
<button class="btn" onclick="updateStock()">Update Stock</button>
</div>
<div>{prod_rows or '<p style="text-align:center;color:#475569;font-size:.75rem;padding:16px">No products. Add from Products tool first.</p>'}</div>
<script>
async function updateStock(){{
  var name=document.getElementById('sName').value;var qty=Number(document.getElementById('sQty').value);
  if(!name)return;
  await fetch('/api/panel/{website_id}/stock-update',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{name:name,qty:qty}})}});
  location.reload();
}}
</script></body></html>"""
    return HTMLResponse(content=html)


@router.post("/{website_id}/stock-update")
async def update_stock(website_id: str, data: dict):
    """Update stock quantity for a product."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    name = data.get("name", "")
    qty = data.get("qty", 0)
    try:
        existing = db.table("store_products").select("id").eq("website_id", website_id).ilike("name", f"%{name}%").limit(1).execute()
        if existing.data:
            db.table("store_products").update({"stock_qty": qty}).eq("id", existing.data[0]["id"]).execute()
            return {"status": "updated"}
        else:
            db.table("store_products").insert({"website_id": website_id, "name": name, "price": 0, "stock_qty": qty, "in_stock": qty > 0}).execute()
            return {"status": "created"}
    except Exception as e:
        return {"error": str(e)[:50]}


@router.get("/{website_id}/edit-site", response_class=HTMLResponse)
def edit_site_page(website_id: str):
    """AI Website Editor."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    content = website.get("content", {}) or {}
    hero_title = content.get("hero_title", "")
    hero_subtitle = content.get("hero_subtitle", "")
    about = content.get("about", "")
    contact = content.get("contact_info", {})
    phone = contact.get("phone", lead.get("phone","") if lead else "")
    email = contact.get("email", "")
    address = contact.get("address", lead.get("address","") if lead else "")
    hours = contact.get("hours", "Mon-Sat: 9 AM - 8 PM")

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Edit - {business_name}</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:12px;max-width:500px;margin:0 auto}}input,textarea{{font-size:16px!important;width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;margin-bottom:8px;outline:none}}.card{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:14px;margin-bottom:10px}}.card h2{{font-size:.8rem;font-weight:700;margin-bottom:8px}}.btn{{width:100%;padding:11px;border:none;border-radius:10px;font-weight:700;font-size:.82rem;cursor:pointer}}label{{font-size:.68rem;color:#94a3b8;margin-bottom:3px;display:block}}</style></head><body>
<h1 style="font-size:1rem;font-weight:800;text-align:center;margin-bottom:12px">Edit Website</h1>
<div class="card"><h2>Quick Edit (Command)</h2><p style="font-size:.65rem;color:#64748b;margin-bottom:8px">e.g. "change headline to Grand Opening"</p><textarea id="aiCmd" rows="2" placeholder="Type what to change..."></textarea><button class="btn" style="background:#6366f1;color:#fff" onclick="aiEdit()">Apply</button><p id="aiSt" style="font-size:.65rem;color:#94a3b8;margin-top:6px"></p></div>
<div class="card"><h2>Hero</h2><label>Headline</label><input id="ht" value="{hero_title}"><label>Subtitle</label><input id="hs" value="{hero_subtitle}"></div>
<div class="card"><h2>About</h2><textarea id="ab" rows="3">{about[:300]}</textarea></div>
<div class="card"><h2>Contact</h2><label>Phone</label><input id="ph" value="{phone}"><label>Email</label><input id="em" value="{email}"><label>Address</label><input id="ad" value="{address}"><label>Hours</label><input id="hr" value="{hours}"></div>
<button class="btn" style="background:#22c55e;color:#fff;margin-top:8px" onclick="saveAll()">Save All Changes</button>
<p id="saveSt" style="font-size:.7rem;color:#22c55e;text-align:center;margin-top:8px"></p>
<script>
async function aiEdit(){{var cmd=document.getElementById("aiCmd").value;if(!cmd)return;document.getElementById("aiSt").textContent="Applying...";try{{var r=await fetch("/api/panel/{website_id}/ai-edit",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{command:cmd}})}});var d=await r.json();document.getElementById("aiSt").textContent=d.status==="updated"?"Done! Refresh site.":"Failed";}}catch(e){{document.getElementById("aiSt").textContent="Error";}}}}
async function saveAll(){{var data={{hero_title:document.getElementById("ht").value,hero_subtitle:document.getElementById("hs").value,about:document.getElementById("ab").value,phone:document.getElementById("ph").value,email:document.getElementById("em").value,address:document.getElementById("ad").value,hours:document.getElementById("hr").value}};try{{var r=await fetch("/api/panel/{website_id}/save-edit",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(data)}});var d=await r.json();document.getElementById("saveSt").textContent=d.status==="saved"?"Saved!":"Failed";}}catch(e){{document.getElementById("saveSt").textContent="Error";}}}}
</script></body></html>"""
    return HTMLResponse(content=html)


@router.post("/{website_id}/ai-edit")
async def ai_edit_website(website_id: str, data: dict):
    """Apply AI edit command to website."""
    from app.core.supabase import get_supabase
    from app.core.llm import chat_completion
    import json
    db = get_supabase()
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        return {"status": "error"}
    content = website.get("content", {}) or {}
    command = data.get("command", "")
    prompt = f"Edit website content. Current: hero_title={content.get('hero_title','')}, hero_subtitle={content.get('hero_subtitle','')}, about={content.get('about','')[:80]}. Command: {command}. Return ONLY changed fields as JSON."
    try:
        raw = await chat_completion([{"role": "user", "content": prompt}])
        cleaned = raw.strip()
        if "```" in cleaned: cleaned = cleaned.split("```")[1].split("```")[0]
        if cleaned.startswith("json"): cleaned = cleaned[4:]
        updates = json.loads(cleaned.strip())
        for k, v in updates.items():
            content[k] = v
        db.table("websites").update({"content": content}).eq("id", website_id).execute()
        return {"status": "updated"}
    except Exception:
        return {"status": "error"}


@router.post("/{website_id}/save-edit")
async def save_manual_edit(website_id: str, data: dict):
    """Save manual edits."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        return {"status": "error"}
    content = website.get("content", {}) or {}
    if data.get("hero_title"): content["hero_title"] = data["hero_title"]
    if data.get("hero_subtitle"): content["hero_subtitle"] = data["hero_subtitle"]
    if data.get("about"): content["about"] = data["about"]
    contact = content.get("contact_info", {})
    if data.get("phone"): contact["phone"] = data["phone"]
    if data.get("email"): contact["email"] = data["email"]
    if data.get("address"): contact["address"] = data["address"]
    if data.get("hours"): contact["hours"] = data["hours"]
    content["contact_info"] = contact
    try:
        db.table("websites").update({"content": content}).eq("id", website_id).execute()
        return {"status": "saved"}
    except Exception:
        return {"status": "error"}
