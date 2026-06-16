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


async def send_site_created_message(business_name: str, phone: str, slug: str) -> dict:
    """Send automated message when a website is created."""
    message = (
        f"Hi {business_name}!\n\n"
        f"Your free business website is now live:\n"
        f"https://{slug}.city-maps.online\n\n"
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