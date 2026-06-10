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
    """City Maps - dark glassmorphism landing page."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        sites = db.table("websites").select("slug", count="exact").not_.is_("slug", "null").execute()
        count = sites.count or 0
    except Exception:
        count = 0

    html = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Smart Digital Presence for Local Businesses</title>
<meta name="description" content="Professional websites and growth tools for local businesses. Get found online, attract customers, grow revenue.">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<link href="https://unpkg.com/aos@2.3.4/dist/aos.css" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Plus Jakarta Sans',sans-serif;background:#ffffff;color:#1e293b;overflow-x:hidden;min-height:100vh}
a{text-decoration:none;color:inherit}

/* GLOBAL */
.container{max-width:1100px;margin:0 auto;padding:0 24px}
.glass{background:#fff;border:1px solid #f1f5f9;backdrop-filter:blur(12px);border-radius:20px}
.tag{display:inline-flex;align-items:center;gap:6px;background:rgba(124,58,237,.12);border:1px solid rgba(124,58,237,.25);padding:6px 14px;border-radius:50px;font-size:.72rem;font-weight:600;color:#a78bfa;letter-spacing:.03em}
.sec-title{font-size:clamp(1.8rem,4vw,2.6rem);font-weight:900;margin-bottom:12px;letter-spacing:-.03em}
.sec-sub{color:#64748b;font-size:1rem;max-width:500px}

/* NAV */
.nav{position:fixed;top:0;left:0;right:0;z-index:100;padding:16px 32px;display:flex;align-items:center;justify-content:space-between}
.nav.solid{background:rgba(255,255,255,.95);backdrop-filter:blur(20px);border-bottom:1px solid #f1f5f9}
.nav-brand{font-weight:900;font-size:1.15rem;background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.nav-links{display:flex;gap:24px;font-size:.85rem;color:#64748b}
.nav-links a:hover{color:#fff}
.nav-btn{background:rgba(255,255,255,.08);border:1px solid #e2e8f0;color:#fff;padding:9px 18px;border-radius:50px;font-weight:600;font-size:.8rem;transition:all .2s}
.nav-btn:hover{background:rgba(255,255,255,.14)}

/* HERO */
.hero{min-height:100vh;display:flex;align-items:center;position:relative;padding:120px 24px 80px;overflow:hidden}
.hero-glow{position:absolute;top:-200px;left:50%;transform:translateX(-50%);width:800px;height:800px;border-radius:50%;background:radial-gradient(circle,rgba(124,58,237,.08) 0%,rgba(37,99,235,.04) 40%,transparent 65%);filter:blur(60px);animation:breathe 8s ease-in-out infinite}
@keyframes breathe{0%,100%{opacity:.8;transform:translateX(-50%) scale(1)}50%{opacity:1;transform:translateX(-50%) scale(1.05)}}
.hero-grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.02) 1px,transparent 1px);background-size:60px 60px}

.hero-inner{position:relative;z-index:2;text-align:center;max-width:750px;margin:0 auto}
.hero-pill{display:inline-flex;align-items:center;gap:8px;background:#f8fafc;border:1px solid #e2e8f0;padding:8px 16px;border-radius:50px;font-size:.78rem;color:#64748b;margin-bottom:28px}
.hero-pill .pulse{width:8px;height:8px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.hero h1{font-size:clamp(2.6rem,6vw,4.2rem);font-weight:900;line-height:1.05;margin-bottom:20px;letter-spacing:-.04em}
.hero h1 .grad{background:linear-gradient(135deg,#a78bfa,#60a5fa,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero .lead{font-size:1.1rem;color:#64748b;line-height:1.7;margin-bottom:32px;max-width:580px;margin-left:auto;margin-right:auto}
.hero-btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:20px}
.btn-glow{background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;padding:14px 28px;border-radius:14px;font-weight:700;font-size:.92rem;box-shadow:0 8px 32px rgba(124,58,237,.35);transition:all .25s}
.btn-glow:hover{transform:translateY(-2px);box-shadow:0 12px 40px rgba(124,58,237,.5)}
.btn-glass{background:#f8fafc;border:1px solid #e2e8f0;color:#fff;padding:14px 28px;border-radius:14px;font-weight:700;font-size:.92rem;transition:all .25s}
.btn-glass:hover{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.2)}

/* SEARCH */
.search-box{max-width:500px;margin:32px auto 0;display:flex;gap:8px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:6px}
.search-box input{flex:1;background:transparent;border:none;padding:12px 16px;color:#fff;font-size:.9rem;outline:none;font-family:inherit}
.search-box input::placeholder{color:#64748b}
.search-box button{background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;border:none;padding:12px 20px;border-radius:10px;font-weight:700;font-size:.82rem;cursor:pointer}
#searchResult{margin-top:14px}

/* STATS */
.stats-row{display:flex;gap:24px;justify-content:center;margin-top:48px}
.stat-pill{background:#fff;border:1px solid #f1f5f9;border-radius:14px;padding:16px 24px;text-align:center}
.stat-pill .num{font-size:1.5rem;font-weight:800;margin-bottom:2px}
.stat-pill .lbl{font-size:.72rem;color:#64748b}

/* FEATURES */
.features{padding:120px 24px;position:relative}
.features::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(124,58,237,.3),transparent)}
.f-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:48px}
.f-card{padding:28px 24px;border-radius:20px;background:#fff;border:1px solid #f8fafc;transition:all .35s;position:relative;overflow:hidden}
.f-card:hover{background:#f8fafc;border-color:#ede9fe;transform:translateY(-4px)}
.f-card::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#7c3aed,#2563eb);opacity:0;transition:opacity .3s}.f-card:hover::after{opacity:1}
.f-card .ic{width:44px;height:44px;border-radius:12px;background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.2);display:flex;align-items:center;justify-content:center;font-size:1.2rem;margin-bottom:16px}
.f-card h3{font-size:.95rem;font-weight:700;margin-bottom:8px;color:#1e293b}
.f-card p{font-size:.82rem;color:#64748b;line-height:1.6}

/* PRICING */
.pricing{padding:120px 24px;position:relative}
.pricing::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(96,165,250,.3),transparent)}
.p-card{max-width:380px;margin:48px auto 0;background:#fff;border:1px solid #e2e8f0;border-radius:24px;padding:36px;text-align:center;position:relative;overflow:hidden}
.p-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#7c3aed,#2563eb,#10b981)}
.p-card h3{font-size:1rem;font-weight:600;color:#64748b;margin-bottom:8px}
.p-card .price{font-size:3.2rem;font-weight:900;background:linear-gradient(135deg,#fff,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px}
.p-card .price small{font-size:1rem;-webkit-text-fill-color:#64748b}
.p-card .per{font-size:.82rem;color:#64748b;margin-bottom:24px}
.p-list{text-align:left;margin-bottom:28px}.p-list .pi{display:flex;align-items:center;gap:10px;padding:9px 0;font-size:.88rem;color:#475569;border-bottom:1px solid rgba(255,255,255,.04)}.p-list .pi::before{content:'\2713';color:#10b981;font-weight:800;font-size:.8rem}
.p-cta{display:block;background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;padding:14px;border-radius:12px;font-weight:700;font-size:.95rem;transition:all .25s;box-shadow:0 8px 24px rgba(124,58,237,.3)}.p-cta:hover{transform:translateY(-2px);box-shadow:0 12px 32px rgba(124,58,237,.4)}

/* HOW */
.how{padding:120px 24px}
.how::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(52,211,153,.3),transparent)}
.how-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-top:48px}
.how-step{text-align:center;padding:24px 16px;border-radius:16px;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);transition:all .3s}
.how-step:hover{background:#fff;border-color:rgba(255,255,255,.1)}
.how-step .num{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;margin:0 auto 12px;font-size:.9rem}
.how-step h3{font-size:.88rem;font-weight:700;color:#1e293b;margin-bottom:4px}
.how-step p{font-size:.78rem;color:#64748b}

/* CTA */
.cta-sec{padding:100px 24px;text-align:center;position:relative}
.cta-glow{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:600px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(124,58,237,.12),transparent 60%);filter:blur(40px)}
.cta-sec h2{position:relative;z-index:2;font-size:clamp(1.6rem,4vw,2.4rem);font-weight:900;margin-bottom:12px}
.cta-sec p{position:relative;z-index:2;color:#64748b;margin-bottom:24px}

.footer{padding:40px 24px;text-align:center;border-top:1px solid rgba(255,255,255,.05)}
.footer h3{font-size:.95rem;font-weight:700;background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px}
.footer p{font-size:.78rem;color:#4b5563}

@media(max-width:768px){.f-grid{grid-template-columns:1fr}.how-grid{grid-template-columns:repeat(2,1fr)}.stats-row{flex-wrap:wrap;gap:12px}.nav-links{display:none}.hero h1{font-size:2.2rem}}
</style></head><body>

<nav class="nav" id="nav">
<div class="nav-brand">City Maps</div>
<div class="nav-links"><a href="#features">Features</a><a href="#pricing">Pricing</a><a href="#how">How It Works</a></div>
<a href="https://ai-agency-platform-blush.vercel.app" class="nav-btn">Admin</a>
</nav>

<section class="hero">
<div class="hero-glow"></div>
<div class="hero-grid"></div>
<div class="hero-inner">
<div class="hero-pill" data-aos="fade-down"><span class="pulse"></span>""" + str(count) + """+ businesses online</div>
<h1 data-aos="fade-up">Your Business<br><span class="grad">Deserves to Shine Online</span></h1>
<p class="lead" data-aos="fade-up" data-aos-delay="100">Customers search Google daily for businesses like yours. Without a website, they find your competitor instead. We fix that in 5 minutes.</p>
<div class="hero-btns" data-aos="fade-up" data-aos-delay="200">
<a href="#pricing" class="btn-glow">Get Started &rarr;</a>
<a href="#features" class="btn-glass">See Features</a>
</div>
<div class="search-box" data-aos="fade-up" data-aos-delay="300">
<input id="bizSearch" type="text" placeholder="Search your business name...">
<button onclick="searchBiz()">Search</button>
</div>
<div id="searchResult"></div>
<div style="margin-top:40px;display:flex;justify-content:center;gap:16px;flex-wrap:wrap" data-aos="fade-up" data-aos-delay="350">
<img src="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=280&h=180&fit=crop" style="border-radius:14px;border:1px solid #e2e8f0;box-shadow:0 10px 30px rgba(0,0,0,.3)" alt="Store">
<img src="https://images.unsplash.com/photo-1560066984-138dadb4c035?w=280&h=180&fit=crop" style="border-radius:14px;border:1px solid #e2e8f0;box-shadow:0 10px 30px rgba(0,0,0,.3)" alt="Salon">
<img src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=280&h=180&fit=crop" style="border-radius:14px;border:1px solid #e2e8f0;box-shadow:0 10px 30px rgba(0,0,0,.3)" alt="Restaurant">
</div>
<div class="stats-row" data-aos="fade-up" data-aos-delay="400">
<div class="stat-pill"><div class="num">""" + str(count) + """+</div><div class="lbl">Websites Live</div></div>
<div class="stat-pill"><div class="num">9</div><div class="lbl">Languages</div></div>
<div class="stat-pill"><div class="num">24/7</div><div class="lbl">Always Online</div></div>
</div>
</div>
</section>

<section class="features" id="features">
<div class="container">
<div style="text-align:center" data-aos="fade-up">
<span class="tag">&#9889; Growth Tools</span>
<h2 class="sec-title" style="margin-top:12px">Tools That Bring You Customers</h2>
<p class="sec-sub" style="margin:0 auto">Every tool designed to get you more calls, walk-ins, and revenue</p>
</div>
<div class="f-grid">
<div class="f-card" data-aos="fade-up"><img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=160&fit=crop" style="width:100%;height:120px;object-fit:cover;border-radius:12px;margin-bottom:14px;opacity:.85"><h3>Your Own Website</h3><p>Customers find you on Google, see services, photos, reviews. Contact you instantly. Works on every phone.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="60"><img src="https://images.unsplash.com/photo-1423666639041-f56000c27a9a?w=400&h=160&fit=crop" style="width:100%;height:120px;object-fit:cover;border-radius:12px;margin-bottom:14px;opacity:.85"><h3>More Phone Calls</h3><p>Click-to-call on every page. See how many people call from your website each day in your dashboard.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="120"><img src="https://images.unsplash.com/photo-1611746872915-64382b5c76da?w=400&h=160&fit=crop" style="width:100%;height:120px;object-fit:cover;border-radius:12px;margin-bottom:14px;opacity:.85"><h3>WhatsApp Enquiries</h3><p>One-tap WhatsApp with pre-filled message. Customers don't need to save your number or type anything.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="180"><img src="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400&h=160&fit=crop" style="width:100%;height:120px;object-fit:cover;border-radius:12px;margin-bottom:14px;opacity:.85"><h3>More Google Reviews</h3><p>Ready messages to send happy customers asking for reviews. More reviews = higher Google ranking.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="240"><img src="https://images.unsplash.com/photo-1611162616305-c69b3fa7fbe0?w=400&h=160&fit=crop" style="width:100%;height:120px;object-fit:cover;border-radius:12px;margin-bottom:14px;opacity:.85"><h3>Social Media Posts</h3><p>Download beautiful Instagram and WhatsApp status posts with your business name. No designer needed.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="300"><img src="https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=400&h=160&fit=crop" style="width:100%;height:120px;object-fit:cover;border-radius:12px;margin-bottom:14px;opacity:.85"><h3>Product Catalog</h3><p>Show products with prices. Customer clicks Buy Now, WhatsApp opens with their order. Simple selling.</p></div>
</div>
</div>
</section>

<section class="how" id="how" style="position:relative">
<div class="container">
<div style="text-align:center" data-aos="fade-up"><span class="tag">&#128640; Quick Start</span><h2 class="sec-title" style="margin-top:12px">Online in 5 Minutes</h2></div>
<div class="how-grid">
<div class="how-step" data-aos="fade-up"><div class="num">1</div><h3>Search Business</h3><p>Type your business name above</p></div>
<div class="how-step" data-aos="fade-up" data-aos-delay="80"><div class="num">2</div><h3>Website Created</h3><p>We build your website professionally</p></div>
<div class="how-step" data-aos="fade-up" data-aos-delay="160"><div class="num">3</div><h3>Claim & Manage</h3><p>Access your tools dashboard</p></div>
<div class="how-step" data-aos="fade-up" data-aos-delay="240"><div class="num">4</div><h3>Get Customers</h3><p>Start receiving calls and messages</p></div>
</div>
</div>
</section>

<section style="padding:60px 24px;text-align:center">
<p style="font-size:.72rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px">Trusted by businesses in</p>
<div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;max-width:700px;margin:0 auto">
<span style="background:#fff;border:1px solid #f1f5f9;padding:8px 18px;border-radius:50px;font-size:.82rem;color:#64748b">Pune</span>
<span style="background:#fff;border:1px solid #f1f5f9;padding:8px 18px;border-radius:50px;font-size:.82rem;color:#64748b">Mumbai</span>
<span style="background:#fff;border:1px solid #f1f5f9;padding:8px 18px;border-radius:50px;font-size:.82rem;color:#64748b">Bangalore</span>
<span style="background:#fff;border:1px solid #f1f5f9;padding:8px 18px;border-radius:50px;font-size:.82rem;color:#64748b">Delhi</span>
<span style="background:#fff;border:1px solid #f1f5f9;padding:8px 18px;border-radius:50px;font-size:.82rem;color:#64748b">Hyderabad</span>
<span style="background:#fff;border:1px solid #f1f5f9;padding:8px 18px;border-radius:50px;font-size:.82rem;color:#64748b">Chennai</span>
<span style="background:#fff;border:1px solid #f1f5f9;padding:8px 18px;border-radius:50px;font-size:.82rem;color:#64748b">Nashik</span>
</div>
</section>
<section class="pricing" id="pricing" style="position:relative">
<div class="container">
<div style="text-align:center" data-aos="fade-up"><span class="tag">&#128176; Simple Pricing</span><h2 class="sec-title" style="margin-top:12px">&#9749; Chai se bhi kam</h2></div>
<div class="p-card" data-aos="zoom-in">
<h3>Business Plan</h3>
<div class="price">&#8377;69<small>/mo</small></div>
<div class="per">Just &#8377;2.3 per day</div>
<div class="p-list">
<div class="pi">Professional website (your-name.city-maps.online)</div>
<div class="pi">Track visitors, calls, and messages</div>
<div class="pi">WhatsApp click-to-chat integration</div>
<div class="pi">Product catalog with Buy Now button</div>
<div class="pi">Social media post downloads</div>
<div class="pi">Festival campaign templates</div>
<div class="pi">Google review request messages</div>
<div class="pi">QR code for visiting cards</div>
<div class="pi">Daily business growth tips</div>
</div>
<a href="https://wa.me/917350785606?text=Hi%2C%20I%20want%20the%20Business%20Plan%20at%20Rs.69%2Fmonth" class="p-cta">Start Growing &rarr;</a>
</div>
</div>
</section>

<section class="cta-sec">
<div class="cta-glow"></div>
<h2 data-aos="fade-up">Stop Losing Customers to Competitors</h2>
<p data-aos="fade-up">""" + str(count) + """+ businesses are already online. Don't get left behind.</p>
<a href="https://wa.me/917350785606?text=Hi%20City%20Maps%2C%20I%20want%20to%20create%20my%20business%20website" class="btn-glow" data-aos="fade-up" style="position:relative;z-index:2">Create My Website &rarr;</a>
</section>

<footer class="footer">
<h3>City Maps</h3>
<p>Your Digital Business Partner &bull; Powered by Kalpdev Digitals</p>
</footer>

<script>
async function searchBiz(){const q=document.getElementById('bizSearch').value.trim();if(!q)return;const r=document.getElementById('searchResult');r.style.display='block';r.innerHTML='<p style="text-align:center;color:#64748b;font-size:.85rem">Searching...</p>';try{const slug=q.toLowerCase().replace(/[^a-z0-9\s-]/g,'').replace(/[\s]+/g,'-');const resp=await fetch('/api/preview/by-slug/'+slug);if(resp.ok){r.innerHTML='<div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:12px;padding:14px;text-align:center;margin-top:12px"><p style="font-weight:700;color:#10b981;margin-bottom:6px">&#10004; Your business is online!</p><a href="https://'+slug+'.city-maps.online" target="_blank" style="color:#a78bfa;font-weight:600;font-size:.88rem">Visit your website &rarr;</a></div>';}else{throw new Error('nf');}}catch(e){r.innerHTML='<div style="background:#fff;border:1px solid #f1f5f9;border-radius:12px;padding:18px;margin-top:12px;text-align:center"><p style="font-weight:600;color:#1e293b;margin-bottom:10px">Website not found for &quot;'+q+'&quot;</p><p style="font-size:.82rem;color:#64748b;margin-bottom:14px">Want a free website for your business?</p><form onsubmit="submitReq(event)" style="display:flex;flex-direction:column;gap:8px;max-width:320px;margin:0 auto"><input id="reqName" value="'+q+'" placeholder="Business Name" required style="padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;color:#fff;font-size:.88rem"><input id="reqPhone" placeholder="WhatsApp Number" required style="padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;color:#fff;font-size:.88rem"><input id="reqCity" placeholder="City / Area" required style="padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;color:#fff;font-size:.88rem"><button type="submit" style="background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;padding:12px;border:none;border-radius:10px;font-weight:700;cursor:pointer">Request Free Website</button></form></div>';}}
async function submitReq(e){e.preventDefault();const name=document.getElementById('reqName').value;const phone=document.getElementById('reqPhone').value;const city=document.getElementById('reqCity').value;try{await fetch('/api/website-requests',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({business_name:name,phone:phone,city:city})});document.getElementById('searchResult').innerHTML='<div style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:12px;padding:14px;text-align:center;margin-top:12px"><p style="font-weight:700;color:#10b981">&#10004; Request submitted!</p><p style="font-size:.82rem;color:#64748b;margin-top:4px">We will create your website and notify you within 24 hours.</p></div>';}catch(err){alert('Failed. Please try again.');}}
</script>
<script src="https://unpkg.com/aos@2.3.4/dist/aos.js"></script>
<script>AOS.init({duration:600,once:true,offset:50});window.addEventListener('scroll',()=>{document.getElementById('nav').classList.toggle('solid',scrollY>50)});</script>
</body></html>"""
    return HTMLResponse(content=html)



static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "videos")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static/videos", StaticFiles(directory=static_dir), name="videos")





@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}
