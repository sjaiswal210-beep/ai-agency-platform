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
async def preview_social_post(website_id: str, platform: str = "instagram", purpose: str = "promotion"):
    """Preview a social media post as rendered HTML."""
    post = await generate_social_post(website_id, SocialPostRequest(platform=platform, purpose=purpose))

    w = post["size"]["w"]
    h = post["size"]["h"]
    primary = post["colors"].get("primary", "#6366f1")
    accent = post["colors"].get("accent", "#10b981")
    scale = min(500 / w, 700 / h)

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Social Post Preview</title>
<style>
body{{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#1e293b;font-family:Inter,sans-serif;margin:0}}
.container{{text-align:center}}
.post{{width:{int(w*scale)}px;height:{int(h*scale)}px;background:linear-gradient(135deg,{primary},{accent});border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;color:#fff;position:relative;overflow:hidden;box-shadow:0 20px 40px rgba(0,0,0,.3)}}
.post::before{{content:'';position:absolute;top:-50%;right:-50%;width:100%;height:100%;background:radial-gradient(circle,rgba(255,255,255,.1),transparent);border-radius:50%}}
.post h1{{font-size:{int(28*scale)}px;font-weight:900;margin-bottom:12px;position:relative;text-align:center;line-height:1.2}}
.post p{{font-size:{int(16*scale)}px;opacity:.9;position:relative;text-align:center;margin-bottom:16px}}
.post .offer{{background:rgba(255,255,255,.2);padding:8px 20px;border-radius:50px;font-weight:700;font-size:{int(14*scale)}px;position:relative}}
.post .brand{{position:absolute;bottom:20px;font-size:{int(12*scale)}px;opacity:.7}}
.caption{{color:#94a3b8;font-size:13px;max-width:400px;margin:20px auto 0;text-align:left;background:#0f172a;padding:16px;border-radius:8px;line-height:1.6}}
.hashtags{{color:#60a5fa;font-size:12px;margin-top:8px}}
</style></head><body>
<div class="container">
<div class="post">
<h1>{post.get('headline','')}</h1>
<p>{post.get('subtext','')}</p>
{'<div class="offer">' + post.get('offer','') + '</div>' if post.get('offer') else ''}
<div class="brand">{post['business_name']} | {post.get('phone','')}</div>
</div>
<div class="caption">{post.get('caption','')}<div class="hashtags">{' '.join(['#'+h for h in post.get('hashtags',[])])}</div></div>
</div></body></html>"""
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