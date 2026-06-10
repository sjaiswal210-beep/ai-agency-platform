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
    """City Maps simple landing page."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        sites = db.table("websites").select("slug", count="exact").not_.is_("slug", "null").execute()
        count = sites.count or 0
    except Exception:
        count = 0

    html = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Business Websites</title>
<meta name="theme-color" content="#111827">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Inter,sans-serif;background:#111827;color:#f9fafb}}a{{text-decoration:none;color:inherit}}
.nav{{padding:14px 20px;display:flex;align-items:center;justify-content:space-between;max-width:900px;margin:0 auto}}.nav b{{font-size:1rem;color:#60a5fa}}.nav a{{font-size:.75rem;color:#9ca3af;border:1px solid #374151;padding:6px 12px;border-radius:6px}}
.hero{{text-align:center;padding:50px 20px 30px;max-width:600px;margin:0 auto}}
.hero h1{{font-size:clamp(1.8rem,5vw,2.8rem);font-weight:900;line-height:1.15;margin-bottom:12px}}.hero h1 span{{color:#60a5fa}}
.hero p{{color:#9ca3af;font-size:.92rem;margin-bottom:22px;line-height:1.6}}
.hero-img{{margin:24px auto;max-width:500px}}.hero-img img{{width:100%;border-radius:12px;border:1px solid #1f2937}}
.search{{display:flex;gap:6px;max-width:380px;margin:0 auto;background:#1f2937;border:1px solid #374151;border-radius:10px;padding:4px}}.search input{{flex:1;background:transparent;border:none;padding:10px 12px;color:#fff;font-size:.85rem;outline:none}}.search input::placeholder{{color:#6b7280}}.search button{{background:#3b82f6;color:#fff;border:none;padding:10px 16px;border-radius:7px;font-weight:700;font-size:.78rem;cursor:pointer}}
#searchResult{{max-width:380px;margin:8px auto 0}}
.stats{{display:flex;justify-content:center;gap:24px;padding:20px;margin-top:16px}}.stats div{{text-align:center}}.stats .n{{font-size:1.2rem;font-weight:800;color:#60a5fa}}.stats .l{{font-size:.65rem;color:#6b7280}}
.section{{max-width:700px;margin:0 auto;padding:50px 20px}}.section h2{{font-size:1.4rem;font-weight:800;text-align:center;margin-bottom:6px}}.section .sub{{text-align:center;color:#6b7280;font-size:.85rem;margin-bottom:24px}}
.cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}.card{{background:#1f2937;border:1px solid #374151;border-radius:10px;padding:16px}}.card .em{{font-size:1.3rem;margin-bottom:8px}}.card h3{{font-size:.82rem;font-weight:700;margin-bottom:3px}}.card p{{font-size:.72rem;color:#9ca3af;line-height:1.5}}
.pricing{{max-width:700px;margin:0 auto;padding:40px 20px;text-align:center}}.pricing h2{{font-size:1.4rem;font-weight:800;margin-bottom:20px}}
.plans{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.plan{{background:#1f2937;border:1px solid #374151;border-radius:12px;padding:20px;text-align:left}}.plan.pop{{border-color:#3b82f6}}.plan h3{{font-size:.78rem;color:#9ca3af;margin-bottom:4px}}.plan .price{{font-size:1.8rem;font-weight:900;color:#f9fafb}}.plan .price small{{font-size:.75rem;color:#6b7280}}.plan ul{{list-style:none;margin:12px 0}}.plan li{{font-size:.75rem;color:#d1d5db;padding:4px 0;padding-left:14px;position:relative}}.plan li::before{{content:"\27A4";position:absolute;left:0;color:#60a5fa;font-size:.6rem}}.plan-btn{{display:block;text-align:center;padding:10px;border-radius:8px;font-weight:700;font-size:.8rem;margin-top:12px}}.plan-btn.fill{{background:#3b82f6;color:#fff}}.plan-btn.ghost{{border:1px solid #374151;color:#d1d5db}}
.cta{{text-align:center;padding:40px 20px}}.cta h2{{font-size:1.2rem;font-weight:800;margin-bottom:8px}}.cta p{{color:#6b7280;font-size:.85rem;margin-bottom:16px}}.cta a{{background:#3b82f6;color:#fff;padding:12px 22px;border-radius:8px;font-weight:700;font-size:.85rem}}
.wa-float{{position:fixed;bottom:20px;right:20px;width:52px;height:52px;border-radius:50%;background:#25D366;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(37,211,102,.4);z-index:99}}
.footer{{text-align:center;padding:20px;font-size:.7rem;color:#4b5563;border-top:1px solid #1f2937}}.footer b{{color:#60a5fa}}
@media(max-width:500px){{.cards,.plans{{grid-template-columns:1fr}}.stats{{gap:14px}}}}
</style></head><body>
<nav class="nav"><b>City Maps</b><a href="https://ai-agency-platform-blush.vercel.app">Admin</a></nav>
<section class="hero">
<h1>Apna Business<br><span>Online Le Jaayein</span></h1>
<p>Professional website for your business. Customers Google pe dhundhein, call karein, WhatsApp pe order dein.</p>
<div class="search"><input id="bizSearch" placeholder="Business name search karein..."><button onclick="searchBiz()">Search</button></div>
<div id="searchResult"></div>
<div class="hero-img"><img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=320&fit=crop" alt="Dashboard"></div>
<div class="stats"><div><div class="n">{count}+</div><div class="l">Businesses</div></div><div><div class="n">5 min</div><div class="l">Setup</div></div><div><div class="n">Rs.49</div><div class="l">Per Month</div></div></div>
</section>
<section class="section">
<h2>Kya Milega Aapko</h2><p class="sub">Simple tools jo customers badhayein</p>
<div class="cards">
<div class="card"><div class="em">&#127760;</div><h3>Business Website</h3><p>Apna professional website jismein services, photos, location sab dikhega.</p></div>
<div class="card"><div class="em">&#128222;</div><h3>More Calls</h3><p>Ek click mein customer call kare. Track karein kitne log call kiye.</p></div>
<div class="card"><div class="em">&#128172;</div><h3>WhatsApp Orders</h3><p>Customer ek tap mein WhatsApp pe order de. Ready message.</p></div>
<div class="card"><div class="em">&#128722;</div><h3>Product Catalog</h3><p>Products dikhayein price ke saath. Buy Now se WhatsApp order.</p></div>
</div>
</section>
<section class="pricing" id="pricing">
<h2>Simple Pricing</h2>
<div class="plans">
<div class="plan"><h3>Starter</h3><div class="price">&#8377;49<small>/mo</small></div><ul><li>Business Website</li><li>WhatsApp Button</li><li>Google Maps</li><li>Contact Form</li><li>Mobile Friendly</li></ul><a href="https://wa.me/917350785606?text=Hi%2C%20Starter%20plan%20chahiye" class="plan-btn ghost">Get Started</a></div>
<div class="plan pop"><h3>Business</h3><div class="price">&#8377;69<small>/mo</small></div><ul><li>Everything in Starter</li><li>Product Catalog</li><li>Analytics Dashboard</li><li>Social Posts</li><li>Growth Tools</li><li>Festival Templates</li></ul><a href="https://wa.me/917350785606?text=Hi%2C%20Business%20plan%20chahiye" class="plan-btn fill">Get Started</a></div>
</div>
</section>
<div class="cta"><h2>Aapka competitor online hai. Aap kab?</h2><p>Har din customers unke paas jaate hain.</p><a href="https://wa.me/917350785606?text=Hi%20City%20Maps%2C%20mera%20website%20banao">Mera Website Banao &rarr;</a></div>
<a href="https://wa.me/917350785606?text=Hi%20City%20Maps" class="wa-float" target="_blank"><svg width="26" height="26" viewBox="0 0 24 24" fill="#fff"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492l4.625-1.476A11.929 11.929 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75c-2.115 0-4.09-.57-5.793-1.564l-.415-.248-2.74.875.876-2.672-.27-.43A9.71 9.71 0 012.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75z"/></svg></a>
<footer class="footer"><b>City Maps</b> &bull; Powered by Kalpdev Digitals</footer>
<script>
async function searchBiz(){{const q=document.getElementById("bizSearch").value.trim();if(!q)return;const r=document.getElementById("searchResult");r.style.display="block";r.innerHTML="<p style=\"text-align:center;color:#6b7280;font-size:.78rem\">Searching...</p>";try{{const slug=q.toLowerCase().replace(/[^a-z0-9\s-]/g,"").replace(/[\s]+/g,"-");const resp=await fetch("/api/preview/by-slug/"+slug);if(resp.ok){{r.innerHTML="<div style=\"background:#064e3b;border:1px solid #065f46;border-radius:8px;padding:10px;text-align:center;margin-top:6px\"><p style=\"color:#34d399;font-size:.82rem;font-weight:600\">Found!</p><a href=\"https://"+slug+".city-maps.online\" target=\"_blank\" style=\"color:#60a5fa;font-size:.78rem\">Visit &rarr;</a></div>";}}else{{throw new Error("nf");}}}}catch{{r.innerHTML="<div style=\"background:#1f2937;border:1px solid #374151;border-radius:8px;padding:12px;margin-top:6px;text-align:center\"><p style=\"font-size:.82rem;margin-bottom:8px\">Not found</p><p style=\"font-size:.72rem;color:#6b7280;margin-bottom:8px\">Free website chahiye?</p><form onsubmit=\"submitReq(event)\" style=\"display:flex;flex-direction:column;gap:5px;max-width:240px;margin:0 auto\"><input id=\"reqName\" value=\""+q+"\" required style=\"padding:8px;background:#111827;border:1px solid #374151;border-radius:6px;color:#fff;font-size:.78rem\"><input id=\"reqPhone\" placeholder=\"WhatsApp No.\" required style=\"padding:8px;background:#111827;border:1px solid #374151;border-radius:6px;color:#fff;font-size:.78rem\"><input id=\"reqCity\" placeholder=\"City\" required style=\"padding:8px;background:#111827;border:1px solid #374151;border-radius:6px;color:#fff;font-size:.78rem\"><button type=\"submit\" style=\"background:#3b82f6;color:#fff;padding:8px;border:none;border-radius:6px;font-weight:700;font-size:.78rem;cursor:pointer\">Request</button></form></div>";}}}}
async function submitReq(e){{e.preventDefault();try{{await fetch("/api/website-requests",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{business_name:document.getElementById("reqName").value,phone:document.getElementById("reqPhone").value,city:document.getElementById("reqCity").value}})}});document.getElementById("searchResult").innerHTML="<div style=\"background:#064e3b;border:1px solid #065f46;border-radius:8px;padding:10px;text-align:center;margin-top:6px\"><p style=\"color:#34d399;font-size:.82rem;font-weight:600\">Done! 24 hours mein notify karenge.</p></div>";}}catch{{alert("Failed");}}}}
</script></body></html>'''
    return HTMLResponse(content=html)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agency-platform"}
