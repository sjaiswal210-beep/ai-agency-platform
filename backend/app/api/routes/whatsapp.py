from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.services.whatsapp_service import generate_outreach_message, generate_whatsapp_link, generate_followup_message
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
logger = get_logger(__name__)


@router.post("/outreach/{lead_id}")
async def send_whatsapp_outreach(lead_id: str):
    """Generate WhatsApp outreach message with demo website link."""
    lead_service = LeadService()
    website_service = WebsiteService()

    lead = lead_service.get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    if not lead.get("phone"):
        raise HTTPException(400, "Lead has no phone number")

    # Find their generated website
    websites = website_service.get_by_lead(lead_id)
    settings = get_settings()

    if websites:
        preview_url = f"{settings.backend_url}/api/preview/{websites[0]['id']}"
    else:
        preview_url = "Website will be generated soon"

    # Generate personalized message
    message = await generate_outreach_message(lead, preview_url)

    # Generate WhatsApp link
    wa_link = generate_whatsapp_link(lead["phone"], message)

    return {
        "lead_id": lead_id,
        "business_name": lead["business_name"],
        "phone": lead["phone"],
        "message": message,
        "whatsapp_link": wa_link,
        "preview_url": preview_url,
    }


@router.post("/followup/{lead_id}")
async def send_followup(lead_id: str, attempt: int = 1):
    """Generate follow-up WhatsApp message."""
    lead_service = LeadService()
    lead = lead_service.get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    if not lead.get("phone"):
        raise HTTPException(400, "Lead has no phone number")

    message = await generate_followup_message(lead, attempt)
    wa_link = generate_whatsapp_link(lead["phone"], message)

    return {
        "lead_id": lead_id,
        "business_name": lead["business_name"],
        "phone": lead["phone"],
        "message": message,
        "whatsapp_link": wa_link,
        "attempt": attempt,
    }


@router.post("/bulk-outreach")
async def bulk_whatsapp_outreach(status: str = "analyzed", limit: int = 10):
    """Generate WhatsApp outreach for multiple leads at once."""
    lead_service = LeadService()
    website_service = WebsiteService()
    settings = get_settings()

    leads = lead_service.list_leads(status=status, limit=limit)
    results = []

    for lead in leads:
        if not lead.get("phone"):
            continue

        websites = website_service.get_by_lead(lead["id"])
        preview_url = f"{settings.backend_url}/api/preview/{websites[0]['id']}" if websites else ""

        message = await generate_outreach_message(lead, preview_url)
        wa_link = generate_whatsapp_link(lead["phone"], message)

        results.append({
            "business_name": lead["business_name"],
            "phone": lead["phone"],
            "message": message,
            "whatsapp_link": wa_link,
        })

    return {"count": len(results), "outreach": results}


@router.post("/test-send")
async def test_send(phone: str, pwd: str, text: str = "City Maps WhatsApp test message - it works!"):
    """Admin: send a test WhatsApp message to verify Cloud API is working.

    Usage: POST /api/whatsapp/test-send?phone=917350785606&pwd=kalpdev2024
    """
    if pwd != "kalpdev2024":
        raise HTTPException(403, "Forbidden")
    from app.services.whatsapp_auto import send_whatsapp_message
    result = await send_whatsapp_message(phone, text)
    return {"requested_phone": phone, "result": result}