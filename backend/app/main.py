from contextlib import asynccontextmanager
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
from app.automation.scheduler import start_scheduler, stop_scheduler
from app.core.logging import setup_logging

setup_logging()


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def subdomain_routing(request: Request, call_next):
    """Route subdomain requests to the correct website."""
    host = request.headers.get("host", "")
    # Check if it's a subdomain of city-maps.online
    if ".city-maps.online" in host and not host.startswith("www.") and not host.startswith("api."):
        subdomain = host.split(".city-maps.online")[0].lower().strip()
        if subdomain and subdomain not in ["www", "api", "admin"]:
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
                    html = generate_html(content, website.get("template", "store"), lead)
                    return HTMLResponse(content=html)
            # If no match, continue to normal routing
    response = await call_next(request)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


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


@app.get("/", response_class=HTMLResponse)
def landing_page():
    """City Maps - minimal modern landing page."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        sites = db.table("websites").select("slug", count="exact").not_.is_("slug", "null").execute()
        count = sites.count or 0
    except Exception:
        count = 0

    html = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Websites That Bring Customers</title>
<meta name="description" content="Professional business websites starting Rs.49/month. Get found online, get more calls.">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:Inter,sans-serif;background:#fff;color:#111}a{text-decoration:none;color:inherit}
.nav{max-width:1000px;margin:0 auto;padding:16px 24px;display:flex;align-items:center;justify-content:space-between}.nav-logo{font-weight:900;font-size:1.1rem}.nav-btn{background:#111;color:#fff;padding:8px 16px;border-radius:8px;font-size:.78rem;font-weight:600}
.hero{max-width:100%;padding:80px 24px 60px;text-align:center;background:linear-gradient(160deg,#f0f7ff 0%,#fdf2f8 30%,#faf5ff 60%,#ecfdf5 100%);position:relative;overflow:hidden}.hero::before{content:'';position:absolute;top:-50%;right:-20%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(124,58,237,.06),transparent 70%)}.hero::after{content:'';position:absolute;bottom:-30%;left:-10%;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(16,185,129,.05),transparent 70%)}
.hero .chip{display:inline-flex;align-items:center;gap:6px;background:#f4f4f5;border:1px solid #e4e4e7;padding:6px 14px;border-radius:20px;font-size:.75rem;color:#555;margin-bottom:20px}
.hero .chip .dot{width:6px;height:6px;border-radius:50%;background:#22c55e}
.hero h1{font-size:clamp(2.2rem,5vw,3.4rem);font-weight:900;line-height:1.1;margin-bottom:16px;letter-spacing:-.03em}.hero h1 em{font-style:normal;background:linear-gradient(135deg,#7c3aed,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{font-size:1.05rem;color:#666;line-height:1.6;margin-bottom:28px;max-width:500px;margin-left:auto;margin-right:auto}
.hero-search{display:flex;gap:6px;max-width:420px;margin:0 auto;border:1.5px solid #e4e4e7;border-radius:12px;padding:4px}
.hero-search input{flex:1;border:none;padding:11px 14px;font-size:.88rem;outline:none;font-family:inherit;background:transparent}
.hero-search button{background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;border:none;padding:11px 18px;border-radius:8px;font-weight:700;font-size:.8rem;cursor:pointer}
#searchResult{max-width:420px;margin:10px auto 0}
.trust{padding:20px 24px;text-align:center;border-top:1px solid #f4f4f5;border-bottom:1px solid #f4f4f5;margin-top:16px}
.trust span{font-size:.75rem;color:#999;margin:0 10px}
.section{max-width:800px;margin:0 auto;padding:60px 24px}
.sec-label{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:#999;margin-bottom:8px}
.sec-title{font-size:1.6rem;font-weight:800;margin-bottom:8px}
.sec-desc{color:#666;font-size:.92rem;margin-bottom:28px}
.features{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.feat{padding:20px;border:1px solid #f4f4f5;border-radius:12px;transition:all .2s}
.feat:hover{border-color:#e4e4e7;box-shadow:0 4px 12px rgba(0,0,0,.03)}
.feat .emoji{font-size:1.4rem;margin-bottom:8px;width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center}
.feat h3{font-size:.85rem;font-weight:700;margin-bottom:4px}.feat p{font-size:.78rem;color:#888;line-height:1.5}
.pricing{max-width:700px;margin:0 auto;padding:60px 24px;text-align:center}
.pricing-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:28px;text-align:left}
.plan{border:1.5px solid #f4f4f5;border-radius:16px;padding:24px;position:relative;transition:all .2s}
.plan:hover{border-color:#111;box-shadow:0 8px 24px rgba(0,0,0,.06)}
.plan.popular{border-color:#7c3aed;background:#faf5ff}
.plan.popular::after{content:'POPULAR';position:absolute;top:12px;right:12px;background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;font-size:.6rem;padding:3px 8px;border-radius:4px;font-weight:700}
.plan h3{font-size:.82rem;color:#888;font-weight:500;margin-bottom:4px}
.plan .price{font-size:2rem;font-weight:900;margin-bottom:2px}.plan .price small{font-size:.8rem;color:#999;font-weight:400}
.plan .desc{font-size:.78rem;color:#888;margin-bottom:16px}
.plan ul{list-style:none;margin-bottom:18px}.plan li{font-size:.8rem;color:#555;padding:5px 0;padding-left:18px;position:relative}.plan li::before{content:'\27A4';position:absolute;left:0;color:#7c3aed;font-weight:700;font-size:.7rem}
.plan-btn{display:block;text-align:center;padding:11px;border-radius:8px;font-weight:700;font-size:.82rem;transition:all .15s}
.plan-btn.dark{background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff}.plan-btn.outline{border:1.5px solid #e4e4e7;color:#111}.plan-btn:hover{transform:translateY(-1px)}
.steps{display:flex;gap:20px;margin-top:20px}
.step{flex:1;text-align:center;padding:16px 8px}.step .num{width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;display:flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:800;margin:0 auto 8px}
.step h3{font-size:.8rem;font-weight:700;margin-bottom:2px}.step p{font-size:.7rem;color:#888}
.cta{text-align:center;padding:50px 24px;background:linear-gradient(135deg,#f0f7ff,#faf5ff);border-top:none;margin-top:40px;border-radius:20px;max-width:800px;margin-left:auto;margin-right:auto}
.cta h2{font-size:1.4rem;font-weight:800;margin-bottom:8px}
.cta p{color:#666;font-size:.88rem;margin-bottom:18px}
.cta-btn{display:inline-block;background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;padding:12px 24px;border-radius:8px;font-weight:700;font-size:.88rem}
.footer{text-align:center;padding:24px;font-size:.75rem;color:#bbb}.footer b{color:#111}
@media(max-width:600px){.features{grid-template-columns:1fr}.pricing-grid{grid-template-columns:1fr}.steps{flex-direction:column;gap:8px}.hero h1{font-size:2rem}}
</style></head><body>
<nav class="nav"><div class="nav-logo">City Maps</div><a href="https://ai-agency-platform-blush.vercel.app" class="nav-btn">Admin</a></nav>
<section class="hero">
<div class="chip"><span class="dot"></span>""" + str(count) + """+ businesses online</div>
<h1>Your business website.<br><em>Ready in 5 minutes.</em></h1>
<p>Professional website for your business. Customers find you on Google, call you, message on WhatsApp. No tech skills needed.</p>
<div class="hero-search"><input id="bizSearch" placeholder="Type your business name..."><button onclick="searchBiz()">Search</button></div>
<div id="searchResult"></div>
</section>
<div class="trust"><span>Salons</span><span>&middot;</span><span>Restaurants</span><span>&middot;</span><span>Doctors</span><span>&middot;</span><span>Gyms</span><span>&middot;</span><span>Stores</span><span>&middot;</span><span>Hotels</span></div>
<section class="section">
<div class="sec-label">Features</div><div class="sec-title">Everything you need to grow</div><div class="sec-desc">Simple tools that bring more customers</div>
<div class="features">
<div class="feat"><div class="emoji" style="background:#ede9fe">&#127760;</div><h3>Business Website</h3><p>Professional mobile-friendly website showing services, photos, and location.</p></div>
<div class="feat"><div class="emoji" style="background:#dbeafe">&#128222;</div><h3>Get More Calls</h3><p>Click-to-call button. Track how many customers call from your site.</p></div>
<div class="feat"><div class="emoji" style="background:#dcfce7">&#128172;</div><h3>WhatsApp Orders</h3><p>One-tap WhatsApp with pre-filled message. Customers reach you instantly.</p></div>
<div class="feat"><div class="emoji" style="background:#fef3c7">&#128722;</div><h3>Product Catalog</h3><p>Show products with prices. Buy Now button opens WhatsApp order.</p></div>
</div>
</section>
<section class="section" style="padding-top:20px">
<div class="sec-label">Process</div><div class="sec-title">How it works</div>
<div class="steps"><div class="step"><div class="num">1</div><h3>Search</h3><p>Find your business</p></div><div class="step"><div class="num">2</div><h3>We Build</h3><p>Website created for you</p></div><div class="step"><div class="num">3</div><h3>Go Live</h3><p>Your site is online</p></div><div class="step"><div class="num">4</div><h3>Grow</h3><p>Get calls & messages</p></div></div>
</section>
<section class="pricing" id="pricing">
<div class="sec-label">Pricing</div><div class="sec-title">Simple plans. No surprises.</div>
<div class="pricing-grid">
<div class="plan"><h3>Starter</h3><div class="price">&#8377;49<small>/mo</small></div><div class="desc">Just your website, live and running</div><ul><li>Professional business website</li><li>your-name.city-maps.online</li><li>Mobile-friendly design</li><li>WhatsApp button</li><li>Google Maps location</li><li>Contact form</li></ul><a href="https://wa.me/917350785606?text=Hi%2C%20I%20want%20the%20Starter%20plan%20at%20Rs.49" class="plan-btn outline">Get Started</a></div>
<div class="plan popular"><h3>Business</h3><div class="price">&#8377;69<small>/mo</small></div><div class="desc">Website + tools to grow your business</div><ul><li>Everything in Starter</li><li>Product catalog</li><li>Track visitors & calls</li><li>Social media posts</li><li>Festival templates</li><li>Google review help</li><li>QR code for cards</li><li>Business dashboard</li></ul><a href="https://wa.me/917350785606?text=Hi%2C%20I%20want%20the%20Business%20plan%20at%20Rs.69" class="plan-btn dark">Get Started</a></div>
</div>
</section>
<div class="cta"><h2>Your competitor is already online.</h2><p>Every day you wait, customers go to them instead of you.</p><a href="https://wa.me/917350785606?text=Hi%20City%20Maps%2C%20I%20want%20a%20website%20for%20my%20business" class="cta-btn">Create My Website &rarr;</a></div>
<footer class="footer"><b>City Maps</b> &bull; Powered by Kalpdev Digitals</footer>
<script>
async function searchBiz(){const q=document.getElementById('bizSearch').value.trim();if(!q)return;const r=document.getElementById('searchResult');r.style.display='block';r.innerHTML='<p style="text-align:center;color:#999;font-size:.82rem">Searching...</p>';try{const slug=q.toLowerCase().replace(/[^a-z0-9\s-]/g,'').replace(/[\s]+/g,'-');const resp=await fetch('/api/preview/by-slug/'+slug);if(resp.ok){r.innerHTML='<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px;text-align:center;margin-top:8px"><p style="font-weight:700;color:#166534;font-size:.85rem">&#10004; Found!</p><a href="https://'+slug+'.city-maps.online" target="_blank" style="color:#111;font-weight:600;font-size:.82rem">Visit website &rarr;</a></div>';}else{throw new Error('nf');}}catch(e){r.innerHTML='<div style="border:1px solid #e4e4e7;border-radius:10px;padding:16px;margin-top:8px;text-align:center"><p style="font-weight:600;font-size:.88rem;margin-bottom:8px">Not found</p><p style="font-size:.78rem;color:#888;margin-bottom:12px">Want a free website?</p><form onsubmit="submitReq(event)" style="display:flex;flex-direction:column;gap:6px;max-width:280px;margin:0 auto"><input id="reqName" value="'+q+'" required style="padding:9px 12px;border:1px solid #e4e4e7;border-radius:8px;font-size:.82rem"><input id="reqPhone" placeholder="WhatsApp Number" required style="padding:9px 12px;border:1px solid #e4e4e7;border-radius:8px;font-size:.82rem"><input id="reqCity" placeholder="City" required style="padding:9px 12px;border:1px solid #e4e4e7;border-radius:8px;font-size:.82rem"><button type="submit" style="background:#111;color:#fff;padding:10px;border:none;border-radius:8px;font-weight:700;font-size:.82rem;cursor:pointer">Request Website</button></form></div>';}}
async function submitReq(e){e.preventDefault();try{await fetch('/api/website-requests',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({business_name:document.getElementById('reqName').value,phone:document.getElementById('reqPhone').value,city:document.getElementById('reqCity').value})});document.getElementById('searchResult').innerHTML='<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px;text-align:center;margin-top:8px"><p style="font-weight:700;color:#166534;font-size:.85rem">&#10004; Submitted!</p><p style="font-size:.78rem;color:#888">We will notify you within 24 hours.</p></div>';}catch(err){alert('Failed.');}}
</script></body></html>"""
    return HTMLResponse(content=html)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}
