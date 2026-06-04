from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
from app.core.logging import get_logger
import json

router = APIRouter(prefix="/creatives", tags=["creatives"])
logger = get_logger(__name__)


class CreativeRequest(BaseModel):
    type: str = "offer"  # offer, testimonial, announcement, tips, festival, before_after
    platform: str = "instagram"  # instagram, facebook, whatsapp, story
    custom_text: str = ""


SIZES = {
    "instagram": {"w": 1080, "h": 1080, "label": "Instagram Post"},
    "facebook": {"w": 1200, "h": 630, "label": "Facebook Post"},
    "whatsapp": {"w": 800, "h": 800, "label": "WhatsApp Status"},
    "story": {"w": 1080, "h": 1920, "label": "Story/Reel Cover"},
}


@router.get("/{website_id}/templates")
def get_templates(website_id: str):
    """Get available creative templates for a business."""
    return {
        "templates": [
            {"id": "offer", "name": "Special Offer", "icon": "🎉", "desc": "Discount/deal announcement"},
            {"id": "testimonial", "name": "Customer Review", "icon": "⭐", "desc": "Showcase a happy customer"},
            {"id": "announcement", "name": "Announcement", "icon": "📢", "desc": "New service/update"},
            {"id": "tips", "name": "Tips & Education", "icon": "💡", "desc": "Share expertise"},
            {"id": "festival", "name": "Festival Greeting", "icon": "🪔", "desc": "Festive wishes"},
            {"id": "before_after", "name": "Before & After", "icon": "✨", "desc": "Transformation showcase"},
            {"id": "hiring", "name": "We're Hiring", "icon": "👥", "desc": "Job opening post"},
            {"id": "milestone", "name": "Milestone", "icon": "🏆", "desc": "Achievement celebration"},
        ],
        "platforms": [
            {"id": "instagram", "name": "Instagram Post (1080x1080)"},
            {"id": "facebook", "name": "Facebook Post (1200x630)"},
            {"id": "whatsapp", "name": "WhatsApp (800x800)"},
            {"id": "story", "name": "Story/Reel (1080x1920)"},
        ]
    }


@router.post("/{website_id}/generate", response_class=HTMLResponse)
async def generate_creative(website_id: str, req: CreativeRequest):
    """Generate a visual ad creative as downloadable HTML."""
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

    # Generate creative content with AI
    prompt = f"""Generate social media ad creative content for:
Business: {business_name}
Category: {category}
Type: {req.type}
Platform: {req.platform}
{f'Custom instruction: {req.custom_text}' if req.custom_text else ''}

Return JSON:
{{
    "headline": "Bold text (max 5 words)",
    "subtext": "Supporting line (max 10 words)",
    "offer_text": "Offer/CTA detail if applicable",
    "footer_text": "Business name or tagline",
    "caption": "Ready-to-post caption with emojis and hashtags (3-4 lines)"
}}
Return ONLY JSON."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        data = {"headline": business_name, "subtext": "Visit us today", "offer_text": "", "footer_text": business_name, "caption": ""}

    size = SIZES.get(req.platform, SIZES["instagram"])
    w = size["w"]
    h = size["h"]

    # Design variations based on type
    designs = {
        "offer": {"bg": f"linear-gradient(135deg, {primary}, {primary}dd)", "badge": "LIMITED OFFER", "badge_color": "#ef4444"},
        "testimonial": {"bg": f"linear-gradient(135deg, #1e293b, #334155)", "badge": "CUSTOMER LOVE", "badge_color": accent},
        "announcement": {"bg": f"linear-gradient(135deg, {primary}, {accent})", "badge": "NEW", "badge_color": "#f59e0b"},
        "tips": {"bg": f"linear-gradient(135deg, #0f172a, #1e293b)", "badge": "PRO TIP", "badge_color": primary},
        "festival": {"bg": f"linear-gradient(135deg, #f59e0b, #ef4444)", "badge": "", "badge_color": ""},
        "before_after": {"bg": f"linear-gradient(135deg, {primary}, #1e293b)", "badge": "TRANSFORMATION", "badge_color": accent},
        "hiring": {"bg": f"linear-gradient(135deg, #059669, #10b981)", "badge": "WE'RE HIRING", "badge_color": "#f59e0b"},
        "milestone": {"bg": f"linear-gradient(135deg, #f59e0b, {primary})", "badge": "MILESTONE", "badge_color": "#fff"},
    }
    design = designs.get(req.type, designs["offer"])

    headline = data.get("headline", business_name)
    subtext = data.get("subtext", "")
    offer_text = data.get("offer_text", "")
    footer_text = data.get("footer_text", business_name)
    caption = data.get("caption", "")

    # Scale for display
    scale = min(600 / w, 800 / h)
    dw = int(w * scale)
    dh = int(h * scale)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Creative - {business_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:#0f172a;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Inter,sans-serif;padding:20px;gap:20px}}
.creative{{width:{dw}px;height:{dh}px;background:{design['bg']};border-radius:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px;color:#fff;position:relative;overflow:hidden;box-shadow:0 25px 60px rgba(0,0,0,.4)}}
.creative::before{{content:'';position:absolute;top:-30%;right:-30%;width:60%;height:60%;background:radial-gradient(circle,rgba(255,255,255,.08),transparent);border-radius:50%}}
.creative::after{{content:'';position:absolute;bottom:-20%;left:-20%;width:50%;height:50%;background:radial-gradient(circle,rgba(255,255,255,.05),transparent);border-radius:50%}}
.badge{{position:absolute;top:24px;left:24px;background:{design['badge_color']};padding:6px 14px;border-radius:6px;font-size:11px;font-weight:700;letter-spacing:1.5px;z-index:1}}
.logo{{position:absolute;top:24px;right:24px;width:44px;height:44px;background:rgba(255,255,255,.15);border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;backdrop-filter:blur(4px);z-index:1}}
.content{{position:relative;z-index:1;text-align:center;max-width:85%}}
.headline{{font-size:{int(36*scale)}px;font-weight:900;line-height:1.1;margin-bottom:12px;text-shadow:0 2px 10px rgba(0,0,0,.3)}}
.subtext{{font-size:{int(18*scale)}px;opacity:.85;margin-bottom:20px;font-weight:500}}
.offer{{background:rgba(255,255,255,.15);backdrop-filter:blur(4px);padding:12px 24px;border-radius:10px;font-size:{int(16*scale)}px;font-weight:700;border:1px solid rgba(255,255,255,.2)}}
.footer{{position:absolute;bottom:24px;font-size:13px;opacity:.7;z-index:1;display:flex;align-items:center;gap:8px}}
.footer-dot{{width:6px;height:6px;background:#fff;border-radius:50%;opacity:.5}}
.caption-box{{background:#1e293b;border-radius:12px;padding:20px;max-width:{dw}px;width:100%;color:#94a3b8;font-size:13px;line-height:1.7}}
.caption-box .label{{color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.caption-box .text{{color:#e2e8f0;white-space:pre-wrap}}
.actions{{display:flex;gap:12px}}
.actions button{{background:#6366f1;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer}}
.actions button:hover{{background:#4f46e5}}
.actions button.secondary{{background:#334155}}
</style></head><body>

<div class="creative" id="creative">
    {f'<div class="badge">{design["badge"]}</div>' if design["badge"] else ''}
    <div class="logo">{business_name[0]}</div>
    <div class="content">
        <div class="headline">{headline}</div>
        <div class="subtext">{subtext}</div>
        {f'<div class="offer">{offer_text}</div>' if offer_text else ''}
    </div>
    <div class="footer"><span class="footer-dot"></span>{footer_text}{f' | {phone}' if phone else ''}</div>
</div>

<div class="caption-box">
    <div class="label">Caption (copy & paste)</div>
    <div class="text" id="caption">{caption}</div>
</div>

<div class="actions">
    <button onclick="navigator.clipboard.writeText(document.getElementById('caption').textContent)">Copy Caption</button>
    <button class="secondary" onclick="window.print()">Save as Image</button>
</div>

</body></html>"""

    return HTMLResponse(content=html)
