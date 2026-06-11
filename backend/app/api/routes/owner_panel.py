from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.api.routes.toolkit import get_tools_for_category

router = APIRouter(prefix="/panel", tags=["owner-panel"])


@router.get("/{website_id}", response_class=HTMLResponse)
def owner_panel(website_id: str):
    """Business owner dashboard."""
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
    category = lead.get("category", "default") if lead else "default"
    phone = lead.get("phone", "") if lead else ""
    slug = website.get("slug", "")
    site_url = f"https://{slug}.city-maps.online" if slug else ""
    tools = get_tools_for_category(category)
    since_30d = (datetime.utcnow() - timedelta(days=30)).isoformat()
    try:
        views = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "page_view").gte("created_at", since_30d).execute()).count or 0
        calls = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "call_click").gte("created_at", since_30d).execute()).count or 0
        wa = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "whatsapp_click").gte("created_at", since_30d).execute()).count or 0
        leads_n = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "lead_form").gte("created_at", since_30d).execute()).count or 0
    except Exception:
        views = calls = wa = leads_n = 0
    tools_html = "".join(f'<button class="t-btn" onclick="runTool(\'{t["id"]}\',\'{t["name"]}\')"><span>{t["icon"]}</span><div><b>{t["name"]}</b><small>{t["desc"]}</small></div></button>' for t in tools)
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{business_name} Dashboard</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet"><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:"Plus Jakarta Sans",sans-serif;background:#f4f6f9;display:flex;min-height:100vh}}.side{{width:68px;background:#1a2332;display:flex;flex-direction:column;align-items:center;padding:14px 0;gap:6px;position:fixed;top:0;bottom:0}}.side .logo{{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:.85rem;margin-bottom:14px}}.side a{{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#64748b;font-size:1.1rem;text-decoration:none;transition:all .15s}}.side a:hover{{background:rgba(99,102,241,.12);color:#818cf8}}.mn{{margin-left:68px;flex:1;padding:20px;max-width:1000px}}.hd{{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}}.hd h1{{font-size:1.2rem;font-weight:800}}.hd .badge{{background:#eef2ff;color:#6366f1;padding:4px 12px;border-radius:16px;font-size:.72rem;font-weight:600}}.sg{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}}.sc{{background:#fff;border-radius:14px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.03)}}.sc .ic{{float:right;width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1rem}}.sc .lb{{font-size:.7rem;color:#94a3b8;margin-bottom:3px}}.sc .vl{{font-size:1.4rem;font-weight:800}}.qg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:20px}}.ql{{background:#fff;border-radius:12px;padding:14px 10px;text-align:center;text-decoration:none;color:#475569;font-size:.72rem;font-weight:600;box-shadow:0 1px 3px rgba(0,0,0,.02);transition:all .15s;display:flex;flex-direction:column;align-items:center;gap:4px}}.ql:hover{{transform:translateY(-2px);box-shadow:0 4px 12px rgba(99,102,241,.08);color:#6366f1}}.ql .qi{{font-size:1.3rem}}.cd{{background:#fff;border-radius:14px;padding:18px;box-shadow:0 1px 4px rgba(0,0,0,.03);margin-bottom:14px}}.cd h3{{font-size:.85rem;font-weight:700;margin-bottom:12px}}.tg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px}}.t-btn{{background:#fff;border:1px solid #f1f5f9;border-radius:10px;padding:12px;display:flex;align-items:flex-start;gap:10px;cursor:pointer;text-align:left;width:100%;transition:all .15s}}.t-btn:hover{{border-color:#c7d2fe;box-shadow:0 3px 8px rgba(99,102,241,.05)}}.t-btn span{{font-size:1.2rem}}.t-btn b{{font-size:.78rem;display:block}}.t-btn small{{font-size:.66rem;color:#94a3b8}}.ob{{background:#fff;border-radius:14px;padding:18px;margin-top:14px;display:none}}.ob.show{{display:block}}.ob textarea{{width:100%;border:1px solid #e2e8f0;border-radius:8px;padding:8px;font-size:.8rem;resize:none;min-height:50px;margin-bottom:8px;font-family:inherit}}.ob button{{background:#6366f1;color:#fff;border:none;padding:8px 14px;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer}}.ob .res{{white-space:pre-wrap;font-size:.8rem;color:#475569;margin-top:10px;padding:10px;background:#f8fafc;border-radius:8px}}@media(max-width:640px){{.side{{display:none}}.mn{{margin-left:0;padding:14px}}.sg{{grid-template-columns:repeat(2,1fr)}}}}</style></head><body><aside class="side"><div class="logo">{business_name[0]}</div><a href="{site_url}" target="_blank">&#127760;</a><a href="https://city-maps.online/api/owner-analytics/{website_id}" target="_blank">&#128200;</a><a href="https://city-maps.online/api/store/{website_id}/manage" target="_blank">&#128722;</a><a href="https://city-maps.online/api/qr/{website_id}" target="_blank">&#128247;</a><a href="https://city-maps.online/api/daily/{website_id}" target="_blank">&#128197;</a></aside><main class="mn"><div class="hd"><h1>{business_name}</h1><a href="{site_url}" target="_blank" class="badge">{slug}.city-maps.online</a></div><div class="sg"><div class="sc"><div class="ic" style="background:#eef2ff;color:#6366f1">&#128065;</div><div class="lb">Views</div><div class="vl">{views}</div></div><div class="sc"><div class="ic" style="background:#fef3c7;color:#d97706">&#128222;</div><div class="lb">Calls</div><div class="vl">{calls}</div></div><div class="sc"><div class="ic" style="background:#dcfce7;color:#16a34a">&#128172;</div><div class="lb">WhatsApp</div><div class="vl">{wa}</div></div><div class="sc"><div class="ic" style="background:#fce7f3;color:#db2777">&#128203;</div><div class="lb">Leads</div><div class="vl">{leads_n}</div></div></div><div class="qg"><a href="{site_url}" target="_blank" class="ql"><span class="qi">&#127760;</span>Website</a><a href="https://city-maps.online/api/owner-analytics/{website_id}" target="_blank" class="ql"><span class="qi">&#128200;</span>Analytics</a><a href="https://city-maps.online/api/daily/{website_id}" target="_blank" class="ql"><span class="qi">&#128197;</span>Daily</a><a href="https://city-maps.online/api/store/{website_id}" target="_blank" class="ql"><span class="qi">&#128722;</span>Store</a><a href="https://city-maps.online/api/store/{website_id}/manage" target="_blank" class="ql"><span class="qi">&#128230;</span>Products</a><a href="https://city-maps.online/api/qr/{website_id}" target="_blank" class="ql"><span class="qi">&#128247;</span>QR Code</a><a href="https://city-maps.online/api/branding/{website_id}/social-post/preview" target="_blank" class="ql"><span class="qi">&#128248;</span>Social Post</a><a href="https://city-maps.online/api/video/{website_id}/prompt" target="_blank" class="ql"><span class="qi">&#127909;</span>Video Ideas</a><a href="https://city-maps.online/api/google-profile/{website_id}/setup-guide" target="_blank" class="ql"><span class="qi">&#128205;</span>Google</a></div><div class="cd"><h3>Business Tools</h3><div class="tg">{tools_html}</div></div><div class="ob" id="ob"><h3 id="oTitle">-</h3><textarea id="oCtx" placeholder="Add context..."></textarea><button onclick="gen()">Generate</button><div class="res" id="oRes"></div></div></main><script>let cT="",cN="";function runTool(id,nm){{cT=id;cN=nm;document.getElementById("ob").classList.add("show");document.getElementById("oTitle").textContent=nm;document.getElementById("oRes").textContent="";}}async function saveGallery(){const urls=document.getElementById("galUrls").value.split(String.fromCharCode(10)).filter(u=>u.trim());try{await fetch("https://city-maps.online/api/panel/{website_id}/gallery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({urls:urls})});alert("Gallery saved! "+urls.length+" photos added.");}catch{alert("Failed");}}
async function gen(){{const c=document.getElementById("oCtx").value;const r=document.getElementById("oRes");r.textContent="Generating...";try{{const res=await fetch("https://city-maps.online/api/toolkit/{website_id}/tools/run",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{tool_id:cT,context:c}})}});const d=await res.json();r.textContent=d.content||JSON.stringify(d);}}catch{{r.textContent="Error";}}}}</script></body></html>'''
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
def save_gallery(website_id: str, images: dict):
    """Save gallery image URLs."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    content = website.get("content", {}) or {}
    content["custom_gallery"] = images.get("urls", [])
    db.table("websites").update({"content": content}).eq("id", website_id).execute()
    return {"saved": True, "count": len(images.get("urls", []))}
