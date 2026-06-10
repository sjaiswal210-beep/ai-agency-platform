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
    """City Maps - Premium Digital Infrastructure Platform."""
    db = get_supabase()
    try:
        sites = db.table("websites").select("slug", count="exact").not_.is_("slug", "null").execute()
        count = sites.count or 0
    except Exception:
        count = 0
    
    # Get some live business examples
    examples = []
    try:
        result = db.table("websites").select("slug").not_.is_("slug", "null").limit(4).execute()
        if result.data:
            for s in result.data:
                if s.get("slug"):
                    examples.append(s["slug"])
    except Exception:
        pass
    
    examples_html = ""
    for slug in examples[:4]:
        name = slug.replace("-", " ").title()
        examples_html += f'<a href="https://{slug}.city-maps.online" target="_blank" style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:14px 18px;display:flex;align-items:center;justify-content:space-between;transition:all .2s;text-decoration:none;color:#e2e8f0"><span style="font-weight:600;font-size:.85rem">{name}</span><span style="font-size:.75rem;color:#64748b">{slug}.city-maps.online &rarr;</span></a>'

    html = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Digital Infrastructure for Local Businesses</title>
<meta name="description" content="Every business deserves a digital address. Professional business profiles, websites, product catalogues, and customer engagement tools.">
<meta name="theme-color" content="#0a0a14">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<link href="https://unpkg.com/aos@2.3.4/dist/aos.css" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Inter,sans-serif;background:#0a0a14;color:#e2e8f0;overflow-x:hidden}}a{{text-decoration:none;color:inherit}}

.nav{{max-width:1100px;margin:0 auto;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;position:relative;z-index:10}}.nav-logo{{font-weight:900;font-size:1rem;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.nav-links{{display:flex;gap:20px;font-size:.8rem;color:#64748b}}.nav-links a:hover{{color:#e2e8f0}}.nav-btn{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);color:#fff;padding:8px 16px;border-radius:8px;font-size:.78rem;font-weight:600}}

.hero{{max-width:1100px;margin:0 auto;padding:80px 24px 60px;text-align:center;position:relative}}.hero-glow{{position:absolute;top:-100px;left:50%;transform:translateX(-50%);width:700px;height:500px;background:radial-gradient(ellipse,rgba(96,165,250,.08),rgba(167,139,250,.04),transparent 70%);filter:blur(40px);pointer-events:none}}
.hero .chip{{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);padding:6px 14px;border-radius:20px;font-size:.72rem;color:#94a3b8;margin-bottom:22px}}.hero .chip .dot{{width:6px;height:6px;border-radius:50%;background:#22c55e;box-shadow:0 0 6px #22c55e}}
.hero h1{{font-size:clamp(2.2rem,5.5vw,3.8rem);font-weight:900;line-height:1.08;margin-bottom:18px;letter-spacing:-.04em}}.hero h1 em{{font-style:normal;background:linear-gradient(135deg,#60a5fa,#a78bfa,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero p{{font-size:1rem;color:#7c8594;line-height:1.7;max-width:560px;margin:0 auto 28px}}
.hero-btns{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}}.btn{{padding:12px 22px;border-radius:10px;font-weight:700;font-size:.85rem;transition:all .2s}}.btn-glow{{background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;box-shadow:0 4px 20px rgba(59,130,246,.25)}}.btn-glow:hover{{transform:translateY(-2px);box-shadow:0 8px 28px rgba(59,130,246,.35)}}.btn-ghost{{border:1px solid rgba(255,255,255,.12);color:#e2e8f0}}.btn-ghost:hover{{background:rgba(255,255,255,.05)}}
.hero-search{{max-width:440px;margin:24px auto 0;display:flex;gap:6px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:4px}}.hero-search input{{flex:1;background:transparent;border:none;padding:11px 14px;color:#fff;font-size:.85rem;outline:none;font-family:inherit}}.hero-search input::placeholder{{color:#4b5563}}.hero-search button{{background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;border:none;padding:10px 16px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer}}
#searchResult{{max-width:440px;margin:8px auto 0}}
.hero-img{{margin-top:36px}}.hero-img img{{width:100%;max-width:700px;border-radius:14px;border:1px solid rgba(255,255,255,.08);box-shadow:0 20px 60px rgba(0,0,0,.5);transition:transform .3s}}

.trust{{padding:28px 24px;border-top:1px solid rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.04);text-align:center}}.trust p{{font-size:.7rem;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px}}.trust-nums{{display:flex;justify-content:center;gap:32px;flex-wrap:wrap}}.trust-num .n{{font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.trust-num .l{{font-size:.68rem;color:#4b5563;margin-top:2px}}

.sec{{max-width:900px;margin:0 auto;padding:80px 24px}}.sec-line{{height:1px;background:linear-gradient(90deg,transparent,rgba(96,165,250,.15),transparent);margin-bottom:48px}}.sec-label{{font-size:.68rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:#60a5fa;margin-bottom:8px}}.sec-title{{font-size:clamp(1.5rem,3.5vw,2.2rem);font-weight:800;margin-bottom:10px;letter-spacing:-.02em}}.sec-desc{{color:#64748b;font-size:.9rem;margin-bottom:32px;max-width:500px}}

.problem-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}.problem-card{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:16px;transition:all .2s}}.problem-card:hover{{border-color:rgba(96,165,250,.2);background:rgba(96,165,250,.03)}}.problem-card .ic{{font-size:1.3rem;margin-bottom:8px}}.problem-card h3{{font-size:.8rem;font-weight:600;color:#cbd5e1}}

.features-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.f-card{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:20px;transition:all .25s;position:relative;overflow:hidden}}.f-card:hover{{border-color:rgba(96,165,250,.2);transform:translateY(-3px)}}.f-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#3b82f6,#8b5cf6);opacity:0;transition:opacity .2s}}.f-card:hover::before{{opacity:1}}.f-card .emoji{{font-size:1.3rem;margin-bottom:10px}}.f-card h3{{font-size:.82rem;font-weight:700;margin-bottom:4px;color:#e2e8f0}}.f-card p{{font-size:.72rem;color:#64748b;line-height:1.5}}

.examples-grid{{display:flex;flex-direction:column;gap:8px}}

.steps{{display:flex;gap:16px;flex-wrap:wrap}}.step{{flex:1;min-width:140px;text-align:center;padding:16px 10px}}.step .num{{width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.72rem;margin:0 auto 10px}}.step h3{{font-size:.78rem;font-weight:700;color:#e2e8f0;margin-bottom:3px}}.step p{{font-size:.68rem;color:#64748b}}

.pricing-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.plan{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:24px;position:relative}}.plan.pop{{border-color:rgba(96,165,250,.3);background:rgba(59,130,246,.03)}}.plan.pop::after{{content:'POPULAR';position:absolute;top:10px;right:10px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;font-size:.58rem;padding:3px 8px;border-radius:4px;font-weight:700}}.plan h3{{font-size:.78rem;color:#64748b;margin-bottom:4px}}.plan .price{{font-size:2rem;font-weight:900;background:linear-gradient(135deg,#e2e8f0,#94a3b8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.plan .price small{{font-size:.8rem}}.plan ul{{list-style:none;margin:14px 0 18px}}.plan li{{font-size:.76rem;color:#94a3b8;padding:4px 0;padding-left:16px;position:relative}}.plan li::before{{content:'\27A4';position:absolute;left:0;color:#60a5fa;font-size:.65rem}}.plan-btn{{display:block;text-align:center;padding:10px;border-radius:8px;font-weight:700;font-size:.8rem}}.plan-btn.fill{{background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff}}.plan-btn.outline{{border:1px solid rgba(255,255,255,.12);color:#e2e8f0}}

.cta-sec{{text-align:center;padding:80px 24px;position:relative}}.cta-glow{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:500px;height:250px;background:radial-gradient(ellipse,rgba(59,130,246,.08),transparent 60%);pointer-events:none}}
.footer{{text-align:center;padding:28px 24px;border-top:1px solid rgba(255,255,255,.04);font-size:.72rem;color:#4b5563}}.footer b{{background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
@media(max-width:640px){{.features-grid{{grid-template-columns:1fr}}.pricing-grid{{grid-template-columns:1fr}}.steps{{flex-direction:column}}.nav-links{{display:none}}.trust-nums{{gap:16px}}}}
</style></head><body>
<nav class="nav"><div class="nav-logo">City Maps</div><div class="nav-links"><a href="#features">Platform</a><a href="#pricing">Pricing</a><a href="#examples">Examples</a></div><a href="https://ai-agency-platform-blush.vercel.app" class="nav-btn">Admin</a></nav>

<section class="hero"><div class="hero-glow"></div>
<div class="chip" data-aos="fade-down"><span class="dot"></span>{count}+ businesses connected</div>
<h1 data-aos="fade-up">Every Business Deserves<br><em>A Digital Address</em></h1>
<p data-aos="fade-up">Create a professional online presence with your own business page, product catalogue, customer contact options, and digital visibility — all from one platform.</p>
<div class="hero-btns" data-aos="fade-up"><a href="#pricing" class="btn btn-glow">Create My Business Page</a><a href="#examples" class="btn btn-ghost">View Examples</a></div>
<div class="hero-search" data-aos="fade-up"><input id="bizSearch" placeholder="Search your business..."><button onclick="searchBiz()">Search</button></div>
<div id="searchResult"></div>
<div class="hero-img" data-aos="fade-up"><img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=400&fit=crop" alt="Platform"></div>
</section>

<div class="trust" data-aos="fade-up"><p>Trusted by growing businesses</p><div class="trust-nums"><div class="trust-num"><div class="n">{count}+</div><div class="l">Businesses</div></div><div class="trust-num"><div class="n">1000+</div><div class="l">Products</div></div><div class="trust-num"><div class="n">5000+</div><div class="l">Monthly Visitors</div></div><div class="trust-num"><div class="n">20+</div><div class="l">Cities</div></div></div></div>

<section class="sec" id="problem"><div class="sec-line"></div><div class="sec-label" data-aos="fade-up">The Problem</div><div class="sec-title" data-aos="fade-up">Most Businesses Are Still Invisible Online</div>
<div class="problem-grid"><div class="problem-card" data-aos="fade-up"><div class="ic">&#128683;</div><h3>No Website</h3></div><div class="problem-card" data-aos="fade-up"><div class="ic">&#128270;</div><h3>No Discoverability</h3></div><div class="problem-card" data-aos="fade-up"><div class="ic">&#128722;</div><h3>No Product Catalog</h3></div><div class="problem-card" data-aos="fade-up"><div class="ic">&#128242;</div><h3>No Digital Presence</h3></div><div class="problem-card" data-aos="fade-up"><div class="ic">&#128101;</div><h3>Missed Customers</h3></div><div class="problem-card" data-aos="fade-up"><div class="ic">&#128263;</div><h3>Word of Mouth Only</h3></div></div></section>

<section class="sec" id="features"><div class="sec-line"></div><div class="sec-label" data-aos="fade-up">Platform</div><div class="sec-title" data-aos="fade-up">Everything For A Professional Online Presence</div>
<div class="features-grid"><div class="f-card" data-aos="fade-up"><div class="emoji">&#127760;</div><h3>Business Website</h3><p>Professional mobile-ready site with your services, photos, and location</p></div><div class="f-card" data-aos="fade-up"><div class="emoji">&#128722;</div><h3>Product Catalogue</h3><p>Showcase products with prices. Customers order via WhatsApp</p></div><div class="f-card" data-aos="fade-up"><div class="emoji">&#128172;</div><h3>WhatsApp Integration</h3><p>One-tap messaging. Pre-filled orders. Instant connection</p></div><div class="f-card" data-aos="fade-up"><div class="emoji">&#128200;</div><h3>Business Dashboard</h3><p>Track visitors, calls, messages. See what works</p></div><div class="f-card" data-aos="fade-up"><div class="emoji">&#128205;</div><h3>Google Visibility</h3><p>Show up when customers search for businesses like yours</p></div><div class="f-card" data-aos="fade-up"><div class="emoji">&#128247;</div><h3>Social Content</h3><p>Download-ready posts for Instagram and WhatsApp status</p></div></div></section>

<section class="sec" id="examples"><div class="sec-line"></div><div class="sec-label" data-aos="fade-up">Live Examples</div><div class="sec-title" data-aos="fade-up">Businesses Already Online</div><div class="sec-desc" data-aos="fade-up">Real businesses using City Maps right now</div>
<div class="examples-grid" data-aos="fade-up">{examples_html}</div></section>

<section class="sec"><div class="sec-line"></div><div class="sec-label" data-aos="fade-up">Process</div><div class="sec-title" data-aos="fade-up">Live In 5 Minutes</div>
<div class="steps"><div class="step" data-aos="fade-up"><div class="num">1</div><h3>Create Profile</h3><p>Add business name & category</p></div><div class="step" data-aos="fade-up"><div class="num">2</div><h3>Add Details</h3><p>Services, products, photos</p></div><div class="step" data-aos="fade-up"><div class="num">3</div><h3>Publish</h3><p>Your site goes live instantly</p></div><div class="step" data-aos="fade-up"><div class="num">4</div><h3>Grow</h3><p>Receive enquiries & orders</p></div></div></section>

<section class="sec"><div class="sec-line"></div><div class="sec-label" data-aos="fade-up">Why Us</div><div class="sec-title" data-aos="fade-up">Traditional Agency vs City Maps</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:24px" data-aos="fade-up">
<div style="background:rgba(239,68,68,.04);border:1px solid rgba(239,68,68,.12);border-radius:12px;padding:18px"><h3 style="font-size:.82rem;font-weight:700;color:#ef4444;margin-bottom:10px">Traditional Agency</h3><div style="font-size:.75rem;color:#94a3b8;line-height:2">&#10060; Rs.15,000 - 50,000 cost<br>&#10060; 2-4 weeks delivery<br>&#10060; Complex process<br>&#10060; Monthly maintenance fees<br>&#10060; Agency dependent</div></div>
<div style="background:rgba(59,130,246,.04);border:1px solid rgba(59,130,246,.12);border-radius:12px;padding:18px"><h3 style="font-size:.82rem;font-weight:700;color:#60a5fa;margin-bottom:10px">City Maps</h3><div style="font-size:.75rem;color:#94a3b8;line-height:2">&#10004; Rs.49 - 69/month<br>&#10004; Ready in 5 minutes<br>&#10004; Simple self-service<br>&#10004; No hidden costs<br>&#10004; You own everything</div></div>
</div></section>

<section class="sec" id="pricing"><div class="sec-line"></div><div class="sec-label" data-aos="fade-up">Pricing</div><div class="sec-title" data-aos="fade-up">Simple. Transparent. No Surprises.</div>
<div class="pricing-grid" data-aos="fade-up"><div class="plan"><h3>Starter</h3><div class="price">&#8377;49<small>/mo</small></div><ul><li>Business Profile</li><li>Website</li><li>Contact Details</li><li>WhatsApp Button</li><li>Product Listings</li><li>Mobile Design</li></ul><a href="https://wa.me/917350785606?text=Hi%2C%20I%20want%20Starter%20plan" class="plan-btn outline">Get Started</a></div><div class="plan pop"><h3>Business</h3><div class="price">&#8377;69<small>/mo</small></div><ul><li>Everything in Starter</li><li>Business Dashboard</li><li>Visitor Analytics</li><li>Social Content</li><li>Product Catalogue</li><li>Lead Management</li><li>Premium Placement</li><li>Growth Tools</li></ul><a href="https://wa.me/917350785606?text=Hi%2C%20I%20want%20Business%20plan" class="plan-btn fill">Get Started</a></div></div></section>

<section class="sec"><div class="sec-line"></div><div class="sec-label" data-aos="fade-up">Testimonials</div><div class="sec-title" data-aos="fade-up">What Business Owners Say</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:24px">
<div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:18px" data-aos="fade-up"><p style="font-size:.8rem;color:#94a3b8;line-height:1.6;margin-bottom:12px;font-style:italic">"Customers now find us on Google. Our calls increased within the first week."</p><div style="font-size:.75rem"><strong style="color:#e2e8f0">Rahul S.</strong><br><span style="color:#4b5563">Restaurant Owner, Pune</span></div></div>
<div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:18px" data-aos="fade-up"><p style="font-size:.8rem;color:#94a3b8;line-height:1.6;margin-bottom:12px;font-style:italic">"Professional website at a price I can afford. WhatsApp orders come directly now."</p><div style="font-size:.75rem"><strong style="color:#e2e8f0">Priya M.</strong><br><span style="color:#4b5563">Boutique Owner, Mumbai</span></div></div>
<div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:18px" data-aos="fade-up"><p style="font-size:.8rem;color:#94a3b8;line-height:1.6;margin-bottom:12px;font-style:italic">"No technical knowledge needed. Everything was ready in minutes. Best investment."</p><div style="font-size:.75rem"><strong style="color:#e2e8f0">Amit K.</strong><br><span style="color:#4b5563">Salon Owner, Bangalore</span></div></div>
</div></section>

<section class="cta-sec"><div class="cta-glow"></div><h2 style="font-size:1.6rem;font-weight:800;margin-bottom:8px;position:relative" data-aos="fade-up">Start Building Your Digital Presence</h2><p style="color:#64748b;margin-bottom:20px;position:relative" data-aos="fade-up">Join {count}+ businesses on City Maps</p><a href="https://wa.me/917350785606?text=Hi%20City%20Maps%2C%20I%20want%20to%20create%20my%20business%20page" class="btn btn-glow" style="position:relative" data-aos="fade-up">Create My Business Page &rarr;</a></section>

<footer class="footer"><b>City Maps</b> &bull; Digital Infrastructure for Local Businesses &bull; Powered by Kalpdev Digitals</footer>

<script>
async function searchBiz(){{const q=document.getElementById("bizSearch").value.trim();if(!q)return;const r=document.getElementById("searchResult");r.style.display="block";r.innerHTML="<p style=\"text-align:center;color:#64748b;font-size:.8rem\">Searching...</p>";try{{const slug=q.toLowerCase().replace(/[^a-z0-9\s-]/g,"").replace(/[\s]+/g,"-");const resp=await fetch("/api/preview/by-slug/"+slug);if(resp.ok){{r.innerHTML="<div style=\"background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);border-radius:10px;padding:10px;text-align:center;margin-top:6px\"><p style=\"font-weight:700;color:#22c55e;font-size:.82rem\">Found!</p><a href=\"https://"+slug+".city-maps.online\" target=\"_blank\" style=\"color:#60a5fa;font-size:.78rem\">Visit &rarr;</a></div>";}}else{{throw new Error("nf");}}}}catch{{r.innerHTML="<div style=\"background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:14px;margin-top:6px;text-align:center\"><p style=\"font-size:.82rem;margin-bottom:8px\">Not found</p><form onsubmit=\"submitReq(event)\" style=\"display:flex;flex-direction:column;gap:5px;max-width:260px;margin:0 auto\"><input id=\"reqName\" value=\""+q+"\" required style=\"padding:8px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:6px;color:#fff;font-size:.8rem\"><input id=\"reqPhone\" placeholder=\"WhatsApp\" required style=\"padding:8px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:6px;color:#fff;font-size:.8rem\"><input id=\"reqCity\" placeholder=\"City\" required style=\"padding:8px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:6px;color:#fff;font-size:.8rem\"><button type=\"submit\" style=\"background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;padding:9px;border:none;border-radius:6px;font-weight:700;font-size:.78rem;cursor:pointer\">Request Page</button></form></div>";}}}}
async function submitReq(e){{e.preventDefault();try{{await fetch("/api/website-requests",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{business_name:document.getElementById("reqName").value,phone:document.getElementById("reqPhone").value,city:document.getElementById("reqCity").value}})}});document.getElementById("searchResult").innerHTML="<div style=\"background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);border-radius:10px;padding:10px;text-align:center;margin-top:6px\"><p style=\"font-weight:700;color:#22c55e;font-size:.82rem\">Submitted! We will notify you soon.</p></div>";}}catch{{alert("Failed");}}}}
</script>
<script src="https://unpkg.com/aos@2.3.4/dist/aos.js"></script>
<script>AOS.init({{duration:500,once:true,offset:30}});</script>
</body></html>'''
    return HTMLResponse(content=html)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}
