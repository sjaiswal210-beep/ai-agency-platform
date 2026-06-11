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

<div class="section-title">Manage Your Business</div>
<div class="tools">
<a href="https://city-maps.online/api/store/{website_id}/manage" target="_blank" class="tool"><div class="emoji">&#128722;</div><div class="name">Products</div><div class="desc">Add & manage items</div></a>
<a href="https://city-maps.online/api/branding/{website_id}/social-post/preview" target="_blank" class="tool"><div class="emoji">&#128247;</div><div class="name">Social Post</div><div class="desc">Create & download</div></a>
<a href="https://city-maps.online/api/qr/{website_id}" target="_blank" class="tool"><div class="emoji">&#128248;</div><div class="name">QR Code</div><div class="desc">For cards & banners</div></a>
<a href="https://city-maps.online/api/owner-analytics/{website_id}" target="_blank" class="tool"><div class="emoji">&#128200;</div><div class="name">Analytics</div><div class="desc">Visitors & calls</div></a>
<a href="https://city-maps.online/api/daily/{website_id}" target="_blank" class="tool"><div class="emoji">&#128197;</div><div class="name">Daily Content</div><div class="desc">Ready to share</div></a>
<a href="https://city-maps.online/api/google-profile/{website_id}/setup-guide" target="_blank" class="tool"><div class="emoji">&#128205;</div><div class="name">Google Setup</div><div class="desc">Get on Maps</div></a>
</div>

<div class="section-title">Edit Your Website</div>
<div class="tools">
<a href="#" onclick="showEditor()" class="tool"><div class="emoji">&#9998;</div><div class="name">Edit Website</div><div class="desc">Change text & info</div></a>
<a href="#" onclick="showSocial()" class="tool"><div class="emoji">&#128279;</div><div class="name">Social Links</div><div class="desc">Instagram & Facebook</div></a>
<a href="#" onclick="showGallery()" class="tool"><div class="emoji">&#128444;</div><div class="name">Gallery Photos</div><div class="desc">Add your photos</div></a>
<a href="https://city-maps.online/api/campaigns/{website_id}/festival/diwali" target="_blank" class="tool"><div class="emoji">&#127878;</div><div class="name">Festival Offers</div><div class="desc">Campaign templates</div></a>
</div>

<div id="editorPanel" style="display:none;background:#fff;border-radius:12px;padding:16px;margin-top:12px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
<h3 style="font-size:.85rem;font-weight:700;margin-bottom:10px">Edit Website Content</h3>
<p style="font-size:.72rem;color:#64748b;margin-bottom:8px">Type what you want to change (e.g., "Change phone number to 9876543210" or "Add Diwali offer 20% off")</p>
<textarea id="editPrompt" rows="3" placeholder="Type your edit here..." style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;font-family:inherit;resize:none;margin-bottom:8px"></textarea>
<button onclick="submitEdit()" style="background:#6366f1;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer;width:100%">Apply Changes</button>
<p id="editResult" style="font-size:.75rem;color:#64748b;margin-top:8px"></p>
</div>

<div id="socialPanel" style="display:none;background:#fff;border-radius:12px;padding:16px;margin-top:12px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
<h3 style="font-size:.85rem;font-weight:700;margin-bottom:10px">Social Media Links</h3>
<input id="instaUrl" placeholder="Instagram URL" style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;margin-bottom:6px">
<input id="fbUrl" placeholder="Facebook URL" style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;margin-bottom:6px">
<input id="ytUrl" placeholder="YouTube URL" style="width:100%;padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;margin-bottom:8px">
<button onclick="saveSocial()" style="background:#6366f1;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer;width:100%">Save Social Links</button>
</div>

<div id="galleryPanel" style="display:none;background:#fff;border-radius:12px;padding:16px;margin-top:12px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
<h3 style="font-size:.85rem;font-weight:700;margin-bottom:10px">Gallery Photos</h3>
<p style="font-size:.72rem;color:#64748b;margin-bottom:8px">Paste image URLs (one per line) from Instagram or any website</p>
<textarea id="galUrls" rows="4" placeholder="Paste image URLs here..." style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;font-family:inherit;resize:none;margin-bottom:8px"></textarea>
<button onclick="saveGallery()" style="background:#6366f1;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer;width:100%">Save Photos</button>
</div>

<div class="wa-bar">
<a href="{site_url}" target="_blank" class="blue">View Website</a>
<a href="https://wa.me/917350785606?text=Hi%2C%20I%20need%20help%20with%20my%20business%20page" target="_blank" class="green">Get Help</a>
</div>
<script>
function showEditor(){{document.getElementById("editorPanel").style.display="block";document.getElementById("socialPanel").style.display="none";document.getElementById("galleryPanel").style.display="none";}}
function showSocial(){{document.getElementById("socialPanel").style.display="block";document.getElementById("editorPanel").style.display="none";document.getElementById("galleryPanel").style.display="none";}}
function showGallery(){{document.getElementById("galleryPanel").style.display="block";document.getElementById("editorPanel").style.display="none";document.getElementById("socialPanel").style.display="none";}}
async function submitEdit(){{var p=document.getElementById("editPrompt").value;if(!p)return;document.getElementById("editResult").textContent="Applying...";try{{var r=await fetch("https://city-maps.online/api/editor/{website_id}/edit",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{prompt:p}})}});var d=await r.json();document.getElementById("editResult").textContent=d.message||"Done! Refresh your website to see changes.";}}catch{{document.getElementById("editResult").textContent="Failed. Try again.";}}}}
async function saveSocial(){{try{{await fetch("https://city-maps.online/api/panel/{website_id}/social-links",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{instagram:document.getElementById("instaUrl").value,facebook:document.getElementById("fbUrl").value,youtube:document.getElementById("ytUrl").value}})}});alert("Social links saved!");}}catch{{alert("Failed");}}}}
async function saveGallery(){{var urls=document.getElementById("galUrls").value.split(String.fromCharCode(10)).filter(function(u){{return u.trim()}});try{{await fetch("https://city-maps.online/api/panel/{website_id}/gallery",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{urls:urls}})}});alert("Gallery saved! "+urls.length+" photos added.");}}catch{{alert("Failed");}}}}
</script></body></html>'''
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


@router.post("/{website_id}/gallery")
def save_gallery(website_id: str, data: dict):
    """Save gallery photos (custom URLs from owner)."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    content = website.get("content", {}) or {}
    urls = data.get("urls", [])
    urls = [u.strip() for u in urls if u and u.strip()]
    content["custom_gallery"] = urls
    db.table("websites").update({"content": content}).eq("id", website_id).execute()
    return {"saved": True, "count": len(urls)}
