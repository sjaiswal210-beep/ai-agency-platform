from __future__ import annotations
import urllib.parse
from app.core.llm import chat_completion
from app.core.logging import get_logger

logger = get_logger(__name__)

# Your business details
AGENCY_NAME = "AI Agency"
AGENCY_PHONE = ""  # Your WhatsApp number (set this)
MONTHLY_PRICE = 79  # Rs per month
CURRENCY = "INR"


async def generate_outreach_message(lead: dict, website_preview_url: str) -> str:
    """Generate a personalized WhatsApp outreach message for a business owner."""
    
    prompt = f"""Write a WhatsApp message to send to a business owner. Keep it short, friendly, and professional.

CONTEXT:
- You are reaching out from an AI-powered web agency
- You have already built a FREE demo website for their business
- The demo website link: {website_preview_url}
- Monthly subscription: Only Rs.{MONTHLY_PRICE}/month for full website + maintenance
- Business name: {lead.get('business_name', '')}
- Business category: {lead.get('category', '')}
- Their current website: {lead.get('website') or 'They have NO website currently'}
- Their rating: {lead.get('rating', 'N/A')} ({lead.get('review_count', 0)} reviews)

MESSAGE RULES:
- Start with a greeting using their business name
- Mention you noticed they could benefit from a better online presence
- Say you built a FREE demo website for them (include the link)
- Mention the price: Only Rs.{MONTHLY_PRICE}/month
- What they get: Professional website, SEO, Google Maps, WhatsApp integration, mobile-friendly
- End with a soft CTA (ask if they'd like to see it)
- Keep under 150 words
- Use some emojis but don't overdo it
- Sound human, not salesy
- Write in English (with Hindi words like "Namaste" or "ji" if appropriate)

Return ONLY the message text, nothing else."""

    message = await chat_completion([{"role": "user", "content": prompt}])
    return message.strip()


def generate_whatsapp_link(phone: str, message: str) -> str:
    """Generate a wa.me link with pre-filled message."""
    # Clean phone number
    clean_phone = phone.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    if clean_phone.startswith("0"):
        clean_phone = "91" + clean_phone[1:]
    elif not clean_phone.startswith("91"):
        clean_phone = "91" + clean_phone
    
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"


async def generate_followup_message(lead: dict, attempt: int = 1) -> str:
    """Generate follow-up messages."""
    
    prompts = {
        1: f"Write a gentle follow-up WhatsApp message for {lead.get('business_name')}. Mention you shared a demo website earlier. Ask if they had a chance to look. Keep under 50 words. Friendly tone.",
        2: f"Write a 2nd follow-up for {lead.get('business_name')}. Mention the demo website is still live. Add urgency: 'offer valid this week'. Rs.{MONTHLY_PRICE}/month. Under 40 words.",
        3: f"Write a final follow-up for {lead.get('business_name')}. Very short, just asking if they're interested or should you remove their demo site. Under 30 words. No pressure.",
    }
    
    prompt = prompts.get(attempt, prompts[1])
    message = await chat_completion([{"role": "user", "content": prompt}])
    return message.strip()
