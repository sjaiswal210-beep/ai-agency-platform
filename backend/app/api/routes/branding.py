from __future__ import annotations
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
from app.core.logging import get_logger

router = APIRouter(prefix="/branding", tags=["branding"])
logger = get_logger(__name__)


class LogoRequest(BaseModel):
    style: str = "modern"  # modern, minimal, bold, elegant, playful


class SocialPostRequest(BaseModel):
    platform: str = "instagram"  # instagram, facebook, whatsapp_status
    purpose: str = "promotion"  # promotion, announcement, offer, testimonial


@router.post("/{website_id}/logo")
async def generate_logo(website_id: str, req: LogoRequest):
    """Generate an SVG logo for the business."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    content = website.get("content", {})
    if "raw_content" in content:
        raw = content["raw_content"]
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        try:
            content = json.loads(raw)
        except json.JSONDecodeError:
            pass

    colors = content.get("color_scheme", {"primary": "#6366f1", "secondary": "#e0e7ff"})
    primary = colors.get("primary", "#6366f1")

    prompt = f"""Create an SVG logo for this business:
- Business Name: {business_name}
- Category: {category}
- Style: {req.style}
- Primary Color: {primary}

Generate a professional SVG logo. Requirements:
- Must be valid SVG code (starting with <svg and ending with </svg>)
- Size: viewBox="0 0 200 60" for horizontal, or "0 0 100 100" for icon-only
- Use the primary color {primary} as main color
- Include the business name as text in the logo
- Add a simple icon/shape relevant to {category}
- Style: {req.style} (modern=clean lines, minimal=simple, bold=thick, elegant=thin serif, playful=rounded)
- Use only basic SVG elements: rect, circle, path, text, polygon, line
- No external images or links

Return ONLY the SVG code, nothing else."""

    result = await chat_completion([{"role": "user", "content": prompt}])

    # Extract SVG from response
    svg = result.strip()
    if "```svg" in svg:
        svg = svg.split("```svg")[1].split("```")[0].strip()
    elif "```xml" in svg:
        svg = svg.split("```xml")[1].split("```")[0].strip()
    elif "```" in svg:
        svg = svg.split("```")[1].split("```")[0].strip()

    # Ensure it starts with <svg
    if not svg.startswith("<svg"):
        svg_start = svg.find("<svg")
        if svg_start >= 0:
            svg = svg[svg_start:]
        else:
            svg = f'<svg viewBox="0 0 200 60" xmlns="http://www.w3.org/2000/svg"><rect width="200" height="60" rx="8" fill="{primary}"/><text x="100" y="38" text-anchor="middle" fill="white" font-size="20" font-weight="bold" font-family="Arial">{business_name}</text></svg>'

    return {"svg": svg, "business_name": business_name}


@router.get("/{website_id}/logo/preview", response_class=HTMLResponse)
async def preview_logo(website_id: str, style: str = "modern"):
    """Preview the generated logo as HTML."""
    from pydantic import BaseModel
    result = await generate_logo(website_id, LogoRequest(style=style))
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Logo Preview</title>
    <style>body{{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f8fafc;font-family:Inter,sans-serif}}
    .container{{text-align:center}}.logo-box{{background:#fff;padding:40px;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,.08);margin-bottom:20px}}
    .variants{{display:flex;gap:20px;justify-content:center;margin-top:20px}}.variant{{background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.05)}}
    .dark{{background:#1e293b}}</style></head>
    <body><div class="container"><div class="logo-box">{result['svg']}</div>
    <div class="variants"><div class="variant dark">{result['svg']}</div></div>
    <p style="color:#64748b;margin-top:16px;font-size:14px">{result['business_name']} - Logo Preview</p></div></body></html>"""
    return HTMLResponse(content=html)


@router.post("/{website_id}/social-post")
async def generate_social_post(website_id: str, req: SocialPostRequest):
    """Generate a social media post design as HTML/CSS."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    phone = lead.get("phone", "") if lead else ""

    content = website.get("content", {})
    if "raw_content" in content:
        raw = content["raw_content"]
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        try:
            content = json.loads(raw)
        except json.JSONDecodeError:
            pass

    colors = content.get("color_scheme", {"primary": "#6366f1", "secondary": "#e0e7ff", "accent": "#10b981"})
    primary = colors.get("primary", "#6366f1")
    accent = colors.get("accent", "#10b981")
    services = content.get("services", [])
    hero_title = content.get("hero_title", business_name)

    size_map = {
        "instagram": {"w": 1080, "h": 1080, "label": "Instagram Post (1080x1080)"},
        "facebook": {"w": 1200, "h": 630, "label": "Facebook Post (1200x630)"},
        "whatsapp_status": {"w": 1080, "h": 1920, "label": "WhatsApp Status (1080x1920)"},
    }
    size = size_map.get(req.platform, size_map["instagram"])

    prompt = f"""Create social media post content for:
- Business: {business_name}
- Category: {category}
- Platform: {req.platform} ({size['label']})
- Purpose: {req.purpose}
- Phone: {phone}
- Services: {', '.join([s.get('name','') for s in services[:4]])}

Generate JSON with:
{{
    "headline": "Bold attention-grabbing text (max 6 words)",
    "subtext": "Supporting text (1 sentence)",
    "offer": "Special offer or CTA text (if purpose is offer/promotion)",
    "hashtags": ["relevant", "hashtags", "for", "this", "business"],
    "caption": "Ready-to-post caption for {req.platform} (2-3 sentences with emojis)"
}}

Return ONLY valid JSON."""

    result = await chat_completion([{"role": "user", "content": prompt}])

    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        post_data = json.loads(cleaned)
    except json.JSONDecodeError:
        post_data = {"headline": business_name, "subtext": f"Visit us today!", "offer": "", "hashtags": [category], "caption": f"Visit {business_name} today!"}

    post_data["platform"] = req.platform
    post_data["size"] = size
    post_data["colors"] = colors
    post_data["business_name"] = business_name
    post_data["phone"] = phone

    return post_data


@router.get("/{website_id}/social-post/preview", response_class=HTMLResponse)
def social_post_preview(website_id: str, platform: str = "instagram", purpose: str = "promotion"):
    """Generate a beautiful social media post with background image + download option."""
    from app.services.website_service import WebsiteService
    from app.services.lead_service import LeadService
    import urllib.parse

    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    phone = lead.get("phone", "") if lead else ""
    slug = website.get("slug", "")
    site_url = f"city-maps.online/{slug}" if slug else ""

    content = website.get("content", {})
    colors = content.get("color_scheme", {})
    primary = colors.get("primary", "#7C3AED")
    
    # Get relevant background image
    bg_img = f"https://source.unsplash.com/1080x1080/?{category},business"
    
    # Generate content based on purpose
    taglines = {
        "promotion": f"Visit us today! Best {category} services in town.",
        "offer": f"Special offer! Limited time deal at {business_name}.",
        "festive": f"Celebrate with {business_name}! Festive special offers.",
        "new": f"Something new at {business_name}! Come check it out.",
    }
    tagline = taglines.get(purpose, taglines["promotion"])

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Social Post - {business_name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:#1e293b;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}}
.post-container{{position:relative;width:100%;max-width:540px}}
.post{{width:100%;aspect-ratio:1;border-radius:16px;overflow:hidden;position:relative;background:url('{bg_img}') center/cover;box-shadow:0 20px 50px rgba(0,0,0,.3)}}
.post-overlay{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.2) 0%,rgba(0,0,0,.7) 100%);display:flex;flex-direction:column;justify-content:flex-end;padding:40px}}
.post-brand{{position:absolute;top:20px;left:20px;background:rgba(255,255,255,.95);padding:8px 16px;border-radius:50px;font-weight:800;font-size:.85rem;color:{primary}}}
.post-badge{{position:absolute;top:20px;right:20px;background:{primary};color:#fff;padding:6px 12px;border-radius:50px;font-size:.7rem;font-weight:700}}
.post-content h2{{color:#fff;font-size:1.8rem;font-weight:800;margin-bottom:12px;text-shadow:0 2px 10px rgba(0,0,0,.5)}}
.post-content p{{color:rgba(255,255,255,.9);font-size:1rem;margin-bottom:16px}}
.post-footer{{display:flex;justify-content:space-between;align-items:center}}
.post-url{{color:rgba(255,255,255,.8);font-size:.8rem;background:rgba(255,255,255,.15);padding:6px 12px;border-radius:50px}}
.post-cta{{background:#fff;color:{primary};padding:8px 16px;border-radius:50px;font-weight:700;font-size:.8rem}}
.controls{{margin-top:20px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}}
.controls select,.controls input{{padding:10px 14px;border-radius:8px;border:1px solid #475569;background:#334155;color:#fff;font-size:.85rem}}
.controls button{{padding:10px 20px;border-radius:8px;border:none;background:#7c3aed;color:#fff;font-weight:700;cursor:pointer;font-size:.85rem}}
.controls button:hover{{background:#6d28d9}}
.download-btn{{background:#059669!important}}.download-btn:hover{{background:#047857!important}}
.tip{{color:#94a3b8;font-size:.75rem;margin-top:12px;text-align:center}}
</style></head><body>
<div class="post-container">
<div class="post" id="socialPost">
<div class="post-overlay">
<div class="post-brand">{business_name}</div>
<div class="post-badge">{platform.upper()}</div>
<div class="post-content">
<h2 id="postText">{tagline}</h2>
<p id="postSub">\U0001f4cd {site_url} | \U0001f4de {phone}</p>
<div class="post-footer">
<span class="post-url">{site_url}</span>
<span class="post-cta">Visit Now \u2192</span>
</div>
</div>
</div>
</div>
</div>
<div class="controls">
<select onchange="changePurpose(this.value)">
<option value="promotion">Promotion</option>
<option value="offer">Special Offer</option>
<option value="festive">Festive</option>
<option value="new">New Arrival</option>
</select>
<input type="text" id="customText" placeholder="Custom text..." style="flex:1;min-width:150px">
<button onclick="applyCustom()">Apply</button>
<button class="download-btn" onclick="downloadPost()">\u2b07 Download</button>
</div>
<p class="tip">Right-click the image to save, or use the Download button. Works best on desktop.</p>
<script>
function changePurpose(p){{
const texts={{promotion:"Visit us today! Best {category} services in town.",offer:"Special offer! Limited time deal at {business_name}.",festive:"Celebrate with {business_name}! Festive special offers.",new:"Something new at {business_name}! Come check it out."}};
document.getElementById('postText').textContent=texts[p]||texts.promotion;
}}
function applyCustom(){{
const t=document.getElementById('customText').value;
if(t)document.getElementById('postText').textContent=t;
}}
function downloadPost(){{
const el=document.getElementById('socialPost');
// Use html2canvas if available, otherwise prompt screenshot
const s=document.createElement('script');
s.src='https://html2canvas.hertzen.com/dist/html2canvas.min.js';
s.onload=function(){{
html2canvas(el,{{useCORS:true,scale:2}}).then(canvas=>{{
const a=document.createElement('a');
a.download='{business_name.replace(" ","-")}-post.png';
a.href=canvas.toDataURL();
a.click();
}});
}};
document.head.appendChild(s);
}}
</script>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/{website_id}/photos")
async def get_photos(website_id: str):
    """Fetch real photos of the business from Google Maps."""
    from app.services.photos_service import get_business_photos
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")
    photos = await get_business_photos(lead.get("business_name", ""), lead.get("address", ""))
    return {"photos": photos, "count": len(photos), "business": lead.get("business_name")}