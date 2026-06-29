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

@router.get("/diag")
async def whatsapp_diag(pwd: str, phone: str = "917350785606"):
    """Admin: diagnose WhatsApp Cloud API config and show raw Meta response.

    Usage: GET /api/whatsapp/diag?pwd=kalpdev2024
    """
    if pwd != "kalpdev2024":
        raise HTTPException(403, "Forbidden")
    import httpx
    from app.core.config import get_settings
    settings = get_settings()
    wa_token = getattr(settings, "whatsapp_token", "") or ""
    wa_phone_id = getattr(settings, "whatsapp_phone_id", "") or ""

    diag = {
        "token_set": bool(wa_token),
        "token_length": len(wa_token),
        "phone_id_set": bool(wa_phone_id),
        "phone_id_value": wa_phone_id,
    }

    if not wa_token or not wa_phone_id:
        diag["verdict"] = "Missing WHATSAPP_TOKEN or WHATSAPP_PHONE_ID on the server (check Render env vars + redeploy)"
        return diag

    clean = phone.replace("+", "").replace(" ", "").replace("-", "")
    if not clean.startswith("91") and len(clean) == 10:
        clean = "91" + clean
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://graph.facebook.com/v18.0/{wa_phone_id}/messages",
                headers={"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "to": clean, "type": "text", "text": {"body": "City Maps diag test"}},
                timeout=15,
            )
            diag["meta_status"] = resp.status_code
            diag["meta_response"] = resp.text[:500]
            diag["verdict"] = "OK - message sent" if resp.status_code == 200 else "Meta rejected the request - see meta_response"
    except Exception as e:
        diag["error"] = str(e)[:300]
        diag["verdict"] = "Request to Meta failed"
    return diag

@router.post("/register")
async def whatsapp_register(pwd: str, pin: str):
    """Admin: register the phone number with WhatsApp Cloud API (fixes error 133010).

    pin = a 6-digit two-step verification PIN of your choice (remember it).
    Usage: POST /api/whatsapp/register?pwd=kalpdev2024&pin=123456
    """
    if pwd != "kalpdev2024":
        raise HTTPException(403, "Forbidden")
    if not (pin.isdigit() and len(pin) == 6):
        raise HTTPException(400, "PIN must be exactly 6 digits")
    import httpx
    from app.core.config import get_settings
    settings = get_settings()
    wa_token = getattr(settings, "whatsapp_token", "") or ""
    wa_phone_id = getattr(settings, "whatsapp_phone_id", "") or ""
    if not wa_token or not wa_phone_id:
        raise HTTPException(400, "Token or phone ID not set on server")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://graph.facebook.com/v18.0/{wa_phone_id}/register",
                headers={"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "pin": pin},
                timeout=20,
            )
            return {
                "status_code": resp.status_code,
                "response": resp.text[:500],
                "verdict": "Registered - now try test-send" if resp.status_code == 200 else "See response for error",
            }
    except Exception as e:
        raise HTTPException(500, f"Register failed: {str(e)[:200]}")