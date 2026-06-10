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
    """City Maps landing page."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        sites = db.table("websites").select("slug", count="exact").not_.is_("slug", "null").execute()
        count = sites.count or 0
    except Exception:
        count = 0

    html = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Grow Your Business Online</title>
<meta name="description" content="City Maps helps local businesses establish a strong online presence. Professional websites, lead management, reviews, and marketing tools starting at Rs.69/month.">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Plus Jakarta Sans',sans-serif;color:#1e293b;line-height:1.7}
.hero{background:linear-gradient(135deg,#0f172a,#1e1b4b);color:#fff;padding:80px 24px;text-align:center}
.hero h1{font-size:clamp(2rem,5vw,3.2rem);font-weight:900;margin-bottom:16px;max-width:700px;margin-left:auto;margin-right:auto}
.hero p{color:#94a3b8;font-size:1.05rem;max-width:600px;margin:0 auto 24px}
.hero .sub{font-size:.85rem;color:#64748b;max-width:500px;margin:0 auto 28px}
.btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.btn{padding:14px 28px;border-radius:50px;font-weight:700;font-size:.95rem;text-decoration:none;transition:transform .2s}
.btn-primary{background:linear-gradient(135deg,#7c3aed,#a78bfa);color:#fff;box-shadow:0 8px 24px rgba(124,58,237,.3)}
.btn-outline{background:transparent;color:#fff;border:2px solid rgba(255,255,255,.3)}
.btn:hover{transform:translateY(-2px)}
.section{padding:70px 24px;max-width:900px;margin:0 auto}
.section-alt{background:#f8fafc}
.section h2{font-size:1.8rem;font-weight:800;margin-bottom:12px;text-align:center}
.section .lead{text-align:center;color:#64748b;margin-bottom:32px;font-size:1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;margin-top:20px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px}
.card h3{font-size:1rem;font-weight:700;margin-bottom:8px}
.card p{font-size:.88rem;color:#64748b}
.check{color:#059669;font-weight:700;margin-bottom:6px;font-size:.9rem}
.pricing{text-align:center;padding:60px 24px;background:linear-gradient(135deg,#f5f3ff,#ede9fe)}
.price-card{background:#fff;border-radius:20px;padding:32px;max-width:380px;margin:0 auto;box-shadow:0 10px 40px rgba(124,58,237,.1);border:2px solid #7c3aed}
.price-card h3{font-size:1.2rem;font-weight:800;margin-bottom:4px}
.price-card .amount{font-size:2.5rem;font-weight:900;color:#7c3aed;margin:12px 0}
.price-card .amount small{font-size:1rem;font-weight:500;color:#64748b}
.price-card .per-day{font-size:.82rem;color:#64748b;margin-bottom:16px}
.price-features{text-align:left;margin-bottom:20px}
.price-features .check{margin-bottom:8px}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-top:24px}
.step{text-align:center;padding:16px}
.step-num{width:40px;height:40px;border-radius:50%;background:#7c3aed;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;margin:0 auto 12px}
.step h3{font-size:.95rem;font-weight:700;margin-bottom:4px}
.step p{font-size:.82rem;color:#64748b}
.footer{background:#0f172a;color:#94a3b8;text-align:center;padding:32px 24px}
.footer h3{color:#fff;font-weight:800;margin-bottom:4px}
.footer p{font-size:.82rem}
.stat{font-size:2.5rem;font-weight:900;color:#7c3aed}
@media(max-width:640px){.hero{padding:50px 16px}.hero h1{font-size:1.8rem}.section{padding:50px 16px}}
</style></head><body>

<section class="hero">
<div class="stat">""" + str(count) + """+</div>
<p style="font-size:.85rem;color:#64748b;margin-bottom:20px">Businesses Online</p>
<h1>Grow Your Business Online</h1>
<p>Website &bull; Leads &bull; Reviews &bull; Marketing &bull; Digital Presence</p>
<p class="sub">City Maps helps local businesses establish a strong online presence and attract more customers. Whether you're a salon, restaurant, doctor, gym, retailer, or service provider.</p>
<div class="btns">
<a href="https://ai-agency-platform-blush.vercel.app" class="btn btn-primary">Get Started</a>
<a href="https://ai-agency-platform-blush.vercel.app" class="btn btn-outline">Find My Business</a>
</div>
</section>

<section class="section">
<h2>Everything Your Business Needs Online</h2>
<p class="lead">Your customers are searching online every day. Make sure they find you.</p>
<div class="grid">
<div class="card"><div class="check">&#10004; Professional Website</div><p>Modern website that works on mobile, tablet, and desktop. Available at business-name.city-maps.online</p></div>
<div class="card"><div class="check">&#10004; WhatsApp Integration</div><p>Customers can reach you instantly via WhatsApp with one click from your website.</p></div>
<div class="card"><div class="check">&#10004; Lead Collection</div><p>Never miss a customer. Track enquiries from website forms, phone calls, and WhatsApp clicks.</p></div>
<div class="card"><div class="check">&#10004; Customer Reviews</div><p>Build trust with reviews. Track, respond, and improve your online rating.</p></div>
<div class="card"><div class="check">&#10004; Business Analytics</div><p>See who visits your website, how they found you, and what actions they take.</p></div>
<div class="card"><div class="check">&#10004; Social Media Content</div><p>Ready-to-post content for Instagram, Facebook, and WhatsApp status. Festival campaigns included.</p></div>
</div>
</section>

<section class="section section-alt">
<h2>How It Works</h2>
<div class="steps">
<div class="step"><div class="step-num">1</div><h3>Find Your Business</h3><p>Search your business or create a new profile.</p></div>
<div class="step"><div class="step-num">2</div><h3>We Create Your Presence</h3><p>Your website and tools are set up automatically.</p></div>
<div class="step"><div class="step-num">3</div><h3>Claim & Manage</h3><p>Take control of your business dashboard.</p></div>
<div class="step"><div class="step-num">4</div><h3>Grow Online</h3><p>Start receiving enquiries and growing your customer base.</p></div>
</div>
</section>

<section class="pricing">
<h2>Simple Pricing</h2>
<p class="lead">Less than &#8377;3 per day.</p>
<div class="price-card">
<h3>Business Plan</h3>
<div class="amount">&#8377;69<small>/month</small></div>
<div class="per-day">That's just &#8377;2.3 per day</div>
<div class="price-features">
<div class="check">&#10004; Website Hosting</div>
<div class="check">&#10004; Business Dashboard</div>
<div class="check">&#10004; Lead Management</div>
<div class="check">&#10004; Review Management</div>
<div class="check">&#10004; Social Content</div>
<div class="check">&#10004; Digital Presence Tools</div>
<div class="check">&#10004; Ongoing Updates</div>
</div>
<a href="https://ai-agency-platform-blush.vercel.app" class="btn btn-primary" style="display:block;text-align:center">Get Started &rarr;</a>
</div>
</section>

<section class="section">
<h2>Built For Indian Businesses</h2>
<p class="lead">Simple. Affordable. Easy to Use.</p>
<div class="grid">
<div class="card"><h3>No Technical Knowledge</h3><p>Everything is set up for you. Just claim and manage.</p></div>
<div class="card"><h3>Multi-Language</h3><p>Available in English, Hindi, and Hinglish.</p></div>
<div class="card"><h3>Local Focus</h3><p>Designed specifically for Indian local businesses.</p></div>
</div>
</section>

<footer class="footer">
<h3>City Maps Online</h3>
<p>Your Digital Business Partner</p>
<p style="margin-top:8px">Powered by Kalpdev Digitals</p>
</footer>
</body></html>"""
    return HTMLResponse(content=html)



static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "videos")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static/videos", StaticFiles(directory=static_dir), name="videos")





@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}
