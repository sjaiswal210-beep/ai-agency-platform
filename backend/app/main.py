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


@app.get("/", response_class=HTMLResponse)
def landing_page():
    """City Maps - Premium Digital Presence Platform."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        sites = db.table("websites").select("slug", count="exact").not_.is_("slug", "null").execute()
        count = sites.count or 0
    except Exception:
        count = 0
    
    # Get live examples
    examples_html = ""
    try:
        result = db.table("websites").select("slug").not_.is_("slug", "null").order("created_at", desc=True).limit(6).execute()
        cats = ["Restaurant", "Salon", "Gym", "Clinic", "Hotel", "Store"]
        for i, s in enumerate((result.data or [])[:6]):
            slug = s.get("slug", "")
            name = slug.replace("-", " ").title()[:20]
            cat = cats[i] if i < len(cats) else "Business"
            examples_html += f'<a href="https://{slug}.city-maps.online" target="_blank" class="demo-card"><div class="demo-cat">{cat}</div><div class="demo-name">{name}</div><div class="demo-url">{slug}.city-maps.online</div></a>'
    except Exception:
        pass

    html = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Digital Presence Platform for Local Businesses</title>
<meta name="description" content="Take your business online in 5 minutes. Professional website, WhatsApp orders, Google visibility, customer growth tools.">
<meta name="theme-color" content="#050816">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Inter,sans-serif;background:#050816;color:#fff;overflow-x:hidden;position:relative}}a{{text-decoration:none;color:inherit}}
.wrap{{max-width:1100px;margin:0 auto;padding:0 20px}}

/* NAV */
.nav{{padding:14px 20px;display:flex;align-items:center;justify-content:space-between;max-width:1100px;margin:0 auto;position:relative;z-index:10}}.nav-logo{{font-weight:900;font-size:1.05rem;background:linear-gradient(135deg,#00e5ff,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.nav-btn{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);color:#fff;padding:7px 14px;border-radius:8px;font-size:.72rem;font-weight:600}}

/* HERO */
.hero{{min-height:90vh;display:flex;align-items:center;position:relative;padding:80px 20px 60px;overflow:hidden;z-index:1}}
.hero-bg{{position:absolute;inset:0;background-image:linear-gradient(rgba(0,229,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,255,.03) 1px,transparent 1px);background-size:50px 50px;animation:gridMove 20s linear infinite}}@keyframes gridMove{{to{{transform:translateY(50px)}}}}
.hero-glow{{position:absolute;top:-100px;left:50%;transform:translateX(-50%);width:700px;height:500px;background:radial-gradient(ellipse,rgba(0,229,255,.08),rgba(124,58,237,.05),transparent 65%);filter:blur(60px);animation:breathe 8s ease-in-out infinite}}@keyframes breathe{{0%,100%{{opacity:.7;transform:translateX(-50%) scale(1)}}50%{{opacity:1;transform:translateX(-50%) scale(1.08)}}}}
.hero-inner{{position:relative;z-index:2;max-width:650px;margin:0 auto;text-align:center}}
.hero-badge{{display:inline-flex;align-items:center;gap:6px;background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.2);padding:6px 14px;border-radius:20px;font-size:.7rem;color:#00e5ff;margin-bottom:20px}}.hero-badge .dot{{width:6px;height:6px;border-radius:50%;background:#22c55e;box-shadow:0 0 6px #22c55e}}
.hero h1{{font-size:clamp(2rem,5.5vw,3.4rem);font-weight:900;line-height:1.1;margin-bottom:16px;letter-spacing:-.03em}}
.hero p{{font-size:.95rem;color:#94a3b8;line-height:1.7;margin-bottom:26px;max-width:520px;margin-left:auto;margin-right:auto}}
.hero-btns{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}}.btn{{padding:12px 22px;border-radius:10px;font-weight:700;font-size:.85rem;transition:all .2s}}.btn-cyan{{background:linear-gradient(135deg,#00e5ff,#00b4d8);color:#050816;box-shadow:0 4px 20px rgba(0,229,255,.2)}}.btn-cyan:hover{{transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,229,255,.3)}}.btn-ghost{{border:1px solid rgba(255,255,255,.15);color:#e2e8f0}}.btn-ghost:hover{{background:rgba(255,255,255,.05)}}
.hero-search{{max-width:420px;margin:22px auto 0;display:flex;gap:5px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:4px}}.hero-search input{{flex:1;background:transparent;border:none;padding:10px 12px;color:#fff;font-size:.82rem;outline:none}}.hero-search input::placeholder{{color:#4b5563}}.hero-search button{{background:linear-gradient(135deg,#00e5ff,#00b4d8);color:#050816;border:none;padding:10px 16px;border-radius:7px;font-weight:700;font-size:.75rem;cursor:pointer}}
#searchResult{{max-width:420px;margin:6px auto 0}}

/* STATS */
.stats{{display:flex;justify-content:center;gap:28px;padding:28px 20px;border-top:1px solid rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.04);flex-wrap:wrap}}.stat .n{{font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,#00e5ff,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.stat .l{{font-size:.65rem;color:#4b5563;margin-top:2px}}

/* SECTIONS */
.sec{{padding:70px 20px;max-width:900px;margin:0 auto;position:relative}}.sec::before{{content:'';position:absolute;top:0;left:10%;right:10%;height:1px;background:linear-gradient(90deg,transparent,rgba(0,229,255,.12),transparent)}}.sec-label{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#00e5ff;margin-bottom:6px}}.sec-title{{font-size:clamp(1.4rem,3.5vw,2rem);font-weight:800;margin-bottom:8px;letter-spacing:-.02em}}.sec-desc{{color:#64748b;font-size:.88rem;margin-bottom:28px}}

/* FEATURES */
.f-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}.f-card{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:20px;transition:all .25s;position:relative;overflow:hidden}}.f-card:hover{{border-color:rgba(0,229,255,.2);transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,229,255,.05)}}.f-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#00e5ff,#7c3aed);opacity:0;transition:opacity .2s}}.f-card:hover::before{{opacity:1}}.f-card .ic{{font-size:1.3rem;margin-bottom:10px}}.f-card h3{{font-size:.82rem;font-weight:700;margin-bottom:4px}}.f-card p{{font-size:.72rem;color:#64748b;line-height:1.5}}

/* DEMOS */
.demo-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.demo-card{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:16px;transition:all .2s;display:block}}.demo-card:hover{{border-color:rgba(0,229,255,.25);transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,229,255,.06)}}.demo-cat{{font-size:.65rem;color:#00e5ff;font-weight:600;margin-bottom:4px}}.demo-name{{font-size:.85rem;font-weight:700;margin-bottom:3px}}.demo-url{{font-size:.68rem;color:#4b5563}}
.showcase-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}.showcase-card{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:14px;overflow:hidden;transition:all .3s;position:relative}}.showcase-card:hover{{border-color:rgba(0,229,255,.3);transform:translateY(-4px) scale(1.01);box-shadow:0 12px 35px rgba(0,229,255,.08)}}.showcase-card::before{{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#00e5ff,#7c3aed);opacity:0;transition:opacity .3s}}.showcase-card:hover::before{{opacity:1}}.showcase-img{{position:relative;height:140px;overflow:hidden}}.showcase-img img{{width:100%;height:100%;object-fit:cover;transition:transform .4s;filter:brightness(0.8)}}.showcase-card:hover .showcase-img img{{transform:scale(1.08);filter:brightness(1)}}.showcase-img::after{{content:"";position:absolute;bottom:0;left:0;right:0;height:40px;background:linear-gradient(transparent,rgba(5,8,22,.8))}}.showcase-info{{padding:14px 16px}}.showcase-info h3{{font-size:.82rem;font-weight:700;margin-bottom:5px}}.showcase-info p{{font-size:.72rem;color:#94a3b8;line-height:1.6}}@keyframes orb1{{0%,100%{{transform:translate(0,0) scale(1)}}50%{{transform:translate(30px,-40px) scale(1.15)}}}}@keyframes orb2{{0%,100%{{transform:translate(0,0) scale(1)}}50%{{transform:translate(-25px,35px) scale(1.1)}}}}@keyframes orb3{{0%,100%{{transform:translate(0,0) scale(1)}}33%{{transform:translate(20px,20px) scale(1.08)}}66%{{transform:translate(-15px,-25px) scale(.95)}}}}@keyframes orb4{{0%,100%{{transform:translate(0,0) scale(1)}}50%{{transform:translate(35px,-20px) scale(1.12)}}}}
@media(max-width:640px){{.showcase-grid{{grid-template-columns:1fr}}}}

/* BEFORE/AFTER */
.ba-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.ba-card{{border-radius:12px;padding:18px}}.ba-bad{{background:rgba(239,68,68,.04);border:1px solid rgba(239,68,68,.15)}}.ba-good{{background:rgba(0,229,255,.04);border:1px solid rgba(0,229,255,.15)}}.ba-card h3{{font-size:.8rem;font-weight:700;margin-bottom:10px}}.ba-card li{{font-size:.75rem;color:#94a3b8;padding:3px 0;list-style:none}}

/* PRICING */
.p-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.p-card{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:20px;text-align:center;transition:all .25s;cursor:pointer}}.p-card:active{{transform:scale(.97)}}.p-card:hover{{border-color:rgba(0,229,255,.3);transform:translateY(-4px);box-shadow:0 12px 30px rgba(0,229,255,.08)}}.p-card.pop{{border-color:rgba(124,58,237,.4);box-shadow:0 0 20px rgba(124,58,237,.08)}}.p-card h3{{font-size:.75rem;color:#64748b;margin-bottom:4px}}.p-card .price{{font-size:1.8rem;font-weight:900;margin-bottom:2px}}.p-card .price small{{font-size:.7rem;color:#64748b}}.p-card ul{{list-style:none;text-align:left;margin:12px 0}}.p-card li{{font-size:.72rem;color:#94a3b8;padding:4px 0;padding-left:16px;position:relative;line-height:1.5}}.p-card li::before{{content:'';position:absolute;left:0;top:7px;width:6px;height:6px;border-radius:50%;background:#00e5ff}}.p-btn{{display:block;padding:9px;border-radius:8px;font-weight:700;font-size:.78rem;margin-top:12px}}.p-btn.fill{{background:linear-gradient(135deg,#00e5ff,#7c3aed);color:#fff;box-shadow:0 4px 14px rgba(0,229,255,.2)}}.p-btn.fill:hover{{box-shadow:0 6px 20px rgba(0,229,255,.3);transform:translateY(-1px)}}.p-btn.ghost{{border:1.5px solid rgba(0,229,255,.4);color:#00e5ff}}.p-btn.ghost:hover{{background:rgba(0,229,255,.08)}}

/* CTA */
.cta-sec{{text-align:center;padding:70px 20px;position:relative}}.cta-glow{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:400px;height:200px;background:radial-gradient(ellipse,rgba(0,229,255,.06),transparent 60%);pointer-events:none}}
.wa-float{{position:fixed;bottom:20px;right:20px;width:50px;height:50px;border-radius:50%;background:#25D366;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(37,211,102,.35);z-index:99;animation:wab 3s ease-in-out infinite}}@keyframes wab{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-4px)}}}}
.footer{{text-align:center;padding:24px;font-size:.7rem;color:#374151;border-top:1px solid rgba(255,255,255,.04)}}.footer b{{color:#00e5ff}}
@keyframes orb1{{0%,100%{{transform:translate(0,0) scale(1)}}50%{{transform:translate(30px,-40px) scale(1.15)}}}}@keyframes orb2{{0%,100%{{transform:translate(0,0) scale(1)}}50%{{transform:translate(-25px,35px) scale(1.1)}}}}@keyframes orb3{{0%,100%{{transform:translate(0,0) scale(1)}}33%{{transform:translate(20px,20px) scale(1.08)}}66%{{transform:translate(-15px,-25px) scale(.95)}}}}@keyframes orb4{{0%,100%{{transform:translate(0,0) scale(1)}}50%{{transform:translate(35px,-20px) scale(1.12)}}}}
@media(max-width:640px){{.f-grid,.ba-grid{{grid-template-columns:1fr}}.p-grid{{grid-template-columns:1fr}}.demo-grid{{grid-template-columns:1fr}}.stats{{gap:14px}}}}
</style></head><body>
<div style="position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none"><div style="position:absolute;top:-20%;left:-10%;width:60%;height:60%;background:radial-gradient(ellipse,rgba(0,229,255,.15),transparent 60%);filter:blur(80px);animation:orb1 18s ease-in-out infinite"></div><div style="position:absolute;bottom:-20%;right:-10%;width:55%;height:55%;background:radial-gradient(ellipse,rgba(124,58,237,.18),transparent 60%);filter:blur(80px);animation:orb2 15s ease-in-out infinite"></div><div style="position:absolute;top:30%;left:40%;width:45%;height:45%;background:radial-gradient(ellipse,rgba(236,72,153,.1),transparent 55%);filter:blur(90px);animation:orb3 20s ease-in-out infinite"></div><div style="position:absolute;top:60%;left:10%;width:40%;height:40%;background:radial-gradient(ellipse,rgba(6,182,212,.12),transparent 55%);filter:blur(70px);animation:orb4 16s ease-in-out infinite"></div></div>
<nav class="nav"><div class="nav-logo">City Maps</div><a href="https://ai-agency-platform-blush.vercel.app" class="nav-btn">Admin</a></nav>

<section class="hero"><div class="hero-bg"></div><div class="hero-glow"></div>
<div class="hero-inner">
<div class="hero-badge"><span class="dot"></span>{count}+ businesses online</div>
<h1>Take Your Business Online At Just &#8377;49</h1>
<p>Professional website, WhatsApp orders, Google visibility, customer tools and business growth &mdash; everything from one platform.</p>
<div class="hero-btns"><a href="#pricing" class="btn btn-cyan">Create My Website</a><a href="#features-showcase" class="btn btn-ghost">&#10024; What You Get</a></div>
<div class="hero-search"><input id="bizSearch" placeholder="Search your business..."><button onclick="searchBiz()">Search</button></div>
<div id="searchResult"></div>
</div>
</section>

<div class="stats"><div class="stat"><div class="n">{count}+</div><div class="l">Businesses Online</div></div><div class="stat"><div class="n">10,000+</div><div class="l">Customer Leads</div></div><div class="stat"><div class="n">95%</div><div class="l">Mobile Traffic</div></div><div class="stat"><div class="n">5 min</div><div class="l">Setup Time</div></div></div>

<section class="sec"><div class="sec-label">Platform</div><div class="sec-title">Everything For Your Digital Presence</div><div class="sec-desc">More than a website. A complete business growth system.</div>
<div class="f-grid"><div class="f-card"><div class="ic">&#127760;</div><h3>Business Website</h3><p>Professional responsive site with services, gallery, location</p></div><div class="f-card"><div class="ic">&#128172;</div><h3>WhatsApp Commerce</h3><p>Accept orders and enquiries directly on WhatsApp</p></div><div class="f-card"><div class="ic">&#128205;</div><h3>Google Visibility</h3><p>Show up when customers search for your business</p></div><div class="f-card"><div class="ic">&#128722;</div><h3>Product Showcase</h3><p>Beautiful catalog with prices and Buy Now</p></div><div class="f-card"><div class="ic">&#128200;</div><h3>Analytics Dashboard</h3><p>Track visitors, calls, messages in real-time</p></div><div class="f-card"><div class="ic">&#128241;</div><h3>Mobile First</h3><p>Optimized for every device your customers use</p></div></div></section>

<section class="sec" id="features-showcase"><div class="sec-label">What You Get</div><div class="sec-title">Everything Included In Your Package</div><div class="sec-desc">See exactly what your business gets â€” professional design, powerful tools, real results.</div><div class="showcase-grid"><div class="showcase-card"><div class="showcase-img"><img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=250&fit=crop" alt="Professional Website" loading="lazy"></div><div class="showcase-info"><h3>&#127760; Professional Website</h3><p>Beautiful responsive design with your brand colors, services, gallery, location map, and contact info.</p></div></div><div class="showcase-card"><div class="showcase-img"><img src="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=250&fit=crop" alt="Product Catalog" loading="lazy"></div><div class="showcase-info"><h3>&#128722; Product Catalog &amp; Orders</h3><p>Showcase products with prices, images, and Buy Now button. Customers order directly via WhatsApp.</p></div></div><div class="showcase-card"><div class="showcase-img"><img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=250&fit=crop" alt="Analytics Dashboard" loading="lazy"></div><div class="showcase-info"><h3>&#128200; Real-Time Analytics</h3><p>Track visitors, calls, WhatsApp clicks in real-time. Beautiful dashboard you can check anytime.</p></div></div><div class="showcase-card"><div class="showcase-img"><img src="https://images.unsplash.com/photo-1611606063065-ee7946f0787a?w=400&h=250&fit=crop" alt="WhatsApp Integration" loading="lazy"></div><div class="showcase-info"><h3>&#128172; WhatsApp Commerce</h3><p>One-tap WhatsApp button for enquiries and orders. Auto-generated messages with product details.</p></div></div><div class="showcase-card"><div class="showcase-img"><img src="https://images.unsplash.com/photo-1432888622747-4eb9a8efeb07?w=400&h=250&fit=crop" alt="Google Maps" loading="lazy"></div><div class="showcase-info"><h3>&#128205; Google Maps Presence</h3><p>Get found when people search nearby. Show up on Google Maps with all your business details.</p></div></div><div class="showcase-card"><div class="showcase-img"><img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=400&h=250&fit=crop" alt="Social Content" loading="lazy"></div><div class="showcase-info"><h3>&#128247; Social Media Content</h3><p>AI-generated daily posts, stories, and promo content ready to share on Instagram and WhatsApp.</p></div></div></div></section>

<section class="sec"><div class="sec-label">Comparison</div><div class="sec-title">Why City Maps?</div>
<div class="ba-grid"><div class="ba-card ba-bad"><h3 style="color:#ef4444">Without City Maps</h3><li>&#10060; No website</li><li>&#10060; No online orders</li><li>&#10060; No visibility</li><li>&#10060; Lost customers daily</li><li>&#10060; Only word of mouth</li></div><div class="ba-card ba-good"><h3 style="color:#00e5ff">With City Maps</h3><li>&#10004; Professional website</li><li>&#10004; WhatsApp orders</li><li>&#10004; Google presence</li><li>&#10004; Product catalog</li><li>&#10004; Customer growth</li></div></div></section>

<section class="sec" id="pricing"><div class="sec-label">Pricing</div><div class="sec-title">Simple Plans. Real Results.</div>
<div class="p-grid"><div class="p-card"><h3>Starter</h3><div class="price">&#8377;49<small>/mo</small></div><ul><li>Business Website</li><li>WhatsApp Button</li><li>Google Maps</li><li>Contact Form</li><li>Mobile Design</li></ul><a href="https://wa.me/917350785606?text=Starter%20plan%20chahiye" class="p-btn ghost">Get Started</a></div><div class="p-card pop"><h3>Growth</h3><div class="price">&#8377;99<small>/mo</small></div><ul><li>Everything in Starter</li><li>Product Catalog</li><li>Analytics Dashboard</li><li>Social Content</li><li>WhatsApp Commerce</li><li>Customer Reviews</li></ul><a href="https://wa.me/917350785606?text=Growth%20plan%20chahiye" class="p-btn fill">Get Started</a></div><div class="p-card"><h3>Premium</h3><div class="price">&#8377;199<small>/mo</small></div><ul><li>Everything in Growth</li><li>Priority Support</li><li>Custom Domain</li><li>Advanced Analytics</li><li>Multi-Location</li><li>Growth Automation</li></ul><a href="https://wa.me/917350785606?text=Premium%20plan%20chahiye" class="p-btn ghost">Get Started</a></div></div></section>

<section class="cta-sec"><div class="cta-glow"></div><h2 style="font-size:1.5rem;font-weight:900;margin-bottom:8px;position:relative">Ready To Grow Your Business Online?</h2><p style="color:#64748b;margin-bottom:18px;font-size:.88rem;position:relative">Join {count}+ businesses already growing with City Maps</p><a href="https://wa.me/917350785606?text=Hi%20City%20Maps%2C%20I%20want%20to%20create%20my%20business%20website" class="btn btn-cyan" style="position:relative">Create My Business Website &rarr;</a></section>

<a href="https://wa.me/917350785606" target="_blank" class="wa-float"><svg width="24" height="24" viewBox="0 0 24 24" fill="#fff"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492l4.625-1.476A11.929 11.929 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75c-2.115 0-4.09-.57-5.793-1.564l-.415-.248-2.74.875.876-2.672-.27-.43A9.71 9.71 0 012.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75z"/></svg></a>

<footer class="footer"><b>City Maps</b> &bull; India's Digital Presence Platform &bull; Powered by Kalpdev Digitals</footer>

<script>
async function searchBiz(){{const q=document.getElementById("bizSearch").value.trim();if(!q)return;const r=document.getElementById("searchResult");r.style.display="block";r.innerHTML="<p style=\"text-align:center;color:#64748b;font-size:.75rem\">Searching...</p>";try{{const slug=q.toLowerCase().replace(/[^a-z0-9\s-]/g,"").replace(/[\s]+/g,"-");const resp=await fetch("/api/preview/by-slug/"+slug);if(resp.ok){{r.innerHTML="<div style=\"background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.2);border-radius:8px;padding:10px;text-align:center;margin-top:6px\"><p style=\"color:#22c55e;font-size:.8rem;font-weight:600\">Found!</p><a href=\"https://"+slug+".city-maps.online\" target=\"_blank\" style=\"color:#00e5ff;font-size:.75rem\">Visit &rarr;</a></div>";}}else{{throw new Error("nf");}}}}catch{{r.innerHTML="<div style=\"background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:12px;margin-top:6px;text-align:center\"><p style=\"font-size:.8rem;margin-bottom:6px\">Not found</p><p style=\"font-size:.7rem;color:#4b5563;margin-bottom:8px\">Want a free business page?</p><form onsubmit=\"submitReq(event)\" style=\"display:flex;flex-direction:column;gap:4px;max-width:240px;margin:0 auto\"><input id=\"reqName\" value=\""+q+"\" required style=\"padding:7px 10px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:6px;color:#fff;font-size:.75rem\"><input id=\"reqPhone\" placeholder=\"WhatsApp\" required style=\"padding:7px 10px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:6px;color:#fff;font-size:.75rem\"><input id=\"reqCity\" placeholder=\"City\" required style=\"padding:7px 10px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:6px;color:#fff;font-size:.75rem\"><button type=\"submit\" style=\"background:linear-gradient(135deg,#00e5ff,#00b4d8);color:#050816;padding:8px;border:none;border-radius:6px;font-weight:700;font-size:.75rem;cursor:pointer\">Request Page</button></form></div>";}}}}
async function submitReq(e){{e.preventDefault();try{{await fetch("/api/website-requests",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{business_name:document.getElementById("reqName").value,phone:document.getElementById("reqPhone").value,city:document.getElementById("reqCity").value}})}});document.getElementById("searchResult").innerHTML="<div style=\"background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.2);border-radius:8px;padding:10px;text-align:center;margin-top:6px\"><p style=\"color:#22c55e;font-size:.8rem;font-weight:600\">Submitted! We will notify you soon.</p></div>";}}catch{{alert("Failed");}}}}
</script></body></html>'''
    return HTMLResponse(content=html)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}
