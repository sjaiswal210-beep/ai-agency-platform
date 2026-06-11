from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.api.routes.toolkit import get_tools_for_category

router = APIRouter(prefix="/panel", tags=["owner-panel"])


@router.get("/{website_id}", response_class=HTMLResponse)
def owner_panel(website_id: str):
    """Simple business dashboard for owners."""
    service = WebsiteService()
    lead_service = LeadService()
    from app.core.supabase import get_supabase
    from datetime import datetime, timedelta
    db = get_supabase()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""
    slug = website.get("slug", "")
    site_url = f"https://{slug}.city-maps.online" if slug else ""
    since_30d = (datetime.utcnow() - timedelta(days=30)).isoformat()
    try:
        views = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "page_view").gte("created_at", since_30d).execute()).count or 0
        calls = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "call_click").gte("created_at", since_30d).execute()).count or 0
        wa = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "whatsapp_click").gte("created_at", since_30d).execute()).count or 0
    except Exception:
        views = calls = wa = 0

    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{business_name} - Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Inter,sans-serif;background:#f8fafc;color:#1e293b;padding:16px;max-width:500px;margin:0 auto}}
.hdr{{text-align:center;padding:20px 0 16px}}.hdr h1{{font-size:1.2rem;font-weight:800}}.hdr p{{font-size:.78rem;color:#64748b;margin-top:4px}}.hdr a{{display:inline-block;margin-top:8px;color:#6366f1;font-size:.78rem;font-weight:600}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px}}.stat{{background:#fff;border-radius:12px;padding:14px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.04)}}.stat .n{{font-size:1.3rem;font-weight:800;color:#6366f1}}.stat .l{{font-size:.65rem;color:#94a3b8;margin-top:2px}}
.section-title{{font-size:.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;margin:16px 0 8px;padding-left:4px}}
.tools{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}.tool{{background:#fff;border-radius:12px;padding:14px;text-align:center;text-decoration:none;color:#1e293b;box-shadow:0 1px 3px rgba(0,0,0,.04);transition:all .15s}}.tool:hover{{transform:translateY(-2px);box-shadow:0 4px 12px rgba(99,102,241,.08)}}.tool .emoji{{font-size:1.5rem;margin-bottom:6px}}.tool .name{{font-size:.78rem;font-weight:600}}.tool .desc{{font-size:.65rem;color:#94a3b8;margin-top:2px}}
.wa-bar{{position:fixed;bottom:0;left:0;right:0;background:#fff;padding:12px 16px;box-shadow:0 -2px 8px rgba(0,0,0,.05);display:flex;gap:8px;max-width:500px;margin:0 auto}}.wa-bar a{{flex:1;text-align:center;padding:10px;border-radius:10px;font-weight:700;font-size:.8rem}}.wa-bar .green{{background:#25D366;color:#fff}}.wa-bar .blue{{background:#6366f1;color:#fff}}
body{{padding-bottom:70px}}
</style></head><body>
<div class="hdr">
<h1>{business_name}</h1>
<p>Your Business Dashboard</p>
<a href="{site_url}" target="_blank">{slug}.city-maps.online &rarr;</a>
</div>

<div class="stats">
<div class="stat"><div class="n">{views}</div><div class="l">Views</div></div>
<div class="stat"><div class="n">{calls}</div><div class="l">Calls</div></div>
<div class="stat"><div class="n">{wa}</div><div class="l">WhatsApp</div></div>
</div>

<div class="section-title">Manage</div>
<div class="tools">
<a href="https://city-maps.online/api/store/{website_id}/manage" target="_blank" class="tool"><div class="emoji">&#128722;</div><div class="name">Products</div><div class="desc">Add & manage products</div></a>
<a href="https://city-maps.online/api/branding/{website_id}/social-post/preview" target="_blank" class="tool"><div class="emoji">&#128247;</div><div class="name">Social Post</div><div class="desc">Create & download</div></a>
<a href="https://city-maps.online/api/qr/{website_id}" target="_blank" class="tool"><div class="emoji">&#128248;</div><div class="name">QR Code</div><div class="desc">For cards & banners</div></a>
<a href="https://city-maps.online/api/owner-analytics/{website_id}" target="_blank" class="tool"><div class="emoji">&#128200;</div><div class="name">Analytics</div><div class="desc">Detailed stats</div></a>
<a href="https://city-maps.online/api/daily/{website_id}" target="_blank" class="tool"><div class="emoji">&#128197;</div><div class="name">Daily Content</div><div class="desc">Ready to share</div></a>
<a href="https://city-maps.online/api/google-profile/{website_id}/setup-guide" target="_blank" class="tool"><div class="emoji">&#128205;</div><div class="name">Google Setup</div><div class="desc">Get on Google Maps</div></a>
</div>

<div class="wa-bar">
<a href="{site_url}" target="_blank" class="blue">View Website</a>
<a href="https://wa.me/917350785606?text=Hi%2C%20I%20need%20help%20with%20my%20business%20page" target="_blank" class="green">Get Help</a>
</div>
</body></html>'''
    return HTMLResponse(content=html)

@router.post("/{website_id}/social-links")
def save_social_links(website_id: str, links: dict):
    """Save social media links."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    content = website.get("content", {}) or {}
    content["social_links"] = {"instagram": links.get("instagram", ""), "facebook": links.get("facebook", ""), "youtube": links.get("youtube", "")}
    db.table("websites").update({"content": content}).eq("id", website_id).execute()
    return {"saved": True}
