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
    """City Maps premium landing page with visuals."""
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
<meta name="description" content="Professional websites for local businesses. Get discovered online, attract customers, grow your revenue. Starting at Rs.69/month.">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<link href="https://unpkg.com/aos@2.3.4/dist/aos.css" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Plus Jakarta Sans',sans-serif;color:#0f172a;background:#fff;overflow-x:hidden}
a{text-decoration:none;color:inherit}
.container{max-width:1100px;margin:0 auto;padding:0 24px}

.nav{position:fixed;top:0;left:0;right:0;z-index:100;padding:16px 32px;display:flex;align-items:center;justify-content:space-between;transition:all .3s}
.nav.solid{background:rgba(255,255,255,.92);backdrop-filter:blur(20px);box-shadow:0 1px 0 rgba(0,0,0,.05)}
.nav-brand{font-weight:900;font-size:1.15rem;background:linear-gradient(135deg,#7c3aed,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.nav-links{display:flex;gap:24px;font-size:.88rem;font-weight:500;color:#64748b}
.nav-links a:hover{color:#7c3aed}
.nav-btn{background:#0f172a;color:#fff;padding:10px 20px;border-radius:50px;font-weight:700;font-size:.82rem}

/* HERO */
.hero{min-height:100vh;display:flex;align-items:center;position:relative;overflow:hidden;padding:100px 24px 60px}
.hero-bg{position:absolute;inset:0;background:linear-gradient(160deg,#fafafa 0%,#ede9fe 25%,#dbeafe 50%,#f0fdf4 75%,#fefce8 100%)}
.hero-mesh{position:absolute;inset:0;background-image:radial-gradient(circle at 1px 1px,rgba(99,102,241,.05) 1px,transparent 0);background-size:32px 32px}
.hero-glow{position:absolute;top:-100px;right:-100px;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,rgba(124,58,237,.12),transparent 65%);animation:glow 10s ease-in-out infinite alternate}
.hero-glow2{position:absolute;bottom:-150px;left:-50px;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(37,99,235,.1),transparent 65%);animation:glow 8s ease-in-out infinite alternate-reverse}
@keyframes glow{0%{transform:scale(1) translate(0,0)}100%{transform:scale(1.1) translate(20px,-20px)}}

.hero-inner{position:relative;z-index:2;display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center;max-width:1100px;margin:0 auto}
.hero-text .pill{display:inline-flex;align-items:center;gap:8px;background:#fff;border:1px solid #e2e8f0;padding:7px 14px;border-radius:50px;font-size:.78rem;font-weight:600;color:#64748b;box-shadow:0 2px 8px rgba(0,0,0,.03);margin-bottom:20px}
.hero-text .pill .dot{width:7px;height:7px;border-radius:50%;background:#10b981;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.hero-text h1{font-size:clamp(2.2rem,5vw,3.6rem);font-weight:900;line-height:1.08;margin-bottom:18px;letter-spacing:-.03em}
.hero-text h1 .grad{background:linear-gradient(135deg,#7c3aed,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-text p{font-size:1.05rem;color:#64748b;line-height:1.7;margin-bottom:28px;max-width:480px}
.hero-btns{display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;padding:14px 26px;border-radius:12px;font-weight:700;font-size:.92rem;transition:all .25s}
.btn-dark{background:#0f172a;color:#fff;box-shadow:0 8px 24px rgba(15,23,42,.18)}.btn-dark:hover{transform:translateY(-2px);box-shadow:0 14px 32px rgba(15,23,42,.25)}
.btn-outline{border:1.5px solid #e2e8f0;color:#0f172a;background:#fff}.btn-outline:hover{border-color:#7c3aed;color:#7c3aed}

.hero-visual{position:relative}
.hero-mockup{width:100%;border-radius:16px;box-shadow:0 40px 80px rgba(15,23,42,.15);border:1px solid rgba(255,255,255,.8)}
.hero-float{position:absolute;background:#fff;border-radius:12px;padding:12px 16px;box-shadow:0 12px 32px rgba(0,0,0,.1);font-size:.8rem;font-weight:600;animation:floaty 4s ease-in-out infinite}
.hero-float.f1{top:20%;right:-20px;animation-delay:0s}.hero-float.f2{bottom:20%;left:-20px;animation-delay:1s}
@keyframes floaty{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}

/* LOGOS */
.logos{padding:40px 24px;background:#f8fafc;border-top:1px solid #f1f5f9;border-bottom:1px solid #f1f5f9}
.logos-inner{display:flex;align-items:center;justify-content:center;gap:32px;flex-wrap:wrap;opacity:.6}
.logos-inner span{font-size:.85rem;font-weight:700;color:#94a3b8}

/* FEATURES */
.features{padding:100px 24px}
.sec-head{text-align:center;max-width:550px;margin:0 auto 52px}
.sec-head .tag{display:inline-block;background:#f0fdf4;color:#059669;font-size:.7rem;font-weight:700;padding:5px 12px;border-radius:50px;margin-bottom:12px;letter-spacing:.08em;text-transform:uppercase}
.sec-head h2{font-size:clamp(1.8rem,4vw,2.5rem);font-weight:900;margin-bottom:10px}
.sec-head p{color:#64748b;font-size:.98rem}
.f-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:1000px;margin:0 auto}
.f-card{background:#fff;border:1px solid #f1f5f9;border-radius:18px;padding:28px 24px;transition:all .35s;position:relative;overflow:hidden}
.f-card:hover{transform:translateY(-6px);box-shadow:0 20px 50px rgba(124,58,237,.08);border-color:#ede9fe}
.f-card::after{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#7c3aed,#2563eb);transform:scaleX(0);transition:transform .3s;transform-origin:left}.f-card:hover::after{transform:scaleX(1)}
.f-card .ic{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;margin-bottom:14px}
.f-card h3{font-size:.98rem;font-weight:700;margin-bottom:6px}
.f-card p{font-size:.84rem;color:#64748b;line-height:1.6}

/* SHOWCASE */
.showcase{padding:80px 24px;background:linear-gradient(180deg,#f8fafc,#fff)}
.showcase-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;max-width:900px;margin:0 auto}
.showcase-item{border-radius:12px;overflow:hidden;aspect-ratio:9/16;position:relative;box-shadow:0 10px 30px rgba(0,0,0,.1)}
.showcase-item img{width:100%;height:100%;object-fit:cover}
.showcase-item .label{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(to top,rgba(0,0,0,.7),transparent);color:#fff;padding:16px;font-size:.8rem;font-weight:600}

/* PRICING */
.pricing{padding:100px 24px;background:#0f172a;color:#fff}
.pricing .sec-head p{color:#94a3b8}
.pricing .sec-head h2{color:#fff}
.p-card{max-width:380px;margin:0 auto;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:36px;text-align:center;position:relative;overflow:hidden}
.p-card::before{content:'POPULAR';position:absolute;top:16px;right:-28px;background:#7c3aed;color:#fff;font-size:.65rem;font-weight:700;padding:4px 32px;transform:rotate(45deg)}
.p-card h3{font-size:1.1rem;font-weight:700;margin-bottom:8px}
.p-card .price{font-size:3rem;font-weight:900;margin:12px 0}.p-card .price small{font-size:1rem;color:#94a3b8;font-weight:400}
.p-card .per{font-size:.82rem;color:#64748b;margin-bottom:20px}
.p-list{text-align:left;margin-bottom:24px}.p-list .pi{display:flex;align-items:center;gap:10px;padding:8px 0;font-size:.88rem;color:#e2e8f0}.p-list .pi::before{content:'\2713';color:#10b981;font-weight:800}
.p-cta{display:block;background:#fff;color:#0f172a;padding:14px;border-radius:12px;font-weight:800;font-size:.95rem;transition:transform .2s}.p-cta:hover{transform:scale(1.02)}

/* HOW */
.how{padding:100px 24px}
.how-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;max-width:900px;margin:0 auto}
.how-step{text-align:center}.how-step .num{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#2563eb);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;margin:0 auto 12px;font-size:1rem}
.how-step h3{font-size:.92rem;font-weight:700;margin-bottom:4px}.how-step p{font-size:.8rem;color:#64748b}

/* CTA */
.cta-sec{padding:80px 24px;text-align:center;background:linear-gradient(135deg,#ede9fe,#dbeafe)}
.cta-sec h2{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:900;margin-bottom:12px}
.cta-sec p{color:#64748b;margin-bottom:24px;font-size:1rem}

.footer{padding:40px 24px;text-align:center;border-top:1px solid #f1f5f9}.footer h3{font-size:1rem;font-weight:800;margin-bottom:4px}.footer p{font-size:.8rem;color:#94a3b8}

@media(max-width:768px){.hero-inner{grid-template-columns:1fr;text-align:center}.hero-text p{margin-left:auto;margin-right:auto}.hero-btns{justify-content:center}.hero-visual{display:none}.f-grid{grid-template-columns:1fr}.how-steps{grid-template-columns:repeat(2,1fr)}.showcase-grid{grid-template-columns:1fr}.nav-links{display:none}}
</style></head><body>

<nav class="nav" id="nav">
<div class="nav-brand">City Maps</div>
<div class="nav-links"><a href="#features">Features</a><a href="#pricing">Pricing</a><a href="#how">How It Works</a></div>
<a href="#pricing" class="nav-btn">Get Started</a>
</nav>

<section class="hero">
<div class="hero-bg"></div><div class="hero-mesh"></div><div class="hero-glow"></div><div class="hero-glow2"></div>
<div class="hero-inner">
<div class="hero-text" data-aos="fade-right">
<div class="pill"><span class="dot"></span>""" + str(count) + """+ businesses trust us</div>
<h1>Your Business<br>Deserves To Be<br><span class="grad">Found Online</span></h1>
<p>Customers search Google every day for businesses like yours. If they can't find you online, they go to your competitor. City Maps fixes that — in just 5 minutes.</p>
<div class="hero-btns">
<a href="#pricing" class="btn btn-dark">Get Started Free &rarr;</a>
<a href="https://wa.me/917276738899?text=Hi%20City%20Maps%2C%20I%20want%20to%20create%20my%20business%20website" class="btn btn-outline">Find My Business</a>
</div>
</div>
<div class="hero-visual" data-aos="fade-left">
<img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=400&fit=crop" class="hero-mockup" alt="Dashboard">
<div class="hero-float f1">&#128200; 340+ visitors this week</div>
<div class="hero-float f2">&#128222; 12 new calls today</div>
</div>
</div>
</section>

<div class="logos">
<div class="logos-inner"><span>Salons</span><span>&#8226;</span><span>Restaurants</span><span>&#8226;</span><span>Doctors</span><span>&#8226;</span><span>Gyms</span><span>&#8226;</span><span>Hotels</span><span>&#8226;</span><span>Stores</span><span>&#8226;</span><span>Schools</span><span>&#8226;</span><span>Photographers</span></div>
</div>

<section class="features" id="features">
<div class="sec-head" data-aos="fade-up"><span class="tag">&#9889; What You Get</span><h2>Tools That Bring You Customers</h2><p>Every tool is designed to get you more calls, more walk-ins, and more revenue</p></div>
<div class="f-grid">
<div class="f-card" data-aos="fade-up"><div class="ic" style="background:#ede9fe">&#127760;</div><h3>Your Own Website</h3><p>Customers find your business name on Google, see your services, photos, reviews, and contact you instantly. Available 24/7.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="80"><div class="ic" style="background:#dbeafe">&#128222;</div><h3>More Phone Calls</h3><p>Click-to-call button on every page. Track how many people call you from your website each day.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="160"><div class="ic" style="background:#f0fdf4">&#128172;</div><h3>WhatsApp Enquiries</h3><p>Customers message you directly on WhatsApp from your website. Pre-filled message so they don't have to type.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="240"><div class="ic" style="background:#fef3c7">&#11088;</div><h3>Google Reviews Help</h3><p>We generate review request messages you can send to happy customers. More reviews = higher Google ranking.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="320"><div class="ic" style="background:#fce7f3">&#128247;</div><h3>Social Media Posts</h3><p>Download ready-made Instagram and WhatsApp status posts with your business name. No designer needed.</p></div>
<div class="f-card" data-aos="fade-up" data-aos-delay="400"><div class="ic" style="background:#ecfdf5">&#128722;</div><h3>Product Catalog</h3><p>Show your products with prices. Customers click "Buy Now" and it opens WhatsApp with their order details.</p></div>
</div>
</section>

<section class="showcase">
<div class="sec-head" data-aos="fade-up"><span class="tag">&#127912; Real Results</span><h2>Businesses Like Yours</h2><p>Salons, restaurants, doctors, gyms, stores — all growing online with City Maps</p></div>
<div class="showcase-grid">
<div class="showcase-item" data-aos="fade-up"><img src="https://images.unsplash.com/photo-1560066984-138dadb4c035?w=400&h=700&fit=crop" alt="Salon"><div class="label">Salon Website</div></div>
<div class="showcase-item" data-aos="fade-up" data-aos-delay="100"><img src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=700&fit=crop" alt="Restaurant"><div class="label">Restaurant Website</div></div>
<div class="showcase-item" data-aos="fade-up" data-aos-delay="200"><img src="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=700&fit=crop" alt="Gym"><div class="label">Gym Website</div></div>
</div>
</section>

<section class="how" id="how">
<div class="sec-head" data-aos="fade-up"><span class="tag">&#128640; Quick Setup</span><h2>Online in 5 Minutes</h2></div>
<div class="how-steps">
<div class="how-step" data-aos="fade-up"><div class="num">1</div><h3>Find Business</h3><p>Search your business name</p></div>
<div class="how-step" data-aos="fade-up" data-aos-delay="100"><div class="num">2</div><h3>Website Created</h3><p>Professional site built instantly</p></div>
<div class="how-step" data-aos="fade-up" data-aos-delay="200"><div class="num">3</div><h3>Claim & Manage</h3><p>Access your dashboard</p></div>
<div class="how-step" data-aos="fade-up" data-aos-delay="300"><div class="num">4</div><h3>Get Customers</h3><p>Start receiving enquiries</p></div>
</div>
</section>

<section class="pricing" id="pricing">
<div class="sec-head" data-aos="fade-up"><span class="tag" style="background:rgba(255,255,255,.1);color:#a78bfa">&#128176; Pricing</span><h2>Simple & Affordable</h2><p>Less than a cup of chai per day</p></div>
<div class="p-card" data-aos="zoom-in">
<h3>Business Plan</h3>
<div class="price">&#8377;69<small>/month</small></div>
<div class="per">Just &#8377;2.3 per day</div>
<div class="p-list">
<div class="pi">Professional Website (your-name.city-maps.online)</div>
<div class="pi">Track who visits, calls, messages you</div>
<div class="pi">WhatsApp click-to-chat on your website</div>
<div class="pi">Product catalog with Buy Now button</div>
<div class="pi">Ready social media posts (just download & post)</div>
<div class="pi">Festival offer templates (Diwali, Holi, etc.)</div>
<div class="pi">Google review request messages</div>
<div class="pi">QR code for visiting cards & banners</div>
<div class="pi">Daily growth tips for your business</div>
</div>
<a href="https://wa.me/917276738899?text=Hi%2C%20I%20want%20to%20start%20the%20Business%20Plan%20at%20Rs.69%2Fmonth" class="p-cta">Start Growing &rarr;</a>
</div>
</section>

<section class="cta-sec">
<div data-aos="fade-up">
<h2>Stop Losing Customers to Competitors</h2>
<p>Join """ + str(count) + """+ local businesses are already online. Don't get left behind.</p>
<a href="https://wa.me/917276738899?text=Hi%2C%20I%20want%20to%20create%20my%20business%20website%20on%20City%20Maps" class="btn btn-dark">Create My Website &rarr;</a>
</div>
</section>

<footer class="footer">
<h3>City Maps</h3>
<p>Your Digital Business Partner &bull; Powered by Kalpdev Digitals</p>
</footer>

<script src="https://unpkg.com/aos@2.3.4/dist/aos.js"></script>
<script>
AOS.init({duration:600,once:true,offset:60});
window.addEventListener('scroll',()=>{document.getElementById('nav').classList.toggle('solid',scrollY>50)});
</script>
</body></html>"""
    return HTMLResponse(content=html)



static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "videos")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static/videos", StaticFiles(directory=static_dir), name="videos")





@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}
