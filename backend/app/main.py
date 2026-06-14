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
from app.api.routes.qa_review import router as qa_router
from app.api.routes.offers import router as offers_router
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
                    html = generate_html(content, website.get("template", "store"), lead, website_id_override=website["id"])
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
app.include_router(qa_router, prefix="/api")
app.include_router(offers_router, prefix="/api")


# Mount static files
import os as _os
_static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'static')
if _os.path.isdir(_static_dir):
    app.mount('/static', StaticFiles(directory=_static_dir), name='static')

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
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Digital Growth Platform for Local Businesses</title>
<meta name="description" content="Take your business online in 5 minutes. Professional website, WhatsApp orders, Google visibility, customer growth tools.">
<meta name="theme-color" content="#020817">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,sans-serif;background:#020817;color:#fff;overflow-x:hidden;-webkit-font-smoothing:antialiased}}
a{{text-decoration:none;color:inherit}}

/* === 3D DEPTH BACKGROUND === */
.bg-depth{{position:fixed;inset:0;z-index:0;overflow:hidden}}
.bg-depth .base{{position:absolute;inset:0;background:
  radial-gradient(ellipse 120% 80% at 50% 50%, rgba(6,24,56,.95) 0%, #020817 70%),
  repeating-linear-gradient(0deg, transparent, transparent 49px, rgba(0,229,255,.02) 50px),
  repeating-linear-gradient(90deg, transparent, transparent 49px, rgba(0,229,255,.02) 50px);
  filter:blur(0.5px)}}
.bg-depth .overlay{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(2,8,23,.3) 0%,rgba(2,8,23,.6) 40%,rgba(2,8,23,.8) 70%,rgba(2,8,23,.95) 100%)}}
.bg-depth .glow-1{{position:absolute;top:-20%;left:20%;width:600px;height:600px;background:radial-gradient(circle,rgba(0,229,255,.08),transparent 60%);filter:blur(60px);animation:drift1 25s ease-in-out infinite}}
.bg-depth .glow-2{{position:absolute;bottom:-10%;right:15%;width:500px;height:500px;background:radial-gradient(circle,rgba(124,58,237,.1),transparent 60%);filter:blur(70px);animation:drift2 20s ease-in-out infinite}}
.bg-depth .glow-3{{position:absolute;top:40%;left:50%;width:400px;height:400px;background:radial-gradient(circle,rgba(6,182,212,.06),transparent 55%);filter:blur(80px);animation:drift3 22s ease-in-out infinite}}
.bg-depth .routes{{position:absolute;inset:0;background:
  linear-gradient(45deg, transparent 48%, rgba(0,229,255,.03) 49%, rgba(0,229,255,.03) 51%, transparent 52%),
  linear-gradient(-45deg, transparent 48%, rgba(124,58,237,.02) 49%, rgba(124,58,237,.02) 51%, transparent 52%);
  background-size:80px 80px;animation:routeShift 30s linear infinite}}
.bg-depth .particles{{position:absolute;inset:0}}
.particle{{position:absolute;width:3px;height:3px;background:#00e5ff;border-radius:50%;opacity:0;animation:particleFade 4s ease-in-out infinite}}
.pin{{position:absolute;width:8px;height:8px;border-radius:50%;background:rgba(0,229,255,.3);box-shadow:0 0 12px rgba(0,229,255,.2);animation:pinPulse 3s ease-in-out infinite}}

@keyframes drift1{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(30px,-25px)}}}}
@keyframes drift2{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(-20px,30px)}}}}
@keyframes drift3{{0%,100%{{transform:translate(0,0)}}33%{{transform:translate(25px,15px)}}66%{{transform:translate(-15px,-20px)}}}}
@keyframes routeShift{{to{{background-position:80px 80px}}}}
@keyframes particleFade{{0%,100%{{opacity:0;transform:translateY(0)}}50%{{opacity:.6;transform:translateY(-20px)}}}}
@keyframes pinPulse{{0%,100%{{transform:scale(1);opacity:.4}}50%{{transform:scale(1.5);opacity:.8}}}}

/* === GLASS CARDS === */
.glass{{background:rgba(255,255,255,.03);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.06);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.3)}}
.glass-hover{{transition:all .35s cubic-bezier(.4,0,.2,1)}}.glass-hover:hover{{border-color:rgba(0,229,255,.15);transform:translateY(-4px);box-shadow:0 16px 48px rgba(0,229,255,.06)}}

/* === CONTENT === */
.content{{position:relative;z-index:1}}

/* Nav */
.nav{{position:fixed;top:0;left:0;right:0;z-index:50;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;max-width:1100px;margin:0 auto;transition:all .3s}}
.nav-logo{{font-weight:900;font-size:1rem;background:linear-gradient(135deg,#00e5ff,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.nav-btn{{padding:8px 16px;font-size:.72rem;font-weight:600;border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;transition:all .2s;background:rgba(255,255,255,.03);backdrop-filter:blur(10px)}}.nav-btn:hover{{background:rgba(255,255,255,.08)}}

/* Hero */
.hero{{min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:100px 24px 60px}}
.hero-inner{{max-width:700px}}
.badge{{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;border-radius:50px;font-size:.72rem;font-weight:600;color:#00e5ff;margin-bottom:24px;background:rgba(0,229,255,.05);border:1px solid rgba(0,229,255,.15);backdrop-filter:blur(10px)}}
.badge .dot{{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;animation:pinPulse 2s infinite}}
.hero h1{{font-size:clamp(2.2rem,5vw,3.8rem);font-weight:900;line-height:1.08;letter-spacing:-.03em;margin-bottom:16px}}
.hero h1 span{{background:linear-gradient(135deg,#00e5ff,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero p{{font-size:clamp(.9rem,1.5vw,1.05rem);color:#94a3b8;max-width:540px;margin:0 auto 28px;line-height:1.7}}
.hero-btns{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}}
.btn-primary{{padding:14px 28px;background:linear-gradient(135deg,#00e5ff,#00b4d8);color:#020817;font-weight:700;font-size:.85rem;border-radius:12px;box-shadow:0 8px 30px rgba(0,229,255,.25);transition:all .25s}}.btn-primary:hover{{transform:translateY(-2px);box-shadow:0 12px 40px rgba(0,229,255,.35)}}
.btn-ghost{{padding:14px 28px;border:1px solid rgba(255,255,255,.12);color:#e2e8f0;font-weight:600;font-size:.85rem;border-radius:12px;backdrop-filter:blur(10px);transition:all .2s}}.btn-ghost:hover{{background:rgba(255,255,255,.05)}}
.hero-search{{max-width:420px;margin:24px auto 0;display:flex;gap:5px;padding:4px;border-radius:12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);backdrop-filter:blur(10px)}}.hero-search input{{flex:1;background:transparent;border:none;padding:10px 14px;color:#fff;font-size:.82rem;outline:none}}.hero-search input::placeholder{{color:#4b5563}}.hero-search button{{background:linear-gradient(135deg,#00e5ff,#00b4d8);color:#020817;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:.75rem;cursor:pointer}}
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
@media(max-width:768px){{
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
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
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
<div class="particle" style="top:15%;left:20%;animation-delay:0s"></div>
<div class="particle" style="top:35%;left:70%;animation-delay:1s"></div>
<div class="particle" style="top:55%;left:40%;animation-delay:2s"></div>
<div class="particle" style="top:75%;left:85%;animation-delay:3s"></div>
<div class="particle" style="top:25%;left:55%;animation-delay:1.5s"></div>
<div class="particle" style="top:65%;left:15%;animation-delay:2.5s"></div>
<div class="particle" style="top:85%;left:60%;animation-delay:0.5s"></div>
<div class="particle" style="top:45%;left:90%;animation-delay:3.5s"></div>
<div class="pin" style="top:20%;left:30%;animation-delay:0s"></div>
<div class="pin" style="top:50%;left:75%;animation-delay:1s"></div>
<div class="pin" style="top:70%;left:25%;animation-delay:2s"></div>
<div class="pin" style="top:35%;left:85%;animation-delay:1.5s"></div>
<div class="pin" style="top:80%;left:55%;animation-delay:2.5s"></div>
</div>
</div>

<!-- Content -->
<div class="content">

<!-- Nav -->
<nav class="nav"><div class="nav-logo">City Maps</div><a href="https://ai-agency-platform-blush.vercel.app" class="nav-btn">Admin</a></nav>

<!-- Hero -->
<section class="hero">
<div class="hero-inner">
<div class="badge"><span class="dot"></span>{count}+ businesses already online</div>
<h1>Take Your Business <span>Online</span> In 5 Minutes</h1>
<p>Professional website, WhatsApp orders, Google visibility, and customer growth tools. Everything your business needs from one platform.</p>
<div class="hero-btns"><a href="https://wa.me/917350785606?text=Hi%20City%20Maps%2C%20I%20want%20to%20create%20my%20business%20website" target="_blank" class="btn-primary">Create My Website &mdash; &#8377;49/mo</a><a href="#features" class="btn-ghost">See What You Get</a></div>
<div class="search-box glass" style="max-width:560px;margin:24px auto 0;padding:12px 14px;border-radius:14px">
<div style="display:flex;gap:8px;flex-wrap:wrap">
<select id="sCountry" style="padding:9px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:.75rem;outline:none;min-width:70px"><option value="India">IN</option><option value="USA">US</option><option value="UK">UK</option><option value="UAE">UAE</option><option value="Australia">AU</option></select>
<input id="sBiz" placeholder="Business name or type" style="flex:1;min-width:120px;padding:9px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:.75rem;outline:none">
<input id="sArea" placeholder="Area / City" style="flex:1;min-width:100px;padding:9px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:.75rem;outline:none" onkeydown="if(event.key==='Enter')pubSearch()">
<button type="button" onclick="pubSearch()" style="padding:9px 18px;background:linear-gradient(135deg,#00e5ff,#00b4d8);color:#020817;border:none;border-radius:8px;font-weight:700;font-size:.75rem;cursor:pointer;white-space:nowrap">Search</button>
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
<div class="feat-card glass glass-hover"><div class="feat-icon">&#127760;</div><h3>Professional Website</h3><p>Beautiful responsive site with services, gallery, map, reviews, and contact.</p></div>
<div class="feat-card glass glass-hover"><div class="feat-icon">&#128172;</div><h3>WhatsApp Commerce</h3><p>One-tap order button. Customers enquire and buy directly on WhatsApp.</p></div>
<div class="feat-card glass glass-hover"><div class="feat-icon">&#128205;</div><h3>Google Maps Visibility</h3><p>Show up when people search near you. Full Google profile optimization.</p></div>
<div class="feat-card glass glass-hover"><div class="feat-icon">&#128722;</div><h3>Product Catalog</h3><p>Showcase products with photos, prices, and Buy Now button.</p></div>
<div class="feat-card glass glass-hover"><div class="feat-icon">&#128200;</div><h3>Real-Time Analytics</h3><p>Track visitors, calls, WhatsApp clicks, and orders in real-time.</p></div>
<div class="feat-card glass glass-hover"><div class="feat-icon">&#127909;</div><h3>Video &amp; Content</h3><p>Create promo videos, social posts, and stories for your business.</p></div>
</div></section>

<!-- Video -->
<section class="sec" style="text-align:center">
<div class="sec-label">See It In Action</div><div class="sec-title">Watch How It Works</div><div class="sec-desc">See how we help businesses grow online in minutes.</div>
<div class="video-wrap"><video width="100%" controls playsinline preload="metadata"><source src="/static/videos/promo.mp4" type="video/mp4"></video></div>
</section>

<!-- Categories -->
<section class="sec">
<div class="sec-label">Industries</div><div class="sec-title">Built For Every Business Type</div><div class="sec-desc">We design the perfect website tailored to your industry.</div>
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
<div class="step-card glass glass-hover"><div class="icon">&#128221;</div><div class="step-num">Step 01</div><h3>Tell Us Your Business</h3><p>Share your business name and location. That is all we need.</p></div>
<div class="step-card glass glass-hover"><div class="icon">&#9889;</div><div class="step-num">Step 02</div><h3>We Build Your Site</h3><p>We create a stunning website with SEO, products, and all features in 5 minutes.</p></div>
<div class="step-card glass glass-hover"><div class="icon">&#128640;</div><div class="step-num">Step 03</div><h3>Go Live on Google</h3><p>Your site goes live instantly. Customers find you on Google Maps.</p></div>
<div class="step-card glass glass-hover"><div class="icon">&#128176;</div><div class="step-num">Step 04</div><h3>Receive Orders</h3><p>Customers call, WhatsApp, and order directly. Watch your business grow.</p></div>
</div></section>

<!-- Testimonials -->
<section class="sec">
<div class="sec-label">Success Stories</div><div class="sec-title">Loved By Business Owners</div>
<div class="test-grid">
<div class="test-card glass glass-hover"><div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><blockquote>&ldquo;Within 2 weeks of going live, I started getting WhatsApp enquiries from new customers who found me on Google. Best Rs.49 I ever spent!&rdquo;</blockquote><div class="author"><div class="avatar">P</div><div><div class="name">Priya Sharma</div><div class="biz">Glow Salon, Pune</div></div></div></div>
<div class="test-card glass glass-hover"><div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><blockquote>&ldquo;My patients now book appointments directly from my website. The analytics show 200+ visits per month. Incredible value.&rdquo;</blockquote><div class="author"><div class="avatar">R</div><div><div class="name">Rajesh Patil</div><div class="biz">Patil Dental Clinic, Kothrud</div></div></div></div>
<div class="test-card glass glass-hover"><div class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</div><blockquote>&ldquo;My website was built with precision and looks better than what I paid Rs.15000 for before. WhatsApp orders for supplements are a bonus!&rdquo;</blockquote><div class="author"><div class="avatar">A</div><div><div class="name">Amit Gupta</div><div class="biz">FitZone Gym, Wakad</div></div></div></div>
</div></section>

<!-- Pricing -->
<section class="sec" id="pricing" style="border-top:1px solid rgba(255,255,255,.04)">
<div class="sec-label">Pricing</div><div class="sec-title">Simple Plans. Real Results.</div><div class="sec-desc">Start free trial. Cancel anytime.</div>
<div class="price-grid">
<div class="price-card glass"><h3>Growth</h3><div class="price-val">&#8377;49<small>/month</small></div><ul><li>Business Website</li><li>Product Catalog</li><li>Full Analytics Dashboard</li><li>Social Media Content</li><li>WhatsApp Commerce</li><li>Customer Reviews</li><li>QR Code</li><li>Google Maps Listing</li><li>Mobile Responsive</li></ul><a href="https://wa.me/917350785606?text=Growth%20plan%20chahiye" class="price-btn outline">Get Started</a></div>
<div class="price-card glass pop"><div class="pop-badge">POPULAR</div><h3>Premium</h3><div class="price-val">&#8377;69<small>/month</small></div><ul><li>Business Website</li><li>Product Catalog</li><li>Full Analytics Dashboard</li><li>Social Media Content</li><li>WhatsApp Commerce</li><li>Customer Reviews</li><li>QR Code</li><li>Google Maps Listing</li><li>Mobile Responsive</li><li>Priority Support</li><li>Custom Domain</li><li>Advanced Analytics</li><li>Video Creator</li><li>Multi-Location</li><li>Growth Automation</li></ul><a href="https://wa.me/917350785606?text=Premium%20plan%20chahiye" class="price-btn fill">Go Premium</a></div>
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
<script src="/static/js/search.js"></script>
</body></html>'''
    return HTMLResponse(content=html)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}