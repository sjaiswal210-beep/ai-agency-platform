from contextlib import asynccontextmanager
import re as _security_re

def _sanitize_input(text: str) -> str:
    """Sanitize input to prevent injection attacks."""
    if not text:
        return text
    # Remove potential NoSQL/SQL injection patterns
    dangerous = ["$where", "$gt", "$lt", "$ne", "$regex", "$or", "$and", "' OR", "'; DROP", "1=1", "UNION SELECT", "/*", "*/"]
    for d in dangerous:
        if d.lower() in text.lower():
            return ""
    # Remove potential SSTI
    text = _security_re.sub(r'\{\{.*?\}\}', '', text)
    text = _security_re.sub(r'\{%.*?%\}', '', text)
    return text

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from app.api.routes import leads, websites, outreach, dashboard
from app.api.routes import automation
from app.api.routes.preview import router as preview_router
from app.api.routes.editor import router as editor_router
from app.api.routes.branding import router as branding_router
from app.api.routes.toolkit import router as toolkit_router
from app.api.routes.owner_panel import router as panel_router
from app.api.routes.whatsapp import router as whatsapp_router
from app.api.routes.video import router as video_router
from app.api.routes.growth import router as growth_router
from app.api.routes.chatbot import router as chatbot_router
from app.api.routes.client_auth import router as client_auth_router
from app.api.routes.payments import router as payments_router
from app.api.routes.deploy import router as deploy_router
from app.api.routes.site_manager import router as site_manager_router
from app.api.routes.owner_daily import router as daily_router
from app.api.routes.creatives import router as creatives_router
from app.api.routes.logo_gen import router as logo_gen_router
from app.api.routes.website_analytics import router as analytics_router
from app.api.routes.owner_analytics import router as owner_analytics_router
from app.api.routes.blog import router as blog_router
from app.api.routes.translate import router as translate_router
from app.api.routes.seo_pages import router as seo_pages_router
from app.api.routes.growth_agent import router as growth_agent_router
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.review_manager import router as review_manager_router
from app.api.routes.qr_code import router as qr_router
from app.api.routes.health_score import router as health_score_router
from app.api.routes.scraper import router as scraper_router
from app.api.routes.agent_status import router as agent_status_router
from app.api.routes.admin_panel import router as admin_panel_router
from app.api.routes.locations import router as locations_router
from app.api.routes.ecommerce import router as ecommerce_router
from app.api.routes.google_profile import router as google_profile_router
from app.api.routes.sitemap import router as sitemap_router
from app.api.routes.qa_review import router as qa_router
from app.api.routes.offers import router as offers_router
from app.api.routes.ads import router as ads_router
from app.automation.scheduler import start_scheduler, stop_scheduler
from app.core.logging import setup_logging

setup_logging()

async def _ping_google_sitemap(slug: str):
    """Notify Google about sitemap update for a subdomain."""
    try:
        import httpx
        url = f"http://www.google.com/ping?sitemap=https://{slug}.city-maps.online/sitemap.xml"
        async with httpx.AsyncClient(timeout=10) as client:
            await client.get(url)
    except Exception:
        pass




@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="City Maps Platform",
    description="Autonomous AI-powered digital agency backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Security: Rate limiting (simple in-memory)
from collections import defaultdict
import time as _time
_rate_limits = defaultdict(list)


# Stricter rate limiting for AI/expensive endpoints (10 per hour per IP)
_ai_rate_limits = defaultdict(list)

def _check_ai_rate_limit(ip: str) -> bool:
    """Check if IP has exceeded AI endpoint rate limit (10/hour)."""
    now = _time.time()
    _ai_rate_limits[ip] = [t for t in _ai_rate_limits[ip] if now - t < 3600]
    if len(_ai_rate_limits[ip]) >= 10:
        return False
    _ai_rate_limits[ip].append(now)
    return True

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Basic rate limiting - 100 requests per minute per IP."""
    ip = request.client.host if request.client else "unknown"
    now = _time.time()
    _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < 60]
    if len(_rate_limits[ip]) > 100:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    _rate_limits[ip].append(now)
    
    # SSTI Prevention: block template injection patterns in query/body
    url_str = str(request.url)
    if any(p in url_str for p in ["{{", "}}", "{%", "%}", "${", "<%"]):
        return JSONResponse(status_code=400, content={"detail": "Invalid request"})
    
    # ReDoS Prevention: block extremely long query params
    if len(url_str) > 4096:
        return JSONResponse(status_code=414, content={"detail": "URI too long"})
    
    # LPDOS: limit request body size (10MB max)
    content_length = request.headers.get("content-length", "0")
    if int(content_length) > 10 * 1024 * 1024:
        return JSONResponse(status_code=413, content={"detail": "Request too large"})
    
    response = await call_next(request)
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "clipboard-read=(), clipboard-write=(self)"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/robots.txt")
def robots_txt(request: Request):
    """Dynamic robots.txt - includes subdomain sitemap if on subdomain."""
    host = request.headers.get("host", "")
    if ".city-maps.online" in host and not host.startswith("www."):
        subdomain = host.split(".city-maps.online")[0].lower().strip()
        if subdomain and subdomain not in ["www", "api", "admin"]:
            txt = f"User-agent: *\nAllow: /\nSitemap: https://{subdomain}.city-maps.online/sitemap.xml"
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=txt)
    # Main domain robots.txt
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content="User-agent: *\nAllow: /\nSitemap: https://city-maps.online/sitemap.xml")

@app.middleware("http")
async def subdomain_routing(request: Request, call_next):
    """Route subdomain requests to the correct website."""
    host = request.headers.get("host", "")
    # Check if it's a subdomain of city-maps.online
    if ".city-maps.online" in host and not host.startswith("www.") and not host.startswith("api."):
        subdomain = host.split(".city-maps.online")[0].lower().strip()
        if subdomain and subdomain not in ["www", "api", "admin"] and not request.url.path.startswith("/api/"):
            # Serve subdomain-specific sitemap
            if request.url.path == "/sitemap.xml":
                from fastapi.responses import Response
                slug_url = f"https://{subdomain}.city-maps.online"
                sub_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>{slug_url}</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
<url><loc>{slug_url}/#services</loc><priority>0.8</priority></url>
<url><loc>{slug_url}/#contact</loc><priority>0.7</priority></url>
</urlset>'''
                return Response(content=sub_xml, media_type="application/xml")
            # Redirect to the preview by slug
            from app.api.routes.preview import generate_html, _get_real_photos, get_images_for_category, _get_logo_icon, get_maps_embed
            from app.services.website_service import WebsiteService
            from app.services.lead_service import LeadService
            from fastapi.responses import HTMLResponse
            from app.core.supabase import get_supabase
            import json
            
            db = get_supabase()
            result = db.table("websites").select("*").eq("slug", subdomain).limit(1).execute()
            if result.data:
                website = result.data[0]
                content = website.get("content", {})
                if content:
                    lead_service = LeadService()
                    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
                    html = generate_html(content, website.get("template", "store"), lead, website_id_override=website["id"])
                    # Inject ad slot before </body>
                    wid = website["id"]
                    ad_inject = '<div id="cm-ad" style="display:none;position:fixed;bottom:62px;left:8px;right:8px;z-index:998;text-align:center"></div><script data-cfasync="false">fetch("/api/ads/serve?website_id=' + wid + '").then(function(r){return r.json()}).then(function(d){if(!d.ad)return;var s=document.getElementById("cm-ad");s.style.display="block";s.innerHTML="<a href=\'"+d.ad.destination_url+"\' target=\'_blank\'><img src=\'"+d.ad.creative_url+"\' style=\'max-width:100%;max-height:90px;border-radius:8px\' alt=\'ad\'></a>";fetch("/api/ads/track",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({campaign_id:d.ad.id,event_type:"ad_impression",website_id:"' + wid + '"})})}).catch(function(){});</script>'
                    # Inject ad - use simple string replace on the body tag
                    html = html.replace("<body>", "<body>" + ad_inject, 1)
                    if ad_inject not in html:
                        # Body tag might have attributes
                        import re as _re
                        html = _re.sub(r"(<body[^>]*>)", r"\1" + ad_inject, html, count=1)
                    return HTMLResponse(content=html, headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"})
            # If no match, continue to normal routing
    response = await call_next(request)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Never expose internal details - sanitize error messages
    error_msg = str(exc)
    # Hide sensitive info from error messages
    for secret in ["api_key", "token", "password", "secret", "supabase"]:
        if secret.lower() in error_msg.lower():
            error_msg = "Internal server error"
            break
    return JSONResponse(status_code=500, content={"detail": error_msg})


app.include_router(leads.router, prefix="/api")
app.include_router(websites.router, prefix="/api")
app.include_router(outreach.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(automation.router, prefix="/api")
app.include_router(preview_router, prefix="/api")
app.include_router(editor_router, prefix="/api")
app.include_router(branding_router, prefix="/api")
app.include_router(toolkit_router, prefix="/api")
app.include_router(panel_router, prefix="/api")
app.include_router(whatsapp_router, prefix="/api")
app.include_router(video_router, prefix="/api")
app.include_router(growth_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(client_auth_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(deploy_router, prefix="/api")
app.include_router(site_manager_router, prefix="/api")
app.include_router(daily_router, prefix="/api")
app.include_router(creatives_router, prefix="/api")
app.include_router(logo_gen_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(owner_analytics_router, prefix="/api")
app.include_router(blog_router, prefix="/api")
app.include_router(translate_router, prefix="/api")
app.include_router(seo_pages_router, prefix="/api")
app.include_router(growth_agent_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(bookings_router, prefix="/api")
app.include_router(review_manager_router, prefix="/api")
app.include_router(qr_router, prefix="/api")
app.include_router(health_score_router, prefix="/api")
app.include_router(scraper_router, prefix="/api")
app.include_router(agent_status_router, prefix="/api")
app.include_router(admin_panel_router, prefix="/api")
app.include_router(locations_router, prefix="/api")
app.include_router(ecommerce_router, prefix="/api")
app.include_router(google_profile_router, prefix="/api")
app.include_router(sitemap_router, prefix="")
app.include_router(qa_router, prefix="/api")
app.include_router(offers_router, prefix="/api")
app.include_router(ads_router, prefix="/api")


# Mount static files
import os as _os
_static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'static')
if _os.path.isdir(_static_dir):
    app.mount('/static', StaticFiles(directory=_static_dir), name='static')

# Replay attack prevention: track used nonces
_used_nonces = {}

@app.post("/api/dashboard-access")
async def dashboard_access(request: Request):
    """Track and grant dashboard access via mobile number."""
    from app.core.supabase import get_supabase
    from datetime import datetime
    data = await request.json()
    phone = data.get("phone", "")
    website_id = data.get("website_id", "")
    
    if not phone or len(phone) < 10:
        return JSONResponse({"message": "Enter valid mobile number"})
    
    db = get_supabase()
    
    # Log access attempt
    try:
        db.table("dashboard_access_logs").insert({
            "phone": phone,
            "website_id": website_id,
            "accessed_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception:
        # Table might not exist yet - that's ok
        pass
    
    # Return panel URL
    panel_url = f"/api/panel/{website_id}" if website_id else ""
    return JSONResponse({"panel_url": panel_url, "phone": phone})

@app.get("/google-site-verification", response_class=HTMLResponse)
def google_verification():
    """Serve Google Search Console verification. Update the content value with your code."""
    return HTMLResponse("google-site-verification: google-site-verification.html")


@app.post("/api/data-deletion")
@app.get("/api/data-deletion")
async def data_deletion(request: Request):
    """Handle user data deletion requests (required by Meta)."""
    return JSONResponse({"url": "https://city-maps.online/api/data-deletion", "confirmation_code": "citymaps_deletion_confirmed", "status": "Data deletion request received. We will process within 30 days."})

@app.get("/sitemap.xml")
def sitemap_xml():
    """Dynamic sitemap for city-maps.online"""
    from app.core.supabase import get_supabase
    from fastapi.responses import Response
    db = get_supabase()
    
    urls = ['<url><loc>https://city-maps.online/</loc><priority>1.0</priority></url>']
    
    # Add all business websites
    try:
        sites = db.table("websites").select("slug").not_.is_("slug", "null").execute()
        for s in (sites.data or []):
            slug = s.get("slug", "")
            if slug:
                urls.append(f'<url><loc>https://{slug}.city-maps.online</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    except Exception:
        pass
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"".join(urls)}
</urlset>'''
    return Response(content=xml, media_type="application/xml")

@app.get("/api/growth-plan", response_class=HTMLResponse)
def growth_plan_page():
    """Self-growth plan with AI-powered action items."""
    html = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Growth Plan - City Maps</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:600px;margin:0 auto}h1{font-size:1.2rem;margin-bottom:4px}.sub{font-size:.75rem;color:#64748b;margin-bottom:20px}.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:10px}.item{display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid #334155}.item:last-child{border:none}.item input[type=checkbox]{margin-top:3px;width:16px;height:16px;accent-color:#6366f1;cursor:pointer}.item-text{font-size:.8rem;flex:1}.item-text.done{text-decoration:line-through;color:#64748b}.ai-input{display:flex;gap:8px;margin-bottom:16px}input{flex:1;padding:10px;border:1px solid #334155;border-radius:8px;background:#1e293b;color:#fff;font-size:.8rem;outline:none}button{padding:10px 16px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;font-size:.8rem;cursor:pointer}.btn-ai{background:linear-gradient(135deg,#6366f1,#8b5cf6)}</style></head><body>
<h1>Growth Plan</h1>
<p class="sub">AI-powered action items & progress tracking</p>

<div class="ai-input">
<input id="goalInput" placeholder="What do you want to achieve? (e.g., Get 50 more leads this month)">
<button class="btn-ai" onclick="generatePlan()">AI Plan</button>
</div>

<div class="card">
<h3 style="font-size:.85rem;margin-bottom:12px">Action Items</h3>
<div id="actionItems"></div>
<div style="display:flex;gap:8px;margin-top:12px">
<input id="newItem" placeholder="Add custom action item..." style="flex:1">
<button onclick="addItem()">Add</button>
</div>
</div>

<div class="card">
<h3 style="font-size:.85rem;margin-bottom:8px">Progress</h3>
<div id="progress" style="font-size:.8rem;color:#64748b">0 of 0 completed</div>
<div style="background:#334155;border-radius:8px;height:8px;margin-top:8px;overflow:hidden"><div id="progressBar" style="height:100%;background:linear-gradient(90deg,#6366f1,#00e5ff);width:0%;transition:width .3s"></div></div>
</div>

<script>
var items = JSON.parse(localStorage.getItem("growth_items") || "[]");
renderItems();

function renderItems(){
var el=document.getElementById("actionItems");
el.innerHTML="";
items.forEach(function(item,i){
el.innerHTML+="<div class=item><input type=checkbox "+(item.done?"checked":"")+" onchange=toggleItem("+i+")><span class='item-text "+(item.done?"done":"")+"'>"+item.text+"</span><button onclick=removeItem("+i+") style='background:none;border:none;color:#ef4444;cursor:pointer;font-size:.8rem'>x</button></div>";
});
var done=items.filter(function(i){return i.done}).length;
document.getElementById("progress").textContent=done+" of "+items.length+" completed";
document.getElementById("progressBar").style.width=(items.length?done/items.length*100:0)+"%";
}

function addItem(){
var t=document.getElementById("newItem").value.trim();
if(!t)return;
items.push({text:t,done:false});
localStorage.setItem("growth_items",JSON.stringify(items));
document.getElementById("newItem").value="";
renderItems();
}

function toggleItem(i){items[i].done=!items[i].done;localStorage.setItem("growth_items",JSON.stringify(items));renderItems();}
function removeItem(i){items.splice(i,1);localStorage.setItem("growth_items",JSON.stringify(items));renderItems();}

async function generatePlan(){
var goal=document.getElementById("goalInput").value.trim();
if(!goal)return;
document.getElementById("goalInput").value="Generating...";
try{
var r=await fetch("/api/growth-plan/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({goal:goal})});
var data=await r.json();
if(data.actions){
data.actions.forEach(function(a){items.push({text:a,done:false});});
localStorage.setItem("growth_items",JSON.stringify(items));
renderItems();
}
}catch(e){}
document.getElementById("goalInput").value="";
}
</script>
</body></html>'''
    return HTMLResponse(content=html)


@app.post("/api/growth-plan/generate")
async def generate_growth_plan(request: Request):
    """Generate AI-powered growth action items."""
    from app.core.llm import chat_completion
    import json
    data = await request.json()
    goal = data.get("goal", "")
    
    prompt = f"""Generate 5-7 specific, actionable growth tasks for this business goal: "{goal}"

Each task should be:
- Specific and measurable
- Achievable in 1-7 days
- Focused on digital growth (SEO, leads, visibility)

Return ONLY a JSON array of strings:
["Task 1 description", "Task 2 description", ...]"""
    
    try:
        result = await chat_completion([{"role": "user", "content": prompt}])
        cleaned = result.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        actions = json.loads(cleaned)
        return {"actions": actions}
    except Exception as e:
        return {"actions": [f"Set up Google Business Profile", "Optimize website for local keywords", "Collect 5 customer reviews", "Create social media content calendar", "Run first lead generation campaign"], "note": "AI unavailable, using defaults"}

@app.get("/category/{category}", response_class=HTMLResponse)
def category_page(category: str):
    """SEO page listing businesses by category."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    leads = db.table("leads").select("id,business_name,address,phone,category").ilike("category", f"%{category}%").limit(50).execute().data or []
    websites = db.table("websites").select("slug,lead_id").not_.is_("slug", "null").execute().data or []
    slug_map = {w["lead_id"]: w["slug"] for w in websites}
    
    cards = ""
    for l in leads:
        slug = slug_map.get(l["id"], "")
        link = f"https://{slug}.city-maps.online" if slug else "#"
        cards += f'<a href="{link}" target="_blank" style="display:block;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px;text-decoration:none;color:#fff;margin-bottom:8px"><b style="font-size:.85rem">{l.get("business_name","")}</b><p style="font-size:.7rem;color:#64748b;margin-top:4px">{l.get("address","")[:50]}</p></a>'
    
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Best {category.title()} Businesses | City Maps</title>
<meta name="description" content="Find the best {category} businesses near you. Professional websites, reviews, and contact details.">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:700px;margin:0 auto}}</style></head><body>
<h1 style="font-size:1.3rem;margin-bottom:4px">Best {category.title()} Businesses</h1>
<p style="font-size:.75rem;color:#64748b;margin-bottom:20px">{len(leads)} businesses found</p>
{cards or '<p style="color:#475569">No businesses found in this category.</p>'}
<p style="text-align:center;margin-top:20px;font-size:.7rem"><a href="/" style="color:#00e5ff">Back to City Maps</a></p>
</body></html>'''
    return HTMLResponse(content=html)


@app.get("/city/{city}", response_class=HTMLResponse)
def city_page(city: str):
    """SEO page listing businesses by city."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    leads = db.table("leads").select("id,business_name,address,phone,category").ilike("address", f"%{city}%").limit(50).execute().data or []
    websites = db.table("websites").select("slug,lead_id").not_.is_("slug", "null").execute().data or []
    slug_map = {w["lead_id"]: w["slug"] for w in websites}
    
    cards = ""
    for l in leads:
        slug = slug_map.get(l["id"], "")
        link = f"https://{slug}.city-maps.online" if slug else "#"
        cards += f'<a href="{link}" target="_blank" style="display:block;background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px;text-decoration:none;color:#fff;margin-bottom:8px"><b style="font-size:.85rem">{l.get("business_name","")}</b><p style="font-size:.7rem;color:#64748b;margin-top:4px">{l.get("category","").title()} | {l.get("address","")[:40]}</p></a>'
    
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Businesses in {city.title()} | City Maps</title>
<meta name="description" content="Find local businesses in {city.title()}. Professional websites, contact details, and reviews.">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:700px;margin:0 auto}}</style></head><body>
<h1 style="font-size:1.3rem;margin-bottom:4px">Businesses in {city.title()}</h1>
<p style="font-size:.75rem;color:#64748b;margin-bottom:20px">{len(leads)} businesses found</p>
{cards or '<p style="color:#475569">No businesses found in this city.</p>'}
<p style="text-align:center;margin-top:20px;font-size:.7rem"><a href="/" style="color:#00e5ff">Back to City Maps</a></p>
</body></html>'''
    return HTMLResponse(content=html)


@app.get("/api/sites", response_class=HTMLResponse)
def all_sites_page():
    """All generated websites grouped by category, city."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    sites = db.table("websites").select("id,slug,lead_id,created_at").not_.is_("slug", "null").order("created_at", desc=True).execute().data or []
    leads_data = db.table("leads").select("id,business_name,category,address").execute().data or []
    leads = {}
    for l in leads_data:
        lid = l.get("id")
        if lid and isinstance(lid, str):
            leads[lid] = l
    
    # Group by category and city
    by_category = {}
    by_city = {}
    for s in sites:
        lead = leads.get(s.get("lead_id", ""), {})
        cat = lead.get("category", "other").lower().strip()
        addr = lead.get("address", "")
        # Extract city from address (last meaningful part)
        parts = [p.strip() for p in addr.split(",") if p.strip()]
        city = parts[-2] if len(parts) >= 2 else (parts[-1] if parts else "unknown")
        city = city.strip().title()
        
        entry = {"slug": s.get("slug",""), "name": lead.get("business_name","Unknown"), "category": cat, "city": city}
        by_category.setdefault(cat, []).append(entry)
        by_city.setdefault(city, []).append(entry)
    
    # Build HTML with tabs
    cat_sections = ""
    for cat, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
        links = "".join([f'<a href="https://{e["slug"]}.city-maps.online" target="_blank" style="display:block;padding:6px 0;font-size:.75rem;color:#00e5ff;border-bottom:1px solid #334155">{e["name"]}</a>' for e in items])
        cat_sections += f'<div style="margin-bottom:16px"><h3 style="font-size:.8rem;font-weight:700;text-transform:capitalize;margin-bottom:6px;color:#94a3b8">{cat} ({len(items)})</h3>{links}</div>'
    
    city_sections = ""
    for city, items in sorted(by_city.items(), key=lambda x: -len(x[1])):
        links = "".join([f'<a href="https://{e["slug"]}.city-maps.online" target="_blank" style="display:block;padding:6px 0;font-size:.75rem;color:#00e5ff;border-bottom:1px solid #334155">{e["name"]} <span style="color:#64748b;font-size:.65rem">({e["category"]})</span></a>' for e in items])
        city_sections += f'<div style="margin-bottom:16px"><h3 style="font-size:.8rem;font-weight:700;margin-bottom:6px;color:#94a3b8">{city} ({len(items)})</h3>{links}</div>'
    
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>All Sites</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:800px;margin:0 auto}}.tabs{{display:flex;gap:8px;margin:16px 0}}.tab{{padding:8px 16px;border-radius:8px;font-size:.75rem;font-weight:600;cursor:pointer;border:1px solid #334155;background:#1e293b;color:#94a3b8}}.tab.active{{background:#6366f1;color:#fff;border-color:#6366f1}}.panel{{display:none}}.panel.active{{display:block}}</style></head><body>
<h1 style="font-size:1.2rem;margin-bottom:4px">All Sites ({len(sites)})</h1>
<input id="searchBox" placeholder="Search business name..." oninput="filterSites()" style="width:100%;padding:10px 14px;border:1px solid #334155;border-radius:8px;background:#1e293b;color:#fff;font-size:.8rem;outline:none;margin-bottom:12px">
<div class="tabs">
<div class="tab active" onclick="showTab('cat')">By Category</div>
<div class="tab" onclick="showTab('city')">By City</div>
<div class="tab" onclick="showTab('all')">All</div>
</div>
<div class="panel active" id="panel-cat">{cat_sections}</div>
<div class="panel" id="panel-city">{city_sections}</div>
<div class="panel" id="panel-all">{''.join([f'<a href="https://{s.get("slug","")}.city-maps.online" target="_blank" style="display:flex;justify-content:space-between;padding:8px 0;font-size:.75rem;color:#00e5ff;border-bottom:1px solid #334155"><span>{leads.get(s.get("lead_id",""),{{}}).get("business_name","?")}</span><span style="color:#64748b;font-size:.65rem">{s.get("slug","")}.city-maps.online</span></a>' for s in sites])}</div>
<script>function filterSites(){{var q=document.getElementById('searchBox').value.toLowerCase();document.querySelectorAll('.panel a').forEach(function(a){{a.style.display=a.textContent.toLowerCase().includes(q)?'':'none'}});}}
function showTab(t){{document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));document.getElementById('panel-'+t).classList.add('active');event.target.classList.add('active');}}</script>
</body></html>'''
    return HTMLResponse(content=html)


@app.get("/", response_class=HTMLResponse)
def landing_page():
    """City Maps - Premium Digital Presence Platform with 3D depth background."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        sites = db.table("websites").select("slug", count="exact").not_.is_("slug", "null").execute()
        count = sites.count or 0
    except Exception:
        count = 0

    html = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>City Maps - Make your business online free with professional Website and Whatsapp sales and 69 growth tools.</title>
<meta name="description" content="Build professional website free. WhatsApp connect, growth tools, Google visibility. If you are on Maps, your website is ready. Make your business growth live.">
<meta name="theme-color" content="#020817"><meta name="google-site-verification" content="39nzaqNCoWxNXFyhZTNOUSSWZiHY9rCEpDFzvEakUo4">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,sans-serif;background:#020817;color:#fff;overflow-x:hidden;-webkit-font-smoothing:antialiased}}
a{{text-decoration:none;color:inherit}}

/* === 3D DEPTH BACKGROUND === */
.bg-depth{{position:fixed;inset:0;z-index:0;overflow:hidden;perspective:1200px;transform-style:preserve-3d}}
.bg-depth .base{{position:absolute;inset:-20%;background:
  radial-gradient(ellipse 100% 60% at 50% 40%, rgba(6,24,80,.98) 0%, rgba(2,8,23,.99) 60%),
  repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(0,229,255,.04) 40px),
  repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(0,229,255,.04) 40px);
  transform:rotateX(15deg) scale(1.3);transform-origin:center 60%;animation:basePerspective 40s ease-in-out infinite}}
.bg-depth .overlay{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(2,8,23,.02) 0%,rgba(2,8,23,.25) 30%,rgba(2,8,23,.6) 60%,rgba(2,8,23,.85) 100%)}}
.bg-depth .glow-1{{position:absolute;top:-15%;left:15%;width:900px;height:900px;background:radial-gradient(circle,rgba(0,229,255,.18),rgba(0,229,255,.03) 40%,transparent 65%);filter:blur(35px);animation:drift1 20s ease-in-out infinite}}
.bg-depth .glow-2{{position:absolute;bottom:-5%;right:10%;width:750px;height:750px;background:radial-gradient(circle,rgba(124,58,237,.2),rgba(124,58,237,.04) 40%,transparent 65%);filter:blur(40px);animation:drift2 18s ease-in-out infinite}}
.bg-depth .glow-3{{position:absolute;top:30%;left:55%;width:650px;height:650px;background:radial-gradient(circle,rgba(6,182,212,.14),rgba(6,182,212,.02) 40%,transparent 60%);filter:blur(45px);animation:drift3 22s ease-in-out infinite}}
.bg-depth .routes{{position:absolute;inset:-10%;background:
  linear-gradient(45deg, transparent 47%, rgba(0,229,255,.04) 48%, rgba(0,229,255,.06) 50%, rgba(0,229,255,.04) 52%, transparent 53%),
  linear-gradient(-45deg, transparent 47%, rgba(124,58,237,.03) 48%, rgba(124,58,237,.05) 50%, rgba(124,58,237,.03) 52%, transparent 53%),
  linear-gradient(90deg, transparent 47%, rgba(0,229,255,.02) 49%, rgba(0,229,255,.02) 51%, transparent 53%);
  background-size:45px 45px;transform:rotateX(28deg) rotateZ(-1deg) scale(1.6);transform-origin:center 70%;animation:routeShift 25s linear infinite}}
.bg-depth .particles{{position:absolute;inset:0;transform:translateZ(30px)}}
.particle{{position:absolute;width:2px;height:2px;background:#00e5ff;border-radius:50%;opacity:0;box-shadow:0 0 8px rgba(0,229,255,.6),0 0 20px rgba(0,229,255,.2);animation:particleFade 5s ease-in-out infinite}}
.pin{{position:absolute;width:6px;height:6px;border-radius:50%;background:rgba(0,229,255,.4);box-shadow:0 0 15px rgba(0,229,255,.5),0 0 35px rgba(0,229,255,.2);animation:pinPulse 3s ease-in-out infinite}}
@keyframes basePerspective{{0%,100%{{transform:rotateX(15deg) scale(1.3)}}50%{{transform:rotateX(12deg) scale(1.35)}}}}

@keyframes drift1{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(30px,-25px)}}}}
@keyframes drift2{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(-20px,30px)}}}}
@keyframes drift3{{0%,100%{{transform:translate(0,0)}}33%{{transform:translate(25px,15px)}}66%{{transform:translate(-15px,-20px)}}}}
@keyframes routeShift{{to{{background-position:50px 50px}}}}
@keyframes baseTilt{{0%,100%{{transform:rotateX(15deg) scale(1.3)}}50%{{transform:rotateX(11deg) scale(1.35)}}}}
@keyframes particleFade{{0%,100%{{opacity:0;transform:translateY(0)}}50%{{opacity:.6;transform:translateY(-20px)}}}}
@keyframes pinPulse{{0%,100%{{transform:scale(1);opacity:.4}}50%{{transform:scale(1.5);opacity:.8}}}}

/* === MOVING ANIMATIONS === */
.shooting-star{{position:absolute;width:80px;height:1px;background:linear-gradient(90deg,rgba(0,229,255,.6),transparent);border-radius:50%;opacity:0;animation:shoot 12s ease-in-out infinite}}
.shooting-star:nth-child(2){{width:60px;animation-duration:16s;animation-delay:4s}}
.shooting-star:nth-child(3){{width:100px;animation-duration:14s;animation-delay:7s}}
.shooting-star:nth-child(4){{width:50px;background:linear-gradient(90deg,rgba(124,58,237,.5),transparent);animation-duration:20s;animation-delay:10s}}
.floating-orb{{position:absolute;border-radius:50%;opacity:0;animation:floatOrb 16s ease-in-out infinite}}
.light-trail{{display:none}}
.pulse-ring{{position:absolute;border-radius:50%;border:1px solid rgba(0,229,255,.15);animation:pulseExpand 10s ease-out infinite;opacity:0}}
@keyframes shoot{{0%{{transform:translateX(-100px) translateY(0);opacity:0}}5%{{opacity:.7}}85%{{opacity:.5}}100%{{transform:translateX(calc(100vw + 100px)) translateY(100px);opacity:0}}}}
@keyframes floatOrb{{0%,100%{{opacity:0;transform:translate(0,0) scale(.8)}}25%{{opacity:.4}}50%{{opacity:.5;transform:translate(20px,-25px) scale(1.1)}}75%{{opacity:.3}}}}
@keyframes trailMove{{0%{{height:0;opacity:0;transform:translateY(-50px)}}10%{{opacity:.5;height:50px}}90%{{opacity:.3;height:30px}}100%{{opacity:0;height:0;transform:translateY(calc(100vh + 50px))}}}}
@keyframes pulseExpand{{0%{{transform:scale(0);opacity:.6}}50%{{opacity:.3}}100%{{transform:scale(3);opacity:0}}}}
@keyframes waveFloat{{0%,100%{{transform:translateX(0) scaleY(1)}}50%{{transform:translateX(20px) scaleY(1.1)}}}}

/* === GLASS CARDS === */
.glass{{background:rgba(255,255,255,.03);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.06);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.3)}}
.glass-hover{{transition:all .35s cubic-bezier(.4,0,.2,1)}}.glass-hover:hover{{border-color:rgba(0,229,255,.15);transform:translateY(-4px);box-shadow:0 16px 48px rgba(0,229,255,.06)}}

/* === CONTENT === */
.content{{position:relative;z-index:1}}

/* Nav */
.nav{{position:fixed;top:0;left:0;right:0;z-index:50;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;max-width:1100px;margin:0 auto;transition:all .3s}}
.nav-logo{{font-weight:900;font-size:1rem;background:linear-gradient(135deg,#00e5ff,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.1}}.nav-logo span:last-child{{background:none;-webkit-text-fill-color:#64748b}}
.nav-btn{{padding:8px 16px;font-size:.72rem;font-weight:600;border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;transition:all .2s;background:rgba(255,255,255,.03);backdrop-filter:blur(10px)}}.nav-btn:hover{{background:rgba(255,255,255,.08)}}

/* Hero */
.hero{{min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:60px 24px 40px}}
.hero-inner{{max-width:700px}}
.badge{{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;border-radius:50px;font-size:.72rem;font-weight:600;color:#00e5ff;margin-bottom:24px;background:rgba(0,229,255,.05);border:1px solid rgba(0,229,255,.15);backdrop-filter:blur(10px)}}
.badge .dot{{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;animation:pinPulse 2s infinite}}
.hero h1{{font-size:clamp(2.2rem,5vw,3.8rem);font-weight:900;line-height:1.08;letter-spacing:-.03em;margin-bottom:16px}}
.hero h1 span{{background:linear-gradient(135deg,#00e5ff,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero p{{font-size:clamp(.9rem,1.5vw,1.05rem);color:#94a3b8;max-width:540px;margin:0 auto 28px;line-height:1.7}}
.hero-btns{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}}
.btn-primary{{padding:14px 28px;background:linear-gradient(135deg,#00e5ff,#00b4d8);color:#020817;font-weight:700;font-size:.85rem;border-radius:12px;box-shadow:0 8px 30px rgba(0,229,255,.25);transition:all .25s}}.btn-primary:hover{{transform:translateY(-2px);box-shadow:0 12px 40px rgba(0,229,255,.35)}}
.btn-ghost{{padding:14px 28px;border:1px solid rgba(255,255,255,.12);color:#e2e8f0;font-weight:600;font-size:.85rem;border-radius:12px;backdrop-filter:blur(10px);transition:all .2s}}.btn-ghost:hover{{background:rgba(255,255,255,.05)}}
.hero-search{{max-width:420px;margin:24px auto 0;display:flex;gap:5px;padding:4px;border-radius:12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);backdrop-filter:blur(10px);justify-content:center}}.hero-search input{{flex:1;background:transparent;border:none;padding:10px 14px;color:#fff;font-size:.82rem;outline:none}}.hero-search input::placeholder{{color:#4b5563}}.hero-search button{{background:linear-gradient(135deg,#00e5ff,#00b4d8);color:#020817;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:.75rem;cursor:pointer}}
#searchResult{{max-width:420px;margin:8px auto 0}}
.hero-sub{{margin-top:24px;font-size:.75rem;font-weight:600;color:#64748b}}
.hero-sub span{{color:#00e5ff}}

/* Stats */
.stats{{padding:28px 24px;border-top:1px solid rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.04)}}
.stats-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;max-width:800px;margin:0 auto;text-align:center}}
.stat-n{{font-size:clamp(1.4rem,2.5vw,2rem);font-weight:900;background:linear-gradient(135deg,#00e5ff,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.stat-l{{font-size:.65rem;color:#4b5563;margin-top:4px;font-weight:500}}

/* Sections */
.sec{{padding:80px 24px;max-width:1000px;margin:0 auto}}
.sec-label{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#00e5ff;text-align:center;margin-bottom:8px}}
.sec-title{{font-size:clamp(1.5rem,3.5vw,2.2rem);font-weight:900;text-align:center;letter-spacing:-.02em;margin-bottom:8px}}
.sec-desc{{color:#64748b;font-size:.88rem;text-align:center;margin-bottom:36px}}

/* Features */
.feat-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.feat-card{{padding:24px;transition:all .3s}}.feat-card:hover{{border-color:rgba(0,229,255,.2);transform:translateY(-3px)}}
.feat-icon{{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;margin-bottom:14px;background:rgba(0,229,255,.06);border:1px solid rgba(0,229,255,.12)}}
.feat-card h3{{font-size:.82rem;font-weight:700;margin-bottom:6px}}.feat-card p{{font-size:.72rem;color:#94a3b8;line-height:1.6}}

/* Video */
.video-wrap{{max-width:640px;margin:0 auto;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,.08);box-shadow:0 20px 60px rgba(0,0,0,.5)}}
.video-wrap video{{display:block;width:100%;background:#0a0a0a}}

/* Categories */
.cat-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}}
.cat-item{{text-align:center;padding:16px 8px;transition:all .2s}}.cat-item:hover{{border-color:rgba(0,229,255,.2);transform:translateY(-2px)}}
.cat-item .emoji{{font-size:1.6rem;margin-bottom:6px}}.cat-item .name{{font-size:.7rem;font-weight:600}}.cat-item .cnt{{font-size:.6rem;color:#4b5563;margin-top:2px}}

/* Journey */
.journey-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.step-card{{text-align:center;padding:20px}}.step-card .icon{{font-size:1.8rem;margin-bottom:10px}}
.step-num{{font-size:.6rem;font-weight:700;color:#00e5ff;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px}}
.step-card h3{{font-size:.8rem;font-weight:700;margin-bottom:6px}}.step-card p{{font-size:.68rem;color:#94a3b8;line-height:1.5}}

/* Testimonials */
.test-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.test-card{{padding:20px}}.stars{{color:#f59e0b;font-size:.85rem;margin-bottom:10px;letter-spacing:2px}}
.test-card blockquote{{font-size:.75rem;color:#cbd5e1;line-height:1.7;font-style:italic;margin-bottom:14px}}
.test-card .author{{display:flex;align-items:center;gap:10px}}
.test-card .avatar{{width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#00e5ff,#7c3aed);display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:700}}
.test-card .name{{font-size:.72rem;font-weight:600}}.test-card .biz{{font-size:.6rem;color:#4b5563}}

/* Pricing */
.price-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;max-width:700px;margin:0 auto}}
.price-card{{padding:28px;display:flex;flex-direction:column;position:relative}}
.price-card.pop{{border-color:rgba(0,229,255,.3);box-shadow:0 0 40px rgba(0,229,255,.06)}}
.pop-badge{{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,#00e5ff,#7c3aed);color:#fff;font-size:.6rem;font-weight:700;padding:4px 12px;border-radius:50px}}
.price-card h3{{font-size:.7rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}}
.price-val{{font-size:2rem;font-weight:900;margin-bottom:4px}}.price-val small{{font-size:.7rem;color:#64748b;font-weight:500}}
.price-card ul{{list-style:none;margin:16px 0;flex:1}}.price-card li{{font-size:.72rem;color:#94a3b8;padding:5px 0;padding-left:18px;position:relative;line-height:1.5}}.price-card li::before{{content:'';position:absolute;left:0;top:9px;width:6px;height:6px;border-radius:50%;background:#00e5ff}}
.price-btn{{display:block;text-align:center;padding:12px;border-radius:10px;font-weight:700;font-size:.78rem;transition:all .2s}}
.price-btn.fill{{background:linear-gradient(135deg,#00e5ff,#7c3aed);color:#fff;box-shadow:0 8px 24px rgba(0,229,255,.2)}}.price-btn.fill:hover{{box-shadow:0 12px 32px rgba(0,229,255,.3);transform:translateY(-2px)}}
.price-btn.outline{{border:1.5px solid rgba(0,229,255,.3);color:#00e5ff}}.price-btn.outline:hover{{background:rgba(0,229,255,.05)}}

/* CTA */
.cta{{text-align:center;padding:80px 24px}}
.cta-glow{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:400px;height:200px;background:radial-gradient(ellipse,rgba(0,229,255,.08),transparent 60%);pointer-events:none}}

/* Footer */
.footer{{text-align:center;padding:24px;font-size:.68rem;color:#374151;border-top:1px solid rgba(255,255,255,.04)}}.footer b{{color:#00e5ff}}

/* WA Float */
.wa-float{{position:fixed;bottom:20px;right:20px;width:50px;height:50px;border-radius:50%;background:#25D366;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(37,211,102,.35);z-index:99;animation:wab 3s ease-in-out infinite}}@keyframes wab{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-4px)}}}}

/* Mobile */
@media(max-width:768px){{.hero{{min-height:auto;padding:80px 16px 30px}}.hero img{{max-width:320px!important}}.hero-inner{{max-width:100%}}input,select,textarea{{font-size:16px!important}}.search-box{{margin:12px auto 0!important;padding:10px 12px!important}}.search-box div{{flex-wrap:wrap;justify-content:center}}.search-box input,.search-box select{{min-width:100%!important;margin-bottom:4px}}.search-box button{{width:100%;margin-top:4px}}
.feat-grid{{grid-template-columns:repeat(2,1fr)}}
.cat-grid{{grid-template-columns:repeat(3,1fr)}}
.journey-grid{{grid-template-columns:repeat(2,1fr)}}
.test-grid{{grid-template-columns:1fr}}
.price-grid{{grid-template-columns:1fr}}
.stats-grid{{grid-template-columns:repeat(2,1fr)}}
.hero h1{{font-size:1.8rem}}
}}
@media(max-width:480px){{
.feat-grid{{grid-template-columns:1fr}}
.cat-grid{{grid-template-columns:repeat(2,1fr)}}
.journey-grid{{grid-template-columns:1fr}}
}}
</style>
<script data-cfasync="false" src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
</head><body>

<!-- 3D Depth Background -->
<div class="bg-depth">
<div class="base"></div>
<div class="routes"></div>
<div class="overlay"></div>
<div class="glow-1"></div>
<div class="glow-2"></div>
<div class="glow-3"></div>
<div class="particles">
<div class="particle" style="top:10%;left:15%;animation-delay:0s"></div>
<div class="particle" style="top:20%;left:45%;animation-delay:0.7s"></div>
<div class="particle" style="top:30%;left:70%;animation-delay:1.2s"></div>
<div class="particle" style="top:40%;left:25%;animation-delay:1.8s"></div>
<div class="particle" style="top:50%;left:85%;animation-delay:2.3s"></div>
<div class="particle" style="top:60%;left:35%;animation-delay:2.8s"></div>
<div class="particle" style="top:70%;left:60%;animation-delay:3.2s"></div>
<div class="particle" style="top:80%;left:10%;animation-delay:3.7s"></div>
<div class="particle" style="top:15%;left:90%;animation-delay:0.4s"></div>
<div class="particle" style="top:45%;left:50%;animation-delay:1.5s"></div>
<div class="particle" style="top:65%;left:80%;animation-delay:2.6s"></div>
<div class="particle" style="top:85%;left:40%;animation-delay:4s"></div>
<div class="pin" style="top:18%;left:28%;animation-delay:0s"></div>
<div class="pin" style="top:38%;left:65%;animation-delay:0.8s"></div>
<div class="pin" style="top:55%;left:80%;animation-delay:1.6s"></div>
<div class="pin" style="top:72%;left:20%;animation-delay:2.2s"></div>
<div class="pin" style="top:45%;left:42%;animation-delay:1s"></div>
<div class="pin" style="top:82%;left:70%;animation-delay:2.8s"></div>
<div class="pin" style="top:25%;left:55%;animation-delay:0.5s"></div>
</div>
<!-- Shooting Stars -->
<div class="shooting-star" style="top:12%;left:-80px;transform:rotate(15deg)"></div>
<div class="shooting-star" style="top:35%;left:-60px;transform:rotate(8deg)"></div>
<div class="shooting-star" style="top:58%;left:-100px;transform:rotate(20deg)"></div>
<div class="shooting-star" style="top:78%;left:-50px;transform:rotate(5deg)"></div>
<!-- Floating Orbs -->
<div class="floating-orb" style="top:20%;left:30%;width:12px;height:12px;background:radial-gradient(circle,rgba(0,229,255,.4),transparent);animation-delay:0s"></div>
<div class="floating-orb" style="top:50%;left:70%;width:8px;height:8px;background:radial-gradient(circle,rgba(124,58,237,.5),transparent);animation-delay:2s"></div>
<div class="floating-orb" style="top:70%;left:20%;width:10px;height:10px;background:radial-gradient(circle,rgba(6,182,212,.4),transparent);animation-delay:4s"></div>
<div class="floating-orb" style="top:35%;left:85%;width:6px;height:6px;background:radial-gradient(circle,rgba(0,229,255,.5),transparent);animation-delay:1s"></div>
<div class="floating-orb" style="top:85%;left:55%;width:14px;height:14px;background:radial-gradient(circle,rgba(124,58,237,.3),transparent);animation-delay:3s"></div>
<!-- Light Trails -->
<div class="light-trail" style="left:25%;animation-delay:0s"></div>
<div class="light-trail" style="left:55%;animation-delay:2s;background:linear-gradient(180deg,rgba(124,58,237,.5),transparent)"></div>
<div class="light-trail" style="left:80%;animation-delay:4s"></div>
<div class="light-trail" style="left:40%;animation-delay:1.5s;background:linear-gradient(180deg,rgba(6,182,212,.4),transparent)"></div>
<!-- Pulse Rings -->
<div class="pulse-ring" style="top:30%;left:45%;width:30px;height:30px;animation-delay:0s"></div>
<div class="pulse-ring" style="top:60%;left:75%;width:20px;height:20px;animation-delay:2s;border-color:rgba(124,58,237,.2)"></div>
<div class="pulse-ring" style="top:80%;left:25%;width:25px;height:25px;animation-delay:4s"></div>
</div>

<!-- Content -->
<div class="content">

<!-- Nav -->
<nav class="nav"><div class="nav-logo"><span style="font-size:1.2rem">City Maps</span><span style="display:block;font-size:.55rem;font-weight:400;color:#64748b;margin-top:-2px">Making World Digital</span></div><a href="https://ai-agency-platform-blush.vercel.app" class="nav-btn">Admin</a></nav>

<!-- Hero -->
<section class="hero">
<div class="hero-inner">


<div class="badge"><span class="dot"></span>{count}+ businesses already online</div>
<h1>Make Your Business <span>Online Free</span></h1>
<p style="font-size:.95rem;color:#94a3b8;margin-bottom:16px">Free Website, WhatsApp & Business Growth Tools</p>
<picture><source srcset="/static/images/hero-banner.webp" type="image/webp"><img src="/static/images/hero-banner-sm.jpg" alt="City Maps - Create Free Websites" style="max-width:500px;width:100%;border-radius:10px;margin-bottom:10px" loading="eager" width="500" height="300" fetchpriority="high"></picture>

<div class="search-box" style="max-width:560px;margin:20px auto 0;padding:14px 16px;border-radius:16px;background:rgba(255,255,255,.04);border:1.5px solid rgba(0,229,255,.15);box-shadow:0 12px 40px rgba(0,229,255,.1),inset 0 1px 0 rgba(255,255,255,.05);backdrop-filter:blur(12px)">
<div style="display:flex;gap:8px;flex-wrap:wrap">
<select id="sCountry" style="padding:9px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:.75rem;outline:none;min-width:70px"><option value="India">IN</option><option value="USA">US</option><option value="UK">UK</option><option value="UAE">UAE</option><option value="Australia">AU</option></select>
<input id="sBiz" placeholder="Your business name" style="flex:1;min-width:120px;padding:9px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:.75rem;outline:none">
<input id="sArea" placeholder="Area or City" style="flex:1;min-width:100px;padding:9px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:.75rem;outline:none" onkeydown="if(event.key==='Enter')pubSearch()">
<button type="button" onclick="pubSearch()" style="white-space:nowrap;padding:10px 20px;background:linear-gradient(135deg,#00e5ff,#0ea5e9);color:#020817;border:none;border-radius:10px;font-weight:800;font-size:.8rem;cursor:pointer;box-shadow:0 4px 14px rgba(0,229,255,.3);transition:all .2s">Find My Website</button>
</div>
</div>
<div id="searchResult" style="max-width:560px;margin:10px auto 0"></div>
<div class="hero-sub"><span>&#128640;</span> Boost Your Business <span style="color:#475569">|</span> <span>&#128222;</span> 24/7 Support</div>
</div>
</section>

<!-- Stats -->
<div class="stats"><div class="stats-grid">
<div><div class="stat-n">{count}+</div><div class="stat-l">Businesses Online</div></div>
<div><div class="stat-n">10K+</div><div class="stat-l">Customer Leads</div></div>
<div><div class="stat-n">50K+</div><div class="stat-l">Monthly Visits</div></div>
<div><div class="stat-n">95%</div><div class="stat-l">Mobile Traffic</div></div>
</div></div>

<!-- Features -->
<section class="sec" id="features">
<div class="sec-label">Platform</div><div class="sec-title">Everything Your Business Needs</div><div class="sec-desc">More than a website. A complete digital growth engine built for local businesses.</div>
<div class="feat-grid">
<a href="#pricing" class="feat-card glass glass-hover" style="text-decoration:none;color:inherit"><div class="feat-icon">&#127760;</div><h3>Professional Website</h3><p>Beautiful responsive site with services, gallery, map, reviews, and contact.</p></a>
<a href="#pricing" class="feat-card glass glass-hover" style="text-decoration:none;color:inherit"><div class="feat-icon">&#128172;</div><h3>WhatsApp Commerce</h3><p>One-tap order button. Customers enquire and buy directly on WhatsApp.</p></a>
<a href="#pricing" class="feat-card glass glass-hover" style="text-decoration:none;color:inherit"><div class="feat-icon">&#128205;</div><h3>Google Maps Visibility</h3><p>Show up when people search near you. Full Google profile optimization.</p></a>
<a href="#pricing" class="feat-card glass glass-hover" style="text-decoration:none;color:inherit"><div class="feat-icon">&#128722;</div><h3>Product Catalog</h3><p>Showcase products with photos, prices, and Buy Now button.</p></a>
<a href="#pricing" class="feat-card glass glass-hover" style="text-decoration:none;color:inherit"><div class="feat-icon">&#128200;</div><h3>Real-Time Analytics</h3><p>Track visitors, calls, WhatsApp clicks, and orders in real-time.</p></a>
<a href="#pricing" class="feat-card glass glass-hover" style="text-decoration:none;color:inherit"><div class="feat-icon">&#127909;</div><h3>Video &amp; Content</h3><p>Create promo videos, social posts, and stories for your business.</p></a>
</div></section>

<!-- Video -->
<section class="sec" style="text-align:center">
<div class="sec-label">See It In Action</div><div class="sec-title">Watch How It Works</div><div class="sec-desc">See how we help businesses grow online in minutes.</div>
<div class="video-wrap"><video width="100%" controls playsinline preload="metadata"><source src="/static/videos/promo.mp4" type="video/mp4"></video></div>
</section>

<!-- Categories -->
<section class="sec">
<div class="sec-label">Real Results</div><div class="sec-title">Websites We Have Built</div><div class="sec-desc">See real business websites created by our platform.</div>
<div class="cat-grid">
<div class="cat-item glass glass-hover"><div class="emoji">&#127858;</div><div class="name">Restaurants</div><div class="cnt">28+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#128135;</div><div class="name">Salons</div><div class="cnt">22+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#127947;</div><div class="name">Gyms</div><div class="cnt">15+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#129658;</div><div class="name">Clinics</div><div class="cnt">18+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#127976;</div><div class="name">Hotels</div><div class="cnt">12+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#128717;</div><div class="name">Retail</div><div class="cnt">20+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#128247;</div><div class="name">Photographers</div><div class="cnt">10+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#127968;</div><div class="name">Real Estate</div><div class="cnt">8+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#127891;</div><div class="name">Schools</div><div class="cnt">6+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#9728;</div><div class="name">Solar</div><div class="cnt">5+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#9878;</div><div class="name">Lawyers</div><div class="cnt">4+ sites</div></div>
<div class="cat-item glass glass-hover"><div class="emoji">&#9749;</div><div class="name">Cafes</div><div class="cnt">14+ sites</div></div>
</div></section>

<!-- How It Works -->
<section class="sec" style="border-top:1px solid rgba(255,255,255,.04)">
<div class="sec-label">How It Works</div><div class="sec-title">Live In 4 Simple Steps</div><div class="sec-desc">No coding. No design skills. No hassle.</div>
<div class="journey-grid">
<div class="step-card glass glass-hover"><div class="icon"><img src="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=80&h=80&fit=crop" style="width:48px;height:48px;border-radius:10px;object-fit:cover"></div><div class="step-num">Step 01</div><h3>Tell Us Your Business</h3><p>Share your business name and location. That is all we need.</p></div>
<div class="step-card glass glass-hover"><div class="icon"><img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=80&h=80&fit=crop" style="width:48px;height:48px;border-radius:10px;object-fit:cover"></div><div class="step-num">Step 02</div><h3>We Build Your Site</h3><p>We create a stunning website with SEO, products, and all features in 5 minutes.</p></div>
<div class="step-card glass glass-hover"><div class="icon"><img src="https://images.unsplash.com/photo-1432888622747-4eb9a8efeb07?w=80&h=80&fit=crop" style="width:48px;height:48px;border-radius:10px;object-fit:cover"></div><div class="step-num">Step 03</div><h3>Go Live on Google</h3><p>Your site goes live instantly. Customers find you on Google Maps.</p></div>
<div class="step-card glass glass-hover"><div class="icon"><img src="https://images.unsplash.com/photo-1556742111-a301076d9d18?w=80&h=80&fit=crop" style="width:48px;height:48px;border-radius:10px;object-fit:cover"></div><div class="step-num">Step 04</div><h3>Receive Orders</h3><p>Customers call, WhatsApp, and order directly. Watch your business grow.</p></div>
</div></section>

<!-- Testimonials -->
<section class="sec">
<div class="sec-label">Success Stories</div><div class="sec-title">Loved By Business Owners</div>
<div class="test-grid">
<div class="test-card glass glass-hover"><div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><blockquote>&ldquo;Within 2 weeks of going live, I started getting WhatsApp enquiries from new customers who found me on Google. Best Rs.49 I ever spent!&rdquo;</blockquote><div class="author"><div class="avatar" style="background:url(https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=40&h=40&fit=crop) center/cover;border-radius:50%"></div><div><div class="name">Priya Sharma</div><div class="biz">Glow Salon, Pune</div></div></div></div>
<div class="test-card glass glass-hover"><div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><blockquote>&ldquo;My patients now book appointments directly from my website. The analytics show 200+ visits per month. Incredible value.&rdquo;</blockquote><div class="author"><div class="avatar" style="background:url(https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=40&h=40&fit=crop) center/cover;border-radius:50%"></div><div><div class="name">Rajesh Patil</div><div class="biz">Patil Dental Clinic, Kothrud</div></div></div></div>
<div class="test-card glass glass-hover"><div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><blockquote>&ldquo;My website was built with precision and looks better than what I paid Rs.15000 for before. WhatsApp orders for supplements are a bonus!&rdquo;</blockquote><div class="author"><div class="avatar" style="background:url(https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=40&h=40&fit=crop) center/cover;border-radius:50%"></div><div><div class="name">Amit Gupta</div><div class="biz">FitZone Gym, Wakad</div></div></div></div>
</div></section>

<!-- Pricing -->
<section class="sec" id="pricing" style="border-top:1px solid rgba(255,255,255,.04)">
<div class="sec-label">Pricing</div><div class="sec-title">Simple Plans. Real Results.</div><div class="sec-desc">Start free trial. Cancel anytime.</div>
<div class="price-grid">
<div class="price-card glass"><h3>Growth</h3><div class="price-val">&#8377;29<small>/month</small></div><ul><li>&#127760; Professional Website</li><li>&#128722; Product Catalog</li><li>&#128200; Full Analytics Dashboard</li><li>&#128247; Social Media Posts</li><li>&#128248; QR Code Generator</li><li>&#128197; Daily Content</li><li>&#127873; Create Offers</li><li>&#128205; Google Business Setup</li><li>&#127912; Logo Generator</li><li>&#9998; Edit Website Anytime</li><li>&#128279; Social Links Page</li><li>&#128444; Gallery Photos</li><li>&#127878; Festival Offers</li></ul><a href="https://wa.me/917350785606?text=Growth%20plan%20chahiye" class="price-btn outline">Get Started</a></div>
<div class="price-card glass pop"><div class="pop-badge">POPULAR</div><h3>Premium</h3><div class="price-val">&#8377;39<small>/month</small></div><ul><li>&#127760; Professional Website</li><li>&#128722; Product Catalog</li><li>&#128200; Full Analytics Dashboard</li><li>&#128247; Social Media Posts</li><li>&#128248; QR Code Generator</li><li>&#128197; Daily Content</li><li>&#127873; Create Offers</li><li>&#128205; Google Business Setup</li><li>&#127912; Logo Generator</li><li>&#127916; Promo Video Creator</li><li>&#9998; Edit Website Anytime</li><li>&#128279; Social Links Page</li><li>&#128444; Gallery Photos</li><li>&#127878; Festival Offers</li><li>&#128170; Custom Tools (Category Based)</li><li>&#128272; Priority Support</li><li>&#127759; Custom Domain</li></ul><a href="https://wa.me/917350785606?text=Premium%20plan%20chahiye" class="price-btn fill">Go Premium</a></div>
</div></section>

<!-- CTA -->
<section class="cta" style="position:relative"><div class="cta-glow"></div>
<h2 style="font-size:clamp(1.5rem,3vw,2.2rem);font-weight:900;margin-bottom:10px;position:relative">Ready To Grow Your Business?</h2>
<p style="color:#64748b;margin-bottom:20px;font-size:.88rem;position:relative">Join {count}+ businesses already growing with City Maps.</p>
<a href="https://wa.me/917350785606?text=Hi%20City%20Maps%2C%20I%20want%20to%20create%20my%20business%20website" class="btn-primary" style="position:relative">Create My Business Website &rarr;</a>
</section>

<!-- Footer -->
<footer class="footer"><b>City Maps</b> &bull; India's Digital Presence Platform &bull; Powered by Kalpdev Digitals</footer>

</div><!-- end content -->

<!-- WA Float -->
<a href="https://wa.me/917350785606" target="_blank" class="wa-float"><svg width="24" height="24" viewBox="0 0 24 24" fill="#fff"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492l4.625-1.476A11.929 11.929 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75c-2.115 0-4.09-.57-5.793-1.564l-.415-.248-2.74.875.876-2.672-.27-.43A9.71 9.71 0 012.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75z"/></svg></a>

<!-- Parallax + Search Script -->
<script data-cfasync="false" src="/static/js/search.js?v=2"></script>
</body></html>'''
    return HTMLResponse(content=html)

@app.get("/api/health-check", response_class=HTMLResponse)
async def full_health_check():
    """Bot that checks if all features are working."""
    import httpx
    import time
    
    base = "https://ai-agency-platform.onrender.com"
    results = []
    
    checks = [
        ("Backend Health", f"{base}/health", "GET"),
        ("Landing Page", f"{base}/", "GET"),
        ("Sitemap", f"{base}/sitemap.xml", "GET"),
        ("Ad Manager", f"{base}/api/ads/manage?pwd=kalpdev2024", "GET"),
        ("Ad Serve", f"{base}/api/ads/serve?website_id=test", "GET"),
        ("Analytics", f"{base}/api/ads/analytics?pwd=kalpdev2024", "GET"),
        ("Ad Creator", f"{base}/api/ads/create-ad", "GET"),
        ("Growth Plan", f"{base}/api/growth-plan", "GET"),
        ("Sites List", f"{base}/api/sites", "GET"),
        ("Category Page", f"{base}/category/salon", "GET"),
        ("City Page", f"{base}/city/pune", "GET"),
        ("Data Deletion", f"{base}/api/data-deletion", "GET"),
        ("Search API", f"{base}/api/leads/public-search?query=test", "GET"),
        ("Dashboard Access", f"{base}/api/dashboard-access", "POST"),
    ]
    
    async with httpx.AsyncClient(timeout=10) as client:
        for name, url, method in checks:
            start = time.time()
            try:
                if method == "POST":
                    r = await client.post(url, json={"phone": "test", "website_id": "test"})
                else:
                    r = await client.get(url)
                ms = int((time.time() - start) * 1000)
                status = "ok" if r.status_code < 500 else "fail"
                results.append({"name": name, "status": status, "code": r.status_code, "ms": ms})
            except Exception as e:
                results.append({"name": name, "status": "fail", "code": 0, "ms": 0, "error": str(e)[:50]})
    
    # Check subdomain
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://plusfitnessmumbaicentral.city-maps.online/")
            results.append({"name": "Subdomain Site", "status": "ok" if r.status_code == 200 else "fail", "code": r.status_code, "ms": 0})
    except Exception as e:
        results.append({"name": "Subdomain Site", "status": "fail", "code": 0, "error": str(e)[:50]})
    
    # Check www
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://www.city-maps.online/")
            results.append({"name": "WWW Premium Site", "status": "ok" if r.status_code == 200 else "fail", "code": r.status_code, "ms": 0})
    except Exception as e:
        results.append({"name": "WWW Premium Site", "status": "fail", "code": 0, "error": str(e)[:50]})
    
    ok = sum(1 for r in results if r["status"] == "ok")
    total = len(results)
    
    rows = ""
    for r in results:
        color = "#22c55e" if r["status"] == "ok" else "#ef4444"
        rows += f'<tr><td style="padding:8px;font-size:.78rem">{r["name"]}</td><td style="padding:8px"><span style="color:{color};font-weight:700;font-size:.75rem">{"✓" if r["status"]=="ok" else "✗"} {r["code"]}</span></td><td style="padding:8px;font-size:.72rem;color:#64748b">{r.get("ms","")}ms</td></tr>'
    
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Health Check</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:600px;margin:0 auto}}table{{width:100%;border-collapse:collapse;background:#1e293b;border-radius:10px;overflow:hidden;margin-top:16px}}th{{text-align:left;padding:10px;font-size:.7rem;color:#64748b;border-bottom:1px solid #334155}}tr:hover{{background:#334155}}</style></head><body>
<h1 style="font-size:1.2rem">{ok}/{total} Features Working</h1>
<p style="font-size:.75rem;color:#64748b;margin-top:4px">Last checked: just now</p>
<div style="background:#334155;border-radius:8px;height:8px;margin-top:12px;overflow:hidden"><div style="height:100%;background:{'#22c55e' if ok==total else '#f59e0b'};width:{ok/total*100}%;border-radius:8px"></div></div>
<table><thead><tr><th>Feature</th><th>Status</th><th>Response</th></tr></thead><tbody>{rows}</tbody></table>
<p style="text-align:center;margin-top:16px;font-size:.7rem"><a href="/api/health-check" style="color:#00e5ff">Refresh</a></p>
</body></html>'''
    return HTMLResponse(content=html)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}