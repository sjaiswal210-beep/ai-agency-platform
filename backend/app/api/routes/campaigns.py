from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
import json

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

FESTIVALS = {
    "diwali": {"name": "Diwali", "emoji": "\U0001f386", "month": "October/November", "theme": "lights, prosperity, gifts, discounts"},
    "holi": {"name": "Holi", "emoji": "\U0001f3a8", "month": "March", "theme": "colors, joy, celebration, spring offers"},
    "navratri": {"name": "Navratri", "emoji": "\U0001f483", "month": "October", "theme": "festive, garba, new beginnings, special offers"},
    "christmas": {"name": "Christmas", "emoji": "\U0001f384", "month": "December", "theme": "gifts, celebration, year-end deals, joy"},
    "new_year": {"name": "New Year", "emoji": "\U0001f389", "month": "January", "theme": "fresh start, resolutions, new year offers"},
    "independence_day": {"name": "Independence Day", "emoji": "\U0001f1ee\U0001f1f3", "month": "August", "theme": "patriotic, freedom, pride, special sale"},
    "raksha_bandhan": {"name": "Raksha Bandhan", "emoji": "\U0001f380", "month": "August", "theme": "siblings, love, gifts, family offers"},
    "eid": {"name": "Eid", "emoji": "\u2b50", "month": "varies", "theme": "celebration, togetherness, festive offers"},
    "ganesh_chaturthi": {"name": "Ganesh Chaturthi", "emoji": "\U0001f418", "month": "September", "theme": "new beginnings, blessings, festive season"},
    "makar_sankranti": {"name": "Makar Sankranti", "emoji": "\U0001f329", "month": "January", "theme": "harvest, kites, new start, winter offers"},
}


@router.get("/festivals")
def list_festivals():
    """List available festival campaigns."""
    return {"festivals": [{**v, "id": k} for k, v in FESTIVALS.items()]}


@router.post("/{website_id}/festival/{festival_id}")
async def generate_festival_campaign(website_id: str, festival_id: str):
    """Generate a complete festival marketing campaign."""
    if festival_id not in FESTIVALS:
        raise HTTPException(400, f"Unknown festival. Available: {list(FESTIVALS.keys())}")

    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")

    business_name = lead.get("business_name", "Business")
    category = lead.get("category", "business")
    phone = lead.get("phone", "")
    festival = FESTIVALS[festival_id]

    prompt = f"""Generate a complete {festival['name']} marketing campaign for a {category} business named "{business_name}".

Festival theme: {festival['theme']}

Generate as JSON:
{{
    "offer_headline": "Catchy festival offer headline (max 10 words)",
    "offer_description": "2 sentences describing the special deal",
    "discount": "e.g., 20% off, Buy 1 Get 1, Free consultation",
    "valid_till": "festival date or week after",
    "whatsapp_messages": [
        "Ready-to-send WhatsApp message 1 (for broadcast to customers, under 100 words, include emoji)",
        "Message 2 (different angle)",
        "Message 3 (urgency/last day)"
    ],
    "instagram_captions": [
        "Instagram post caption 1 (with hashtags, emojis, under 150 words)",
        "Caption 2 (different style)"
    ],
    "sms_text": "Short SMS (under 160 chars) with offer + CTA",
    "google_post": "Google Business Profile post text (under 300 chars)",
    "story_ideas": ["Instagram/WhatsApp story idea 1", "Story idea 2", "Story idea 3"],
    "banner_text": {{
        "headline": "Bold headline for poster/banner",
        "subtext": "Supporting text",
        "cta": "Call to action text"
    }}
}}

RULES:
- All content specific to {category} business
- Include {festival['emoji']} {festival['name']} references
- Indian market language (mix of English + Hindi words is OK)
- Create urgency (limited time, limited slots)
- Include phone number {phone} in messages
- Sound festive and celebratory
- Return ONLY valid JSON"""

    result = await chat_completion([{"role": "user", "content": prompt}])

    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        campaign = json.loads(cleaned)
    except Exception:
        campaign = {"raw": cleaned[:500]}

    return {
        "festival": festival["name"],
        "festival_emoji": festival["emoji"],
        "business": business_name,
        "category": category,
        "campaign": campaign,
    }


@router.post("/{website_id}/social-week")
async def generate_social_week(website_id: str):
    """Generate a week of social media content ideas."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")

    business_name = lead.get("business_name", "Business")
    category = lead.get("category", "business")

    prompt = f"""Create 7 days of social media content for a {category} business named "{business_name}".
Mix of Instagram posts, Reels ideas, WhatsApp status, and Google posts.
Indian audience. Engaging, not salesy.

Return as JSON array of 7 items:
[
  {{"day": "Monday", "platform": "Instagram Post", "idea": "What to post", "caption": "Ready caption with hashtags", "time": "Best posting time"}}
]

Return ONLY valid JSON array."""

    result = await chat_completion([{"role": "user", "content": prompt}])

    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        week_plan = json.loads(cleaned)
    except Exception:
        week_plan = [{"day": "Error", "idea": cleaned[:200]}]

    return {"business": business_name, "social_week": week_plan}
