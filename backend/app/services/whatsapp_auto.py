"""WhatsApp Auto Message Service - uses Meta WhatsApp Cloud API (free 1000/month)."""
import httpx
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Meta WhatsApp Cloud API endpoint
WA_API_URL = "https://graph.facebook.com/v18.0"


async def send_whatsapp_message(phone: str, message: str) -> dict:
    """Send WhatsApp message via Meta Cloud API."""
    settings = get_settings()
    
    # Clean phone number (must include country code, no + sign)
    clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not clean.startswith("91") and len(clean) == 10:
        clean = "91" + clean
    
    # Get WhatsApp Cloud API credentials from env
    wa_token = getattr(settings, "whatsapp_token", "") or ""
    wa_phone_id = getattr(settings, "whatsapp_phone_id", "") or ""
    
    if wa_token and wa_phone_id:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{WA_API_URL}/{wa_phone_id}/messages",
                    headers={
                        "Authorization": f"Bearer {wa_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": clean,
                        "type": "text",
                        "text": {"body": message}
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    logger.info("WhatsApp sent via Cloud API", phone=clean)
                    return {"sent": True, "method": "cloud_api", "phone": clean}
                else:
                    logger.warning("WhatsApp API error", status=resp.status_code, body=resp.text[:200])
        except Exception as e:
            logger.warning("WhatsApp Cloud API failed", error=str(e))
    
    # Fallback: generate wa.me link
    import urllib.parse
    encoded = urllib.parse.quote(message)
    link = f"https://wa.me/{clean}?text={encoded}"
    
    return {"sent": False, "method": "link", "link": link, "phone": clean}


# TEMP: route all lead/site-created notifications to this number instead of the
# business owner (testing mode). Set to "" to send directly to owners.
LEAD_NOTIFY_OVERRIDE = "917350785606"


async def send_site_ready_template(phone: str, business_name: str, site_url: str) -> dict:
    """Send the approved 'site_ready' utility template (works outside 24h window)."""
    settings = get_settings()
    clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not clean.startswith("91") and len(clean) == 10:
        clean = "91" + clean

    wa_token = getattr(settings, "whatsapp_token", "") or ""
    wa_phone_id = getattr(settings, "whatsapp_phone_id", "") or ""
    template_name = getattr(settings, "whatsapp_site_template", "") or "site_ready"
    template_lang = getattr(settings, "whatsapp_site_lang", "") or "en"

    if not (wa_token and wa_phone_id):
        return {"sent": False, "method": "no_config"}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{WA_API_URL}/{wa_phone_id}/messages",
                headers={"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "to": clean,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": template_lang},
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": business_name or "there"},
                                    {"type": "text", "text": site_url},
                                ],
                            }
                        ],
                    },
                },
                timeout=15,
            )
            if resp.status_code == 200:
                logger.info("site_ready template sent", phone=clean)
                return {"sent": True, "method": "template", "phone": clean}
            logger.warning("site_ready template failed", status=resp.status_code, body=resp.text[:300])
            return {"sent": False, "method": "template_failed", "status": resp.status_code, "body": resp.text[:300]}
    except Exception as e:
        logger.warning("site_ready template error", error=str(e))
        return {"sent": False, "method": "error", "error": str(e)[:200]}


async def send_site_created_message(business_name: str, phone: str, slug: str) -> dict:
    """Send notification when a website is created.

    Uses the approved 'site_ready' template so it reaches owners even outside the
    24h window. During testing, routed to LEAD_NOTIFY_OVERRIDE instead of the owner.
    """
    site_url = f"https://{slug}.city-maps.online"
    recipient = LEAD_NOTIFY_OVERRIDE or phone

    # Try the approved template first (works for cold contacts)
    result = await send_site_ready_template(recipient, business_name, site_url)
    if result.get("sent"):
        return result

    # Fallback: plain text (only delivers inside 24h window)
    if LEAD_NOTIFY_OVERRIDE:
        message = (
            f"New website generated\n\n"
            f"Business: {business_name}\n"
            f"Owner phone: {phone}\n"
            f"Live site: {site_url}"
        )
        return await send_whatsapp_message(LEAD_NOTIFY_OVERRIDE, message)

    message = (
        f"Hi {business_name}!\n\n"
        f"Your free business website is now live:\n"
        f"{site_url}\n\n"
        f"Share it with your customers!\n"
        f"Powered by City Maps"
    )
    return await send_whatsapp_message(phone, message)


async def send_bulk_message(phones: list, message: str) -> list:
    """Send message to multiple numbers."""
    results = []
    for phone in phones:
        result = await send_whatsapp_message(phone, message)
        results.append(result)
    return results

async def send_whatsapp_otp(phone: str, otp: str) -> dict:
    """Send OTP via WhatsApp Authentication template (with plain-text fallback).

    Meta requires business-initiated messages (cold OTP) to use an approved
    Authentication template. Falls back to plain text if template send fails
    (works only inside the 24h customer service window) and finally to a wa.me link.
    """
    settings = get_settings()

    clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not clean.startswith("91") and len(clean) == 10:
        clean = "91" + clean

    wa_token = getattr(settings, "whatsapp_token", "") or ""
    wa_phone_id = getattr(settings, "whatsapp_phone_id", "") or ""
    template_name = getattr(settings, "whatsapp_otp_template", "") or "login_otp"
    template_lang = getattr(settings, "whatsapp_otp_lang", "") or "en"

    if wa_token and wa_phone_id:
        # Try Authentication template first (required for cold sends)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{WA_API_URL}/{wa_phone_id}/messages",
                    headers={
                        "Authorization": f"Bearer {wa_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": clean,
                        "type": "template",
                        "template": {
                            "name": template_name,
                            "language": {"code": template_lang},
                            "components": [
                                {
                                    "type": "body",
                                    "parameters": [{"type": "text", "text": otp}],
                                },
                                {
                                    "type": "button",
                                    "sub_type": "url",
                                    "index": "0",
                                    "parameters": [{"type": "text", "text": otp}],
                                },
                            ],
                        },
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    logger.info("OTP sent via WhatsApp template", phone=clean)
                    return {"sent": True, "method": "template", "phone": clean}
                else:
                    logger.warning("WhatsApp template send failed", status=resp.status_code, body=resp.text[:300])
        except Exception as e:
            logger.warning("WhatsApp template send error", error=str(e))

    # Fallback: plain text (only delivers inside 24h window)
    message = (
        f"Your City Maps login code is: {otp}\n\n"
        f"This code expires in 5 minutes.\n"
        f"Do not share it with anyone."
    )
    return await send_whatsapp_message(phone, message)