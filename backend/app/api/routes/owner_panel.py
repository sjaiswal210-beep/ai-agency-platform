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

    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{business_name} - Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Inter,sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}
.hdr{{text-align:center;padding:12px 0 10px}}.hdr h1{{font-size:1.2rem;font-weight:800}}.hdr p{{font-size:.78rem;color:#64748b;margin-top:4px}}.hdr a{{display:inline-block;margin-top:8px;color:#6366f1;font-size:.78rem;font-weight:600}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px}}.stat{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:14px;text-align:center}}.stat .n{{font-size:1.1rem;font-weight:800;color:#6366f1}}.stat .l{{font-size:.65rem;color:#94a3b8;margin-top:2px}}
.section-title{{font-size:.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;margin:10px 0 6px;padding-left:4px}}
.tools{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}}.tool{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:10px 6px;text-align:center;text-decoration:none;color:#fff;transition:all .15s}}.tool:hover{{transform:translateY(-2px);border-color:#6366f1;box-shadow:0 4px 12px rgba(99,102,241,.15)}}.tool .emoji{{font-size:1.2rem;margin-bottom:4px}}.tool .name{{font-size:.68rem;font-weight:600}}.tool .desc{{display:none}}
.wa-bar{{position:fixed;bottom:0;left:0;right:0;background:#0f172a;border-top:1px solid #334155;padding:12px 16px;display:flex;gap:8px;max-width:500px;margin:0 auto}}.wa-bar a{{flex:1;text-align:center;padding:10px;border-radius:10px;font-weight:700;font-size:.8rem;text-decoration:none}}.wa-bar .green{{background:#25D366;color:#fff}}.wa-bar .blue{{background:#6366f1;color:#fff}}
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
<a href="/api/branding/{website_id}/social-post/preview" target="_blank" class="tool"><div class="emoji">&#128247;</div><div class="name">Social Post</div><div class="desc">Create & download</div></a>
<a href="/api/qr/{website_id}" target="_blank" class="tool"><div class="emoji">&#128248;</div><div class="name">QR Code</div><div class="desc">For cards & banners</div></a>
<a href="/api/owner-analytics/{website_id}" target="_blank" class="tool"><div class="emoji">&#128200;</div><div class="name">Analytics</div><div class="desc">Visitors & calls</div></a>
<a href="/api/daily/{website_id}" target="_blank" class="tool"><div class="emoji">&#128197;</div><div class="name">Daily Content</div><div class="desc">Ready to share</div></a>
<a href="/api/offers/{website_id}" target="_blank" class="tool"><div class="emoji">&#127873;</div><div class="name">Create Offer</div><div class="desc">Share deals & ads</div></a>
<a href="https://city-maps.online/api/google-profile/{website_id}/setup-guide" target="_blank" class="tool"><div class="emoji">&#128205;</div><div class="name">Google Setup</div><div class="desc">Get on Maps</div></a>
<a href="/api/logo-gen/{website_id}/preview" target="_blank" class="tool"><div class="emoji">&#127912;</div><div class="name">Logo</div><div class="desc">Generate logo</div></a>
<a href="https://city-maps.online/api/panel/{website_id}/video-creator" target="_blank" class="tool"><div class="emoji">&#127916;</div><div class="name">Promo Videos</div><div class="desc">Photo slideshow</div></a>
<a href="https://city-maps.online/api/panel/{website_id}/ai-video" target="_blank" class="tool"><div class="emoji">&#129302;</div><div class="name">Video Creator</div><div class="desc">Create promo video</div></a>
</div>

<div class="section-title">Edit Your Website</div>
<div class="tools">
<a href="#" onclick="showEditor()" class="tool"><div class="emoji">&#9998;</div><div class="name">Edit Website</div><div class="desc">Change text & info</div></a>
<a href="/api/panel/{website_id}/social-links" target="_blank" class="tool"><div class="emoji">&#128279;</div><div class="name">Social Links</div><div class="desc">Instagram & Facebook</div></a>
<a href="/api/panel/{website_id}/gallery" target="_blank" class="tool"><div class="emoji">&#128444;</div><div class="name">Gallery Photos</div><div class="desc">Add your photos</div></a>
<a href="/api/offers/{website_id}" target="_blank" class="tool"><div class="emoji">&#127878;</div><div class="name">Festival Offers</div><div class="desc">Campaign templates</div></a>
</div>

<div id="editorPanel" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center;padding:16px"><div style="background:#fff;border-radius:16px;padding:20px;width:100%;max-width:400px;position:relative"><button onclick="closeModals()" style="position:absolute;top:10px;right:12px;background:none;border:none;font-size:1.2rem;cursor:pointer">&times;</button>
<div style="background:#fff;border-radius:16px;padding:20px;width:100%;max-width:400px"><button onclick="closeModals()" style="float:right;background:none;border:none;font-size:1.3rem;cursor:pointer">&times;</button><h3 style="font-size:.85rem;font-weight:700;margin-bottom:10px">Edit Website Content</h3>
<p style="font-size:.72rem;color:#64748b;margin-bottom:8px">Type what you want to change (e.g., "Change phone number to 9876543210" or "Add Diwali offer 20% off")</p>
<textarea id="editPrompt" rows="3" placeholder="Type your edit here..." style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;font-family:inherit;resize:none;margin-bottom:8px"></textarea>
<button onclick="submitEdit()" style="background:#6366f1;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer;width:100%">Apply Changes</button>
<p id="editResult" style="font-size:.75rem;color:#64748b;margin-top:8px"></p>
</div>

<div id="socialPanel" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center;padding:16px"><div style="background:#fff;border-radius:16px;padding:20px;width:100%;max-width:400px;position:relative"><button onclick="closeModals()" style="position:absolute;top:10px;right:12px;background:none;border:none;font-size:1.2rem;cursor:pointer">&times;</button>
<div style="background:#fff;border-radius:16px;padding:20px;width:100%;max-width:400px"><button onclick="closeModals()" style="float:right;background:none;border:none;font-size:1.3rem;cursor:pointer">&times;</button><h3 style="font-size:.85rem;font-weight:700;margin-bottom:10px">Social Media Links</h3>
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
<script>function openTool(url){{var m=document.getElementById('toolModal');m.style.display='flex';m.style.visibility='visible';document.getElementById('toolFrame').src=url;}}function closeTool(){{document.getElementById('toolModal').style.display='none';document.getElementById('toolFrame').src='';}}function closeModals(){{document.querySelectorAll("#editorPanel,#socialPanel,#galleryPanel").forEach(function(p){{p.style.display="none"}})}}
function showEditor(){{document.getElementById("editorPanel").style.display="flex";document.getElementById("socialPanel").style.display="none";document.getElementById("galleryPanel").style.display="none";}}
function showSocial(){{document.getElementById("socialPanel").style.display="flex";document.getElementById("editorPanel").style.display="none";document.getElementById("galleryPanel").style.display="none";}}
function showGallery(){{document.getElementById("galleryPanel").style.display="flex";document.getElementById("editorPanel").style.display="none";document.getElementById("socialPanel").style.display="none";}}
async function submitEdit(){{var p=document.getElementById("editPrompt").value;if(!p)return;document.getElementById("editResult").textContent="Applying...";try{{var r=await fetch("https://city-maps.online/api/editor/{website_id}/edit",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{prompt:p}})}});var d=await r.json();document.getElementById("editResult").textContent=d.message||"Done! Refresh your website to see changes.";}}catch{{document.getElementById("editResult").textContent="Failed. Try again.";}}}}
async function saveSocial(){{try{{await fetch("https://city-maps.online/api/panel/{website_id}/social-links",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{instagram:document.getElementById("instaUrl").value,facebook:document.getElementById("fbUrl").value,youtube:document.getElementById("ytUrl").value}})}});alert("Social links saved!");}}catch{{alert("Failed");}}}}
async function saveGallery(){{var urls=document.getElementById("galUrls").value.split(String.fromCharCode(10)).filter(function(u){{return u.trim()}});try{{await fetch("https://city-maps.online/api/panel/{website_id}/gallery",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{urls:urls}})}});alert("Gallery saved! "+urls.length+" photos added.");}}catch{{alert("Failed");}}}}
</script><div id="toolModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;align-items:center;justify-content:center;padding:10px"><div style="background:#fff;border-radius:16px;width:100%;max-width:480px;height:85vh;position:relative;overflow:hidden"><button onclick="closeTool()" style="position:absolute;top:8px;right:12px;background:rgba(0,0,0,.6);color:#fff;border:none;width:28px;height:28px;border-radius:50%;font-size:1rem;cursor:pointer;z-index:10">&times;</button><iframe id="toolFrame" style="width:100%;height:100%;border:none;border-radius:16px" src=""></iframe></div></div></body></html>'''
    return HTMLResponse(content=html)

@router.get("/{website_id}/social-links", response_class=HTMLResponse)
def social_links_page(website_id: str):
    """Social links editor page."""
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Social Links</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:400px;margin:0 auto}}h2{{font-size:1rem;margin-bottom:16px}}input{{width:100%;padding:10px;border:1px solid #334155;border-radius:8px;background:#1e293b;color:#fff;font-size:.8rem;margin-bottom:10px;outline:none}}button{{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.85rem}}</style></head><body><h2>Social Media Links</h2><input id="instaUrl" placeholder="Instagram URL"><input id="fbUrl" placeholder="Facebook URL"><input id="ytUrl" placeholder="YouTube URL"><button onclick="save()">Save Links</button><p id="msg" style="margin-top:10px;font-size:.75rem;color:#22c55e"></p><script>async function save(){{try{{await fetch("/api/panel/{website_id}/social-links",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{instagram:document.getElementById("instaUrl").value,facebook:document.getElementById("fbUrl").value,youtube:document.getElementById("ytUrl").value}})}});document.getElementById("msg").textContent="Saved!"}}catch{{alert("Failed")}}}}</script></body></html>'''
    return HTMLResponse(content=html)


@router.get("/{website_id}/gallery", response_class=HTMLResponse)
def gallery_page(website_id: str):
    """Gallery photos editor page."""
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>Gallery Photos</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:400px;margin:0 auto}}h2{{font-size:1rem;margin-bottom:8px}}p{{font-size:.75rem;color:#64748b;margin-bottom:12px}}textarea{{width:100%;padding:10px;border:1px solid #334155;border-radius:8px;background:#1e293b;color:#fff;font-size:.8rem;min-height:150px;margin-bottom:10px;outline:none;resize:vertical}}button{{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.85rem}}</style></head><body><h2>Gallery Photos</h2><p>Add image URLs (one per line). Use Google Drive or Imgur links.</p><textarea id="galUrls" placeholder="https://drive.google.com/...&#10;https://i.imgur.com/...&#10;https://..."></textarea><button onclick="save()">Save Gallery</button><p id="msg" style="margin-top:10px;font-size:.75rem;color:#22c55e"></p><script>async function save(){{var urls=document.getElementById("galUrls").value.split("\\n").filter(function(u){{return u.trim()}});try{{await fetch("/api/panel/{website_id}/gallery",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{urls:urls}})}});document.getElementById("msg").textContent="Saved! "+urls.length+" photos added."}}catch{{alert("Failed")}}}}</script></body></html>'''
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


@router.get("/{website_id}/video-creator", response_class=HTMLResponse)
def video_creator_page(website_id: str):
    """Browser-based video creator - all processing client-side."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"

    html = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{business_name} - Video Creator</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}input,select,textarea{{font-size:16px!important}}
body{{font-family:Inter,sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}
.hdr{{text-align:center;padding:16px 0}}.hdr h1{{font-size:1.1rem;font-weight:800}}.hdr p{{font-size:.72rem;color:#64748b;margin-top:4px}}
.step{{background:#fff;border-radius:14px;padding:18px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.04);border:1px solid #e2e8f0}}
.step h2{{font-size:.85rem;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:8px}}
.step-num{{width:24px;height:24px;border-radius:50%;background:#6366f1;color:#fff;font-size:.7rem;font-weight:700;display:flex;align-items:center;justify-content:center}}
.upload-zone{{border:2px dashed #e2e8f0;border-radius:10px;padding:24px;text-align:center;cursor:pointer;transition:all .2s}}
.upload-zone:hover{{border-color:#6366f1;background:rgba(99,102,241,.02)}}
.upload-zone p{{font-size:.78rem;color:#64748b}}.upload-zone .icon{{font-size:2rem;margin-bottom:8px}}
.thumbs{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}}
.thumb{{position:relative;aspect-ratio:1;border-radius:8px;overflow:hidden}}.thumb img{{width:100%;height:100%;object-fit:cover}}
.thumb .del{{position:absolute;top:2px;right:2px;width:18px;height:18px;border-radius:50%;background:rgba(0,0,0,.6);color:#fff;font-size:.6rem;display:flex;align-items:center;justify-content:center;cursor:pointer}}
.text-input{{width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;margin-bottom:8px}}
.text-opts{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}}
.text-opts button{{padding:5px 10px;border-radius:6px;border:1px solid #e2e8f0;background:#fff;font-size:.7rem;font-weight:600;cursor:pointer}}
.text-opts button.active{{background:#6366f1;color:#fff;border-color:#6366f1}}
.music-list{{display:flex;flex-direction:column;gap:6px}}
.music-item{{display:flex;align-items:center;gap:10px;padding:10px;border:1px solid #e2e8f0;border-radius:8px;cursor:pointer;transition:all .15s}}
.music-item:hover,.music-item.selected{{border-color:#6366f1;background:rgba(99,102,241,.04)}}
.music-item .name{{font-size:.78rem;font-weight:600;flex:1}}.music-item .dur{{font-size:.68rem;color:#94a3b8}}
.music-item .play-btn{{width:28px;height:28px;border-radius:50%;background:#6366f1;color:#fff;display:flex;align-items:center;justify-content:center;font-size:.7rem;border:none;cursor:pointer}}
.gen-btn{{width:100%;padding:14px;background:#6366f1;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.88rem;cursor:pointer;transition:all .2s}}
.gen-btn:hover{{background:#4f46e5;transform:translateY(-1px)}}.gen-btn:disabled{{opacity:.5;cursor:not-allowed;transform:none}}
.progress{{width:100%;height:6px;background:#e2e8f0;border-radius:3px;margin-top:10px;overflow:hidden}}
.progress-bar{{height:100%;background:linear-gradient(90deg,#6366f1,#8b5cf6);border-radius:3px;transition:width .3s}}
.result{{text-align:center;padding:20px}}.result video{{width:100%;border-radius:10px;margin-bottom:12px}}
.dl-btn{{display:inline-block;padding:12px 24px;background:#22c55e;color:#fff;border-radius:10px;font-weight:700;font-size:.85rem;text-decoration:none;cursor:pointer;border:none}}
.reset-btn{{display:block;margin:10px auto 0;background:none;border:none;color:#64748b;font-size:.75rem;cursor:pointer;text-decoration:underline}}
.note{{font-size:.68rem;color:#94a3b8;text-align:center;margin-top:8px}}
.hidden{{display:none}}
</style></head><body>
<div class="hdr">
<h1>&#127916; Video Creator</h1>
<p>{business_name} - Create promotional videos</p>
</div>

<div id="step1" class="step">
<h2><span class="step-num">1</span>Upload Photos</h2>
<div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
<div class="icon">&#128247;</div>
<p>Tap to select photos (2-20 images)<br><span style="font-size:.68rem;color:#94a3b8">JPEG, PNG, WebP &bull; Max 10MB each</span></p>
</div>
<input type="file" id="fileInput" accept="image/jpeg,image/png,image/webp" multiple style="display:none" onchange="handleFiles(this.files)">
<div class="thumbs" id="thumbs"></div>
</div>

<div id="step2" class="step hidden">
<h2><span class="step-num">2</span>Add Text</h2>
<input type="text" class="text-input" id="textInput" placeholder="Business name or offer text (optional)" maxlength="100">
<div class="text-opts">
<button onclick="setPos('top')" id="pos-top">Top</button>
<button onclick="setPos('center')" id="pos-center" class="active">Center</button>
<button onclick="setPos('bottom')" id="pos-bottom">Bottom</button>
</div>
<div class="text-opts">
<button onclick="setSize('small')" id="sz-small">Small</button>
<button onclick="setSize('medium')" id="sz-medium" class="active">Medium</button>
<button onclick="setSize('large')" id="sz-large">Large</button>
</div>
</div>

<div id="step3" class="step hidden">
<h2><span class="step-num">3</span>Choose Music</h2>
<div class="music-list" id="musicList"></div>
</div>

<div id="step4" class="step hidden">
<h2><span class="step-num">4</span>Generate Video</h2>
<button class="gen-btn" id="genBtn" onclick="generateVideo()">&#127916; Create Video</button>
<div class="progress hidden" id="progressWrap"><div class="progress-bar" id="progressBar" style="width:0%"></div></div>
<p id="statusText" class="note"></p>
</div>

<div id="step5" class="step hidden">
<div class="result">
<h2 style="margin-bottom:12px">&#10004;&#65039; Video Ready!</h2>
<video id="resultVideo" controls></video>
<button class="dl-btn" onclick="downloadVideo()">&#11015; Download Video</button>
<button class="reset-btn" onclick="resetAll()">Create Another Video</button>
<p class="note">No data stored on server. Everything processed in your browser.</p>
</div>
</div>

<script>function openTool(url){{var m=document.getElementById('toolModal');m.style.display='flex';m.style.visibility='visible';document.getElementById('toolFrame').src=url;}}function closeTool(){{document.getElementById('toolModal').style.display='none';document.getElementById('toolFrame').src='';}}function closeModals(){{document.querySelectorAll("#editorPanel,#socialPanel,#galleryPanel").forEach(function(p){{p.style.display="none"}})}}
let photos=[];let textOverlay="";let textPos="center";let textSize="medium";let selectedMusic=0;let videoBlob=null;let videoUrl=null;

const MUSIC_TRACKS=[
{{name:"Upbeat Corporate",url:"https://cdn.pixabay.com/audio/2022/10/25/audio_564fdf2fac.mp3",dur:"2:10"}},
{{name:"Happy Acoustic",url:"https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",dur:"1:55"}},
{{name:"Inspiring Piano",url:"https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d2.mp3",dur:"2:30"}},
{{name:"Modern Technology",url:"https://cdn.pixabay.com/audio/2022/03/15/audio_942de29241.mp3",dur:"2:05"}},
{{name:"Chill Lofi",url:"https://cdn.pixabay.com/audio/2022/11/22/audio_a1876e0990.mp3",dur:"1:45"}}
];

let audioEl=null;

function initMusic(){{
const list=document.getElementById("musicList");
MUSIC_TRACKS.forEach((t,i)=>{{
const div=document.createElement("div");
div.className="music-item"+(i===0?" selected":"");
div.innerHTML=`<button class="play-btn" onclick="event.stopPropagation();previewMusic(${{i}})">&#9654;</button><span class="name">${{t.name}}</span><span class="dur">${{t.dur}}</span>`;
div.onclick=()=>selectMusic(i);
list.appendChild(div);
}});
}}

function selectMusic(i){{
selectedMusic=i;
document.querySelectorAll(".music-item").forEach((el,idx)=>{{el.className="music-item"+(idx===i?" selected":"");}});
}}

function previewMusic(i){{
if(audioEl){{audioEl.pause();audioEl=null;}}
audioEl=new Audio(MUSIC_TRACKS[i].url);
audioEl.volume=0.5;audioEl.play();
setTimeout(()=>{{if(audioEl)audioEl.pause();}},8000);
}}

function handleFiles(files){{
const maxFiles=20;const maxSize=10*1024*1024;
for(let f of files){{
if(photos.length>=maxFiles){{alert("Max 20 photos");break;}}
if(f.size>maxSize){{alert(f.name+" is too large (max 10MB)");continue;}}
if(!f.type.match(/image\/(jpeg|png|webp)/)){{alert(f.name+" is not a valid format");continue;}}
const reader=new FileReader();
reader.onload=(e)=>{{
photos.push({{data:e.target.result,name:f.name}});
renderThumbs();
if(photos.length>=2)showSteps();
}};
reader.readAsDataURL(f);
}}
}}

function renderThumbs(){{
const container=document.getElementById("thumbs");
container.innerHTML="";
photos.forEach((p,i)=>{{
container.innerHTML+=`<div class="thumb"><img src="${{p.data}}"><div class="del" onclick="removePhoto(${{i}})">&times;</div></div>`;
}});
}}

function removePhoto(i){{photos.splice(i,1);renderThumbs();if(photos.length<2)hideSteps();}}

function showSteps(){{
document.getElementById("step2").classList.remove("hidden");
document.getElementById("step3").classList.remove("hidden");
document.getElementById("step4").classList.remove("hidden");
}}

function hideSteps(){{
document.getElementById("step2").classList.add("hidden");
document.getElementById("step3").classList.add("hidden");
document.getElementById("step4").classList.add("hidden");
}}

function setPos(p){{textPos=p;document.querySelectorAll("[id^=pos-]").forEach(b=>b.classList.remove("active"));document.getElementById("pos-"+p).classList.add("active");}}
function setSize(s){{textSize=s;document.querySelectorAll("[id^=sz-]").forEach(b=>b.classList.remove("active"));document.getElementById("sz-"+s).classList.add("active");}}

async function generateVideo(){{
const btn=document.getElementById("genBtn");
btn.disabled=true;btn.textContent="Generating...";
document.getElementById("progressWrap").classList.remove("hidden");
document.getElementById("statusText").textContent="Creating canvas frames...";

textOverlay=document.getElementById("textInput").value;

const W=1280,H=720,FPS=30,SLIDE_SEC=3,TRANS_SEC=0.5;
const totalFrames=photos.length*SLIDE_SEC*FPS;
const canvas=document.createElement("canvas");
canvas.width=W;canvas.height=H;
const ctx=canvas.getContext("2d");

// Load images
const imgs=[];
for(let p of photos){{
const img=new Image();
img.src=p.data;
await new Promise(r=>{{img.onload=r;}});
imgs.push(img);
}}

// Generate frames as blob array
const frames=[];
let frameCount=0;

for(let i=0;i<imgs.length;i++){{
const slideFrames=SLIDE_SEC*FPS;
const transFrames=TRANS_SEC*FPS;

for(let f=0;f<slideFrames;f++){{
ctx.fillStyle="#000";ctx.fillRect(0,0,W,H);

// Draw current image (cover fit)
drawCover(ctx,imgs[i],W,H);

// Transition: fade in from previous at start
if(i>0&&f<transFrames){{
const alpha=f/transFrames;
ctx.globalAlpha=1-alpha;
drawCover(ctx,imgs[i-1],W,H);
ctx.globalAlpha=1;
// Redraw current with alpha
ctx.globalAlpha=alpha;
drawCover(ctx,imgs[i],W,H);
ctx.globalAlpha=1;
}}

// Text overlay
if(textOverlay){{
const fontSize=textSize==="small"?28:textSize==="large"?52:38;
ctx.font=`bold ${{fontSize}}px Inter,sans-serif`;
ctx.textAlign="center";
ctx.fillStyle="#fff";
ctx.shadowColor="rgba(0,0,0,.7)";ctx.shadowBlur=8;
let y=textPos==="top"?80:textPos==="bottom"?H-40:H/2;
ctx.fillText(textOverlay,W/2,y);
ctx.shadowBlur=0;
}}

frames.push(canvas.toDataURL("image/jpeg",0.8));
frameCount++;
const pct=Math.round(frameCount/totalFrames*70);
document.getElementById("progressBar").style.width=pct+"%";
// Yield to prevent freezing
if(frameCount%10===0)await new Promise(r=>setTimeout(r,0));
}}
}}

document.getElementById("statusText").textContent="Encoding video... (this may take a moment)";
document.getElementById("progressBar").style.width="75%";

// Use canvas captureStream + MediaRecorder for video encoding
const stream=canvas.captureStream(FPS);

// Add audio
let audioStream=null;
try{{
const audioCtx=new AudioContext();
const audioResp=await fetch(MUSIC_TRACKS[selectedMusic].url);
const audioBuffer=await audioCtx.decodeAudioData(await audioResp.arrayBuffer());
const source=audioCtx.createBufferSource();
source.buffer=audioBuffer;
source.loop=true;
const dest=audioCtx.createMediaStreamDestination();
source.connect(dest);
source.start();
audioStream=dest.stream;
stream.addTrack(audioStream.getAudioTracks()[0]);
}}catch(e){{console.log("Audio failed, continuing without:",e);}}

const recorder=new MediaRecorder(stream,{{mimeType:"video/webm;codecs=vp9",videoBitsPerSecond:2500000}});
const chunks=[];
recorder.ondataavailable=(e)=>{{if(e.data.size>0)chunks.push(e.data);}};

recorder.start();

// Play back frames to canvas
for(let i=0;i<frames.length;i++){{
const img=new Image();
img.src=frames[i];
await new Promise(r=>{{img.onload=r;}});
ctx.drawImage(img,0,0);
const pct=75+Math.round(i/frames.length*20);
document.getElementById("progressBar").style.width=pct+"%";
await new Promise(r=>setTimeout(r,1000/FPS));
}}

recorder.stop();
await new Promise(r=>{{recorder.onstop=r;}});

document.getElementById("progressBar").style.width="100%";
document.getElementById("statusText").textContent="Done!";

videoBlob=new Blob(chunks,{{type:"video/webm"}});
videoUrl=URL.createObjectURL(videoBlob);

// Show result
document.getElementById("step1").classList.add("hidden");
document.getElementById("step2").classList.add("hidden");
document.getElementById("step3").classList.add("hidden");
document.getElementById("step4").classList.add("hidden");
document.getElementById("step5").classList.remove("hidden");
document.getElementById("resultVideo").src=videoUrl;

// Free frame memory
frames.length=0;
}}

function drawCover(ctx,img,W,H){{
const ratio=Math.max(W/img.width,H/img.height);
const w=img.width*ratio,h=img.height*ratio;
ctx.drawImage(img,(W-w)/2,(H-h)/2,w,h);
}}

function downloadVideo(){{
const a=document.createElement("a");
a.href=videoUrl;
a.download="{business_name.replace(" ","_")}_promo.webm";
a.click();
}}

function resetAll(){{
// Cleanup
if(videoUrl)URL.revokeObjectURL(videoUrl);
videoBlob=null;videoUrl=null;photos=[];
document.getElementById("thumbs").innerHTML="";
document.getElementById("textInput").value="";
document.getElementById("step1").classList.remove("hidden");
document.getElementById("step2").classList.add("hidden");
document.getElementById("step3").classList.add("hidden");
document.getElementById("step4").classList.add("hidden");
document.getElementById("step5").classList.add("hidden");
document.getElementById("genBtn").disabled=false;
document.getElementById("genBtn").textContent="\U0001f3ac Create Video";
document.getElementById("progressWrap").classList.add("hidden");
document.getElementById("progressBar").style.width="0%";
document.getElementById("statusText").textContent="";
if(audioEl){{audioEl.pause();audioEl=null;}}
}}

initMusic();
</script><div id="toolModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;align-items:center;justify-content:center;padding:10px"><div style="background:#fff;border-radius:16px;width:100%;max-width:480px;height:85vh;position:relative;overflow:hidden"><button onclick="closeTool()" style="position:absolute;top:8px;right:12px;background:rgba(0,0,0,.6);color:#fff;border:none;width:28px;height:28px;border-radius:50%;font-size:1rem;cursor:pointer;z-index:10">&times;</button><iframe id="toolFrame" style="width:100%;height:100%;border:none;border-radius:16px" src=""></iframe></div></div></body></html>'''
    return HTMLResponse(content=html)

@router.get("/{website_id}/ai-video", response_class=HTMLResponse)
def ai_video_page(website_id: str):
    """Video Creator - generates 20-sec video with script and branding."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    html = f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{business_name} - Video Creator</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}input,select,textarea{{font-size:16px!important}}
body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:500px;margin:0 auto}}
h1{{font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px}}
.sub{{font-size:.72rem;color:#64748b;text-align:center;margin-bottom:20px}}
.card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:12px}}
.card h2{{font-size:.82rem;font-weight:700;margin-bottom:8px}}
.card p{{font-size:.7rem;color:#64748b;margin-bottom:10px}}
textarea,.text-input{{width:100%;padding:10px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#fff;font-size:.8rem;outline:none}}
textarea{{resize:none;min-height:100px}}
.gen-btn{{width:100%;padding:14px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.88rem;cursor:pointer;margin-top:12px}}
.gen-btn:disabled{{opacity:.5;cursor:not-allowed}}
.script-btn{{width:100%;padding:10px;background:#334155;color:#fff;border:none;border-radius:8px;font-weight:600;font-size:.8rem;cursor:pointer;margin-bottom:10px}}
.script-btn:hover{{background:#475569}}
.status{{text-align:center;padding:16px;font-size:.78rem;color:#94a3b8}}
.result{{text-align:center;margin-top:12px}}
.result video{{width:100%;border-radius:10px;margin-bottom:10px}}
.dl-btn{{display:inline-block;padding:10px 20px;background:#22c55e;color:#fff;border-radius:8px;font-weight:700;font-size:.8rem;text-decoration:none}}
.script-preview{{background:#0f172a;border:1px solid #334155;border-radius:8px;padding:10px;margin-top:10px;font-size:.68rem;color:#94a3b8;white-space:pre-wrap;display:none;max-height:120px;overflow-y:auto}}
.note{{font-size:.6rem;color:#475569;text-align:center;margin-top:12px}}
</style></head><body>
<h1>&#127916; Video Creator</h1>
<p class="sub">{business_name} - Create a 20-second promotional video</p>

<div class="card">
<h2>Step 1: Video Script</h2>
<p>Add keywords or a brief idea. We will generate a full 4-scene script for your video.</p>
<textarea id="blurb" placeholder="e.g., festive sale, new collection arrived, grand opening, best services in town..."></textarea>
<button class="script-btn" id="scriptBtn" onclick="generateScript()">&#9998; Generate Video Script</button>
<div class="script-preview" id="scriptPreview"></div>
</div>

<div class="card">
<h2>Step 2: Text on Video</h2>
<p>This text will appear on your video along with your business name.</p>
<input type="text" class="text-input" id="customText" placeholder="e.g., 50% OFF This Week! | Call Now" maxlength="60">
<p style="margin-top:6px;font-size:.6rem;color:#475569">Business name &amp; website will be added automatically</p>
</div>

<button class="gen-btn" id="genBtn" onclick="generateVideo()" disabled>&#127916; Generate 20-sec Video</button>

<div id="status" class="status" style="display:none"></div>
<div id="result" class="result" style="display:none"></div>

<p class="note">Creates a 20-second video (4 scenes x 5 sec). May take 3-5 minutes.</p>

<script>
var generatedScript = '';

async function generateScript(){{
  var blurb = document.getElementById('blurb').value.trim();
  if(!blurb) blurb = '{category} business promotional video';
  var btn = document.getElementById('scriptBtn');
  var preview = document.getElementById('scriptPreview');
  btn.disabled = true; btn.textContent = 'Generating script...';
  preview.style.display = 'none';
  try{{
    var r = await fetch('/api/video/{website_id}/generate-script', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{blurb: blurb, business_name: '{business_name}', category: '{category}'}})
    }});
    var data = await r.json();
    if(data.script){{
      generatedScript = data.script.join(String.fromCharCode(10));
      preview.style.display = 'block';
      preview.innerHTML = '<b style="color:#fff;font-size:.75rem">Video Script (4 scenes):</b><br><br>' + data.script.map(function(s,i){{return '<b style="color:#00e5ff">Scene '+(i+1)+':</b> '+s}}).join('<br><br>');
      document.getElementById('genBtn').disabled = false;
    }}
  }}catch(e){{
    preview.style.display = 'block';
    preview.textContent = 'Failed to generate script. Try again.';
  }}
  btn.disabled = false; btn.textContent = '\u270e Generate Video Script';
}}

async function generateVideo(){{
  var btn = document.getElementById('genBtn');
  var status = document.getElementById('status');
  var result = document.getElementById('result');
  var customText = document.getElementById('customText').value.trim();
  btn.disabled = true; btn.textContent = 'Creating video...';
  status.style.display = 'none';
  var popup = document.createElement('div');
  popup.id='genPopup';
  popup.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:9999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(6px)';
  popup.innerHTML='<div style="background:#1e293b;border:1px solid #334155;border-radius:16px;padding:28px;text-align:center;max-width:300px;width:90%"><div style="width:40px;height:40px;border:3px solid rgba(99,102,241,.2);border-top:3px solid #6366f1;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 14px"></div><p style="font-size:.85rem;font-weight:700;color:#fff;margin-bottom:6px">Generating Video</p><p id="genMsg" style="font-size:.7rem;color:#94a3b8">Creating 4 scenes... (3-5 min)</p><style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style></div>';
  document.body.appendChild(popup);
  result.style.display = 'none';
  try{{
    var r = await fetch('/api/video/{website_id}/generate-free', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{prompt: generatedScript || document.getElementById('blurb').value, custom_text: customText}})
    }});
    var data = await r.json();
    if(data.status === 'completed'){{
      result.style.display = 'block';
      var bname=data.business_name||'';var surl=data.site_url||'';var ctxt=data.custom_text||'';
      var gp=document.getElementById('genPopup');if(gp)gp.remove();
      if(data.video_url){{
        result.innerHTML='<div style="position:relative;width:100%;border-radius:10px;overflow:hidden;margin-bottom:10px"><video src="'+data.video_url+'" controls autoplay playsinline style="width:100%;display:block;border-radius:10px"></video></div><p style="font-size:.72rem;color:#94a3b8;text-align:center;margin:8px 0">'+(data.total_duration||'20 seconds')+' | '+(data.total_clips||4)+' scenes stitched</p><a href="'+data.video_url+'" download style="display:block;text-align:center;padding:10px 20px;background:#22c55e;border-radius:8px;color:#fff;font-weight:700;font-size:.8rem;text-decoration:none;max-width:200px;margin:0 auto">Download Video</a>';
      }}else if(data.clips && data.clips.length > 0){{var clips=data.clips;
      var gp=document.getElementById('genPopup');if(gp)gp.remove();
      var vh='<div style="position:relative;width:100%;border-radius:10px;overflow:hidden;margin-bottom:10px;background:#000">';
      vh+='<video id="mainVid" playsinline autoplay style="width:100%;display:block;border-radius:10px"></video>';
      vh+='<div style="position:absolute;top:0;left:0;right:0;padding:8px 12px;background:linear-gradient(180deg,rgba(0,0,0,.6),transparent);color:#fff;font-size:.8rem;font-weight:700">'+(ctxt||bname)+'</div>';
      vh+='<div style="position:absolute;bottom:0;left:0;right:0;padding:8px;background:linear-gradient(0deg,rgba(0,0,0,.6),transparent);text-align:center;color:#fff;font-size:.65rem;font-weight:600">'+surl+'</div>';
      vh+='</div>';
      vh+='<p id="clipStatus" style="font-size:.72rem;color:#94a3b8;text-align:center;margin:8px 0">Playing clip 1/'+clips.length+' ('+data.total_duration+' total)</p>';
      vh+='<div style="display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin:10px 0">';
      for(var ci=0;ci<clips.length;ci++){{vh+='<a href="'+clips[ci]+'" download="clip_'+(ci+1)+'.mp4" style="padding:6px 12px;background:#22c55e;border-radius:6px;color:#fff;font-size:.7rem;font-weight:600;text-decoration:none">Download Clip '+(ci+1)+'</a>';}}
      vh+='</div>';
      result.innerHTML=vh;
      var vid=document.getElementById('mainVid');var cc=0;
      vid.src=clips[0];
      vid.onended=function(){{cc++;if(cc<clips.length){{vid.src=clips[cc];vid.play();document.getElementById('clipStatus').textContent='Playing clip '+(cc+1)+'/'+clips.length;}}else{{document.getElementById('clipStatus').innerHTML='<span style="color:#22c55e">All clips played!</span> Download clips above.';}}}};}}
      status.style.display = 'none';
    }}else if(data.status === 'loading' || data.status === 'timeout'){{var gp2=document.getElementById('genPopup');if(gp2)gp2.remove();
      status.innerHTML = '<p>&#9203; '+(data.message||'Model is loading. Try again in 2 min.')+'</p>';
    }}else{{
      var gp3=document.getElementById('genPopup');if(gp3)gp3.remove();status.style.display='block';status.innerHTML = '<p style="color:#ef4444">'+(data.message||data.detail||'Generation failed. Try again.')+'</p>';
    }}
  }}catch(e){{
    status.innerHTML = '<p style="color:#ef4444">Error: '+e.message+'</p>';
  }}
  btn.disabled = false; btn.textContent = '\U0001f3ac Generate 20-sec Video';
}}
</script>
</body></html>"""
    return HTMLResponse(content=html)

