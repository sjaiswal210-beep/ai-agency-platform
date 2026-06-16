"""WhatsApp Auto Message Service - sends messages via API."""
import httpx
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_whatsapp_message(phone: str, message: str) -> dict:
    """Send WhatsApp message via API. Uses UltraMsg or fallback to wa.me link."""
    settings = get_settings()
    
    # Clean phone number
    clean = phone.replace(" ", "").replace("-", "").replace("+", "")
    if not clean.startswith("91") and len(clean) == 10:
        clean = "91" + clean
    
    # Try UltraMsg API if configured
    ultramsg_token = getattr(settings, "ultramsg_token", "") or ""
    ultramsg_instance = getattr(settings, "ultramsg_instance", "") or ""
    
    if ultramsg_token and ultramsg_instance:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.ultramsg.com/{ultramsg_instance}/messages/chat",
                    data={"token": ultramsg_token, "to": clean, "body": message},
                    timeout=15,
                )
                if resp.status_code == 200:
                    logger.info("WhatsApp sent via UltraMsg", phone=clean)
                    return {"sent": True, "method": "ultramsg", "phone": clean}
        except Exception as e:
            logger.warning("UltraMsg failed", error=str(e))
    
    # Fallback: generate wa.me link
    import urllib.parse
    encoded = urllib.parse.quote(message)
    link = f"https://wa.me/{clean}?text={encoded}"
    
    return {"sent": False, "method": "link", "link": link, "phone": clean}


async def send_site_created_message(business_name: str, phone: str, slug: str) -> dict:
    """Send automated message when a website is created."""
    message = f"Hi {business_name}! Your free business website is now live at https://{slug}.city-maps.online - Share it with your customers! Powered by City Maps."
    return await send_whatsapp_message(phone, message)


async def send_bulk_message(phones: list, message: str) -> list:
    """Send message to multiple numbers."""
    results = []
    for phone in phones:
        result = await send_whatsapp_message(phone, message)
        results.append(result)
    return results