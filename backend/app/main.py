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
    """City Maps premium landing page."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        sites = db.table("websites").select("slug", count="exact").not_.is_("slug", "null").execute()
        count = sites.count or 0
    except Exception:
        count = 0

    html = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Premium Websites for Local Businesses</title>
<meta name="description" content="City Maps helps local businesses grow online with professional websites, lead management, and digital marketing tools.">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Plus Jakarta Sans',sans-serif;color:#0f172a;background:#fff;overflow-x:hidden}
a{text-decoration:none}

/* NAV */
.nav{position:fixed;top:0;left:0;right:0;z-index:100;padding:16px 32px;display:flex;align-items:center;justify-content:space-between;transition:all .3s}
.nav.scrolled{background:rgba(255,255,255,.9);backdrop-filter:blur(20px);box-shadow:0 1px 0 rgba(0,0,0,.05)}
.nav-brand{font-weight:900;font-size:1.2rem;color:#0f172a;display:flex;align-items:center;gap:8px}
.nav-brand span{background:linear-gradient(135deg,#7c3aed,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.nav-btn{background:#0f172a;color:#fff;padding:10px 20px;border-radius:50px;font-weight:700;font-size:.82rem;transition:transform .2s}
.nav-btn:hover{transform:scale(1.05)}

/* HERO */
.hero{min-height:100vh;display:flex;align-items:center;position:relative;overflow:hidden;padding:100px 24px}
.hero-bg{position:absolute;inset:0;background:linear-gradient(135deg,#f8fafc 0%,#ede9fe 30%,#dbeafe 70%,#f0fdf4 100%)}
.hero-grid{position:absolute;inset:0;background-image:radial-gradient(circle at 1px 1px,rgba(124,58,237,.07) 1px,transparent 0);background-size:40px 40px}
.hero-orb1{position:absolute;top:10%;right:10%;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(124,58,237,.15),transparent 70%);filter:blur(40px);animation:float 8s ease-in-out infinite}
.hero-orb2{position:absolute;bottom:10%;left:5%;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(37,99,235,.12),transparent 70%);filter:blur(30px);animation:float 6s ease-in-out infinite reverse}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-30px)}}
.hero-content{position:relative;z-index:2;max-width:700px;margin:0 auto;text-align:center}
.hero-pill{display:inline-flex;align-items:center;gap:8px;background:#fff;border:1px solid #e2e8f0;padding:8px 16px;border-radius:50px;font-size:.8rem;font-weight:600;color:#64748b;margin-bottom:24px;box-shadow:0 4px 12px rgba(0,0,0,.04)}
.hero-pill .dot{width:8px;height:8px;border-radius:50%;background:#10b981;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.hero h1{font-size:clamp(2.4rem,6vw,4rem);font-weight:900;line-height:1.1;margin-bottom:20px;letter-spacing:-.03em}
.hero h1 .gradient{background:linear-gradient(135deg,#7c3aed,#2563eb,#0ea5e9);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero .lead{font-size:clamp(1rem,2vw,1.2rem);color:#64748b;max-width:550px;margin:0 auto 32px;line-height:1.7}
.hero-btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;padding:14px 28px;border-radius:14px;font-weight:700;font-size:.95rem;transition:all .25s}
.btn-primary{background:#0f172a;color:#fff;box-shadow:0 10px 30px rgba(15,23,42,.2)}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 16px 40px rgba(15,23,42,.3)}
.btn-secondary{background:#fff;color:#0f172a;border:1.5px solid #e2e8f0;box-shadow:0 4px 12px rgba(0,0,0,.04)}
.btn-secondary:hover{border-color:#7c3aed;color:#7c3aed}
.hero-stat{margin-top:40px;display:flex;gap:32px;justify-content:center}
.hero-stat div{text-align:center}
.hero-stat .num{font-size:1.8rem;font-weight:900;color:#0f172a}
.hero-stat .lbl{font-size:.75rem;color:#94a3b8;font-weight:500}

/* 3D CARDS SECTION */
.features{padding:100px 24px;background:#fff}
.features-head{text-align:center;max-width:600px;margin:0 auto 56px}
.features-head .tag{display:inline-block;background:#f0fdf4;color:#059669;font-size:.72rem;font-weight:700;padding:6px 14px;border-radius:50px;margin-bottom:14px;letter-spacing:.05em;text-transform:uppercase}
.features-head h2{font-size:clamp(1.8rem,4vw,2.6rem);font-weight:900;margin-bottom:12px}
.features-head p{color:#64748b;font-size:1rem}
.features-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:1000px;margin:0 auto;perspective:1000px}
.f-card{background:#fff;border:1px solid #f1f5f9;border-radius:20px;padding:28px;transition:all .4s cubic-bezier(.16,1,.3,1);transform-style:preserve-3d}
.f-card:hover{transform:translateY(-8px) rotateX(2deg) rotateY(-2deg);box-shadow:0 30px 60px rgba(124,58,237,.1);border-color:#ede9fe}
.f-card .icon{width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;margin-bottom:16px}
.f-card h3{font-size:1rem;font-weight:700;margin-bottom:8px}
.f-card p{font-size:.85rem;color:#64748b;line-height:1.6}

/* PRICING */
.pricing{padding:100px 24px;background:linear-gradient(180deg,#f8fafc,#fff)}
.pricing-head{text-align:center;max-width:500px;margin:0 auto 48px}
.pricing-head h2{font-size:clamp(1.8rem,4vw,2.6rem);font-weight:900;margin-bottom:12px}
.price-card{max-width:400px;margin:0 auto;background:#fff;border:2px solid #7c3aed;border-radius:24px;padding:40px 32px;text-align:center;box-shadow:0 20px 60px rgba(124,58,237,.12);position:relative;overflow:hidden}
.price-card::before{content:'';position:absolute;top:-2px;left:-2px;right:-2px;height:6px;background:linear-gradient(90deg,#7c3aed,#2563eb,#0ea5e9);border-radius:24px 24px 0 0}
.price-card h3{font-size:1.1rem;font-weight:700;margin-bottom:4px}
.price-card .amt{font-size:3rem;font-weight:900;color:#7c3aed;margin:12px 0}.price-card .amt small{font-size:1rem;color:#94a3b8;font-weight:500}
.price-card .perday{font-size:.82rem;color:#64748b;margin-bottom:20px}
.price-list{text-align:left;margin-bottom:24px}
.price-list .item{display:flex;align-items:center;gap:10px;padding:8px 0;font-size:.9rem;font-weight:500}
.price-list .item::before{content:'\2713';color:#059669;font-weight:800;font-size:.85rem}
.price-cta{display:block;background:#0f172a;color:#fff;padding:16px;border-radius:14px;font-weight:700;font-size:1rem;transition:transform .2s}
.price-cta:hover{transform:scale(1.02)}

/* HOW IT WORKS */
.how{padding:100px 24px;background:#0f172a;color:#fff}
.how-head{text-align:center;margin-bottom:56px}
.how-head h2{font-size:clamp(1.8rem,4vw,2.6rem);font-weight:900;margin-bottom:12px}
.how-head p{color:#94a3b8}
.how-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;max-width:900px;margin:0 auto}
.how-step{text-align:center;position:relative}
.how-step .num{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;margin:0 auto 14px;font-size:1.1rem}
.how-step h3{font-size:.95rem;font-weight:700;margin-bottom:6px}
.how-step p{font-size:.8rem;color:#94a3b8}

/* FOOTER */
.footer{padding:48px 24px;text-align:center;border-top:1px solid #f1f5f9}
.footer h3{font-size:1.1rem;font-weight:800;margin-bottom:4px}
.footer p{font-size:.82rem;color:#94a3b8}

@media(max-width:768px){
.features-grid{grid-template-columns:1fr;gap:14px}
.how-grid{grid-template-columns:repeat(2,1fr);gap:16px}
.hero-stat{gap:20px}
.nav{padding:12px 16px}
}
</style></head><body>

<nav class="nav" id="nav">
<div class="nav-brand"><span>City Maps</span></div>
<a href="https://ai-agency-platform-blush.vercel.app" class="nav-btn">Dashboard</a>
</nav>

<section class="hero">
<div class="hero-bg"></div>
<div class="hero-grid"></div>
<div class="hero-orb1"></div>
<div class="hero-orb2"></div>
<div class="hero-content">
<div class="hero-pill"><span class="dot"></span>""" + str(count) + """+ businesses already online</div>
<h1>Grow Your Business<br><span class="gradient">Online Effortlessly</span></h1>
<p class="lead">Professional websites, lead management, customer reviews, and marketing tools. Everything local businesses need to get discovered and grow.</p>
<div class="hero-btns">
<a href="https://ai-agency-platform-blush.vercel.app" class="btn btn-primary">Get Started Free &rarr;</a>
<a href="https://ai-agency-platform-blush.vercel.app" class="btn btn-secondary">Find My Business</a>
</div>
<div class="hero-stat">
<div><div class="num">""" + str(count) + """+</div><div class="lbl">Websites Created</div></div>
<div><div class="num">9</div><div class="lbl">Languages</div></div>
<div><div class="num">&#8377;69</div><div class="lbl">Per Month</div></div>
</div>
</div>
</section>

<section class="features">
<div class="features-head">
<span class="tag">&#10024; All-in-one Platform</span>
<h2>Everything Your Business Needs</h2>
<p>From websites to marketing, we handle your entire digital presence.</p>
</div>
<div class="features-grid">
<div class="f-card"><div class="icon" style="background:#f0fdf4">&#127760;</div><h3>Professional Website</h3><p>Modern, mobile-first website at your-business.city-maps.online</p></div>
<div class="f-card"><div class="icon" style="background:#ede9fe">&#128172;</div><h3>WhatsApp Integration</h3><p>One-click WhatsApp for instant customer contact</p></div>
<div class="f-card"><div class="icon" style="background:#dbeafe">&#128200;</div><h3>Business Analytics</h3><p>Track visitors, calls, WhatsApp clicks, and leads</p></div>
<div class="f-card"><div class="icon" style="background:#fef3c7">&#11088;</div><h3>Review Management</h3><p>Track and respond to customer reviews easily</p></div>
<div class="f-card"><div class="icon" style="background:#fce7f3">&#128247;</div><h3>Social Content</h3><p>Ready-to-post content for Instagram and Facebook</p></div>
<div class="f-card"><div class="icon" style="background:#ecfdf5">&#128722;</div><h3>Online Store</h3><p>Sell products via WhatsApp with a beautiful catalog</p></div>
</div>
</section>

<section class="how">
<div class="how-head">
<h2>How It Works</h2>
<p>Get online in under 5 minutes</p>
</div>
<div class="how-grid">
<div class="how-step"><div class="num">1</div><h3>Find Business</h3><p>Search your business name</p></div>
<div class="how-step"><div class="num">2</div><h3>Website Created</h3><p>Professional site built instantly</p></div>
<div class="how-step"><div class="num">3</div><h3>Claim & Manage</h3><p>Take control of your dashboard</p></div>
<div class="how-step"><div class="num">4</div><h3>Grow Online</h3><p>Get leads and customers</p></div>
</div>
</section>

<section class="pricing">
<div class="pricing-head"><h2>Simple, Transparent Pricing</h2></div>
<div class="price-card">
<h3>Business Plan</h3>
<div class="amt">&#8377;69<small>/month</small></div>
<div class="perday">Less than &#8377;3 per day</div>
<div class="price-list">
<div class="item">Professional Website</div>
<div class="item">Business Dashboard</div>
<div class="item">Lead Management</div>
<div class="item">Review Management</div>
<div class="item">Social Media Content</div>
<div class="item">WhatsApp Integration</div>
<div class="item">Online Store</div>
<div class="item">Ongoing Updates</div>
</div>
<a href="https://ai-agency-platform-blush.vercel.app" class="price-cta">Start Growing &rarr;</a>
</div>
</section>

<footer class="footer">
<h3>City Maps</h3>
<p>Your Digital Business Partner &bull; Powered by Kalpdev Digitals</p>
</footer>

<script>
window.addEventListener('scroll',()=>{document.getElementById('nav').classList.toggle('scrolled',scrollY>50)});
</script>
</body></html>"""
    return HTMLResponse(content=html)



static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "videos")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static/videos", StaticFiles(directory=static_dir), name="videos")





@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}
