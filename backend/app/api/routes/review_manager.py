from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
import json

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/{website_id}/reply")
async def generate_review_reply(website_id: str, review_text: str = "", rating: int = 5, reviewer_name: str = "Customer"):
    """Generate a professional reply to a Google review."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    prompt = f"""Write a professional Google review reply for {business_name} ({category}).

Customer: {reviewer_name}
Rating: {rating}/5
Review: "{review_text}"

RULES:
- Thank them by name
- If positive (4-5 stars): express gratitude, invite them back
- If negative (1-3 stars): apologize sincerely, offer to make it right, give phone number
- Keep under 80 words
- Sound human and warm, not corporate
- Include business name once
- End with a personal touch

Return ONLY the reply text."""

    reply = await chat_completion([{"role": "user", "content": prompt}])
    return {"reply": reply.strip(), "rating": rating, "reviewer": reviewer_name, "business": business_name}


@router.post("/{website_id}/request-messages")
async def generate_review_requests(website_id: str, count: int = 3):
    """Generate WhatsApp messages to request reviews from happy customers."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    prompt = f"""Write {count} different WhatsApp messages that {business_name} ({category}) can send to happy customers asking for a Google review.

RULES:
- Each message under 60 words
- Casual, friendly tone (not formal)
- Include a Google Maps review link placeholder: [REVIEW_LINK]
- Make it easy for them (specific: "just 2 minutes", "click this link")
- Different approach for each (gratitude, humor, simple request)
- Indian conversational style

Return as JSON array: ["message1", "message2", ...]
Return ONLY valid JSON."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
    try:
        messages = json.loads(cleaned)
    except Exception:
        messages = [cleaned[:200]]

    return {"business": business_name, "review_request_messages": messages}
