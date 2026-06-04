from __future__ import annotations
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
from app.core.logging import get_logger

router = APIRouter(prefix="/toolkit", tags=["toolkit"])
logger = get_logger(__name__)


# Category-specific tools
CATEGORY_TOOLS = {
    "hotel": [
        {"id": "booking_msg", "name": "Booking Confirmation Generator", "icon": "📋", "desc": "Generate booking confirmation messages for WhatsApp/SMS"},
        {"id": "review_reply", "name": "Review Reply Writer", "icon": "⭐", "desc": "AI-written replies to Google/TripAdvisor reviews"},
        {"id": "social_caption", "name": "Social Media Caption", "icon": "��", "desc": "Generate Instagram/Facebook captions for hotel photos"},
        {"id": "offer_msg", "name": "Seasonal Offer Creator", "icon": "🎉", "desc": "Create festive/seasonal offer messages"},
        {"id": "guest_welcome", "name": "Guest Welcome Message", "icon": "🙏", "desc": "Personalized welcome messages for guests"},
        {"id": "checkin_reminder", "name": "Check-in Reminder", "icon": "🔔", "desc": "Pre-arrival reminder messages"},
    ],
    "restaurant": [
        {"id": "menu_post", "name": "Menu Item Promoter", "icon": "🍽️", "desc": "Create social posts for new dishes/specials"},
        {"id": "review_reply", "name": "Review Reply Writer", "icon": "⭐", "desc": "AI replies to Zomato/Google reviews"},
        {"id": "offer_msg", "name": "Offer/Discount Creator", "icon": "��", "desc": "Generate offer messages for WhatsApp broadcast"},
        {"id": "social_caption", "name": "Food Photo Caption", "icon": "📸", "desc": "Captions for food photography posts"},
        {"id": "event_announce", "name": "Event Announcement", "icon": "🎊", "desc": "Create event/live music announcements"},
        {"id": "feedback_ask", "name": "Feedback Request", "icon": "💬", "desc": "Polite feedback request messages after dining"},
    ],
    "gym": [
        {"id": "motivation_post", "name": "Motivation Post", "icon": "💪", "desc": "Daily fitness motivation for social media"},
        {"id": "class_announce", "name": "Class Schedule Post", "icon": "📅", "desc": "Announce new classes or schedule changes"},
        {"id": "offer_msg", "name": "Membership Offer", "icon": "🎉", "desc": "Create membership discount offers"},
        {"id": "transformation", "name": "Transformation Story", "icon": "🏆", "desc": "Write client transformation success stories"},
        {"id": "tips_post", "name": "Fitness Tips Post", "icon": "📝", "desc": "Generate workout/nutrition tip posts"},
        {"id": "reminder_msg", "name": "Renewal Reminder", "icon": "🔔", "desc": "Membership renewal reminder messages"},
    ],
    "clinic": [
        {"id": "health_tip", "name": "Health Tip Post", "icon": "🩺", "desc": "Educational health tips for social media"},
        {"id": "appointment_remind", "name": "Appointment Reminder", "icon": "📅", "desc": "Generate appointment reminder messages"},
        {"id": "review_reply", "name": "Review Reply Writer", "icon": "⭐", "desc": "Professional replies to patient reviews"},
        {"id": "offer_msg", "name": "Health Camp Announcement", "icon": "��", "desc": "Create free checkup/camp announcements"},
        {"id": "followup_msg", "name": "Patient Follow-up", "icon": "💊", "desc": "Post-visit follow-up care messages"},
        {"id": "awareness_post", "name": "Awareness Day Post", "icon": "🎗️", "desc": "Posts for health awareness days"},
    ],
    "dentist": [
        {"id": "health_tip", "name": "Dental Tip Post", "icon": "🦷", "desc": "Dental hygiene tips for social media"},
        {"id": "appointment_remind", "name": "Appointment Reminder", "icon": "📅", "desc": "Friendly appointment reminders"},
        {"id": "review_reply", "name": "Review Reply Writer", "icon": "⭐", "desc": "Replies to Google reviews"},
        {"id": "offer_msg", "name": "Treatment Offer", "icon": "✨", "desc": "Create offers for teeth whitening, cleaning etc."},
        {"id": "before_after", "name": "Before/After Post", "icon": "📸", "desc": "Write captions for treatment results"},
        {"id": "kids_dental", "name": "Kids Dental Post", "icon": "��", "desc": "Fun dental care posts for parents"},
    ],
    "salon": [
        {"id": "style_post", "name": "Style Showcase Post", "icon": "✂️", "desc": "Captions for hairstyle/makeover photos"},
        {"id": "offer_msg", "name": "Service Offer Creator", "icon": "🎉", "desc": "Create discount/package offers"},
        {"id": "trend_post", "name": "Trend Alert Post", "icon": "🔥", "desc": "Posts about latest beauty/hair trends"},
        {"id": "review_reply", "name": "Review Reply Writer", "icon": "⭐", "desc": "Reply to Google/social reviews"},
        {"id": "bridal_pkg", "name": "Bridal Package Post", "icon": "👰", "desc": "Create bridal/wedding package promotions"},
        {"id": "tips_post", "name": "Beauty Tips Post", "icon": "💄", "desc": "Skincare/haircare tips for social media"},
    ],
    "default": [
        {"id": "social_caption", "name": "Social Media Post", "icon": "📱", "desc": "Generate engaging social media captions"},
        {"id": "review_reply", "name": "Review Reply Writer", "icon": "⭐", "desc": "AI-written replies to customer reviews"},
        {"id": "offer_msg", "name": "Offer/Promotion Creator", "icon": "🎉", "desc": "Create promotional messages"},
        {"id": "whatsapp_broadcast", "name": "WhatsApp Broadcast", "icon": "💬", "desc": "Create broadcast messages for customers"},
        {"id": "ad_copy", "name": "Ad Copy Writer", "icon": "📢", "desc": "Write Google/Facebook ad copy"},
        {"id": "email_template", "name": "Email Template", "icon": "✉️", "desc": "Generate professional email templates"},
    ],
}


def get_tools_for_category(category: str) -> list:
    """Get relevant tools for a business category."""
    cat = category.lower().strip()
    if cat in CATEGORY_TOOLS:
        return CATEGORY_TOOLS[cat]
    for key in CATEGORY_TOOLS:
        if key in cat or cat in key:
            return CATEGORY_TOOLS[key]
    # Keyword matching
    keyword_map = {
        "food": "restaurant", "cafe": "restaurant", "pizza": "restaurant",
        "fitness": "gym", "yoga": "gym", "workout": "gym",
        "hospital": "clinic", "doctor": "clinic", "medical": "clinic",
        "dental": "dentist", "teeth": "dentist",
        "beauty": "salon", "hair": "salon", "spa": "salon",
        "lodge": "hotel", "resort": "hotel", "hostel": "hotel",
    }
    for keyword, mapped in keyword_map.items():
        if keyword in cat:
            return CATEGORY_TOOLS[mapped]
    return CATEGORY_TOOLS["default"]


@router.get("/{website_id}/tools")
def get_tools(website_id: str):
    """Get available tools for a website's business category."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    category = lead.get("category", "default") if lead else "default"
    tools = get_tools_for_category(category)
    return {"category": category, "tools": tools}


class ToolRunRequest(BaseModel):
    tool_id: str
    context: str = ""  # Optional extra context from the user


@router.post("/{website_id}/tools/run")
async def run_tool(website_id: str, req: ToolRunRequest):
    """Run a specific tool and generate content."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    phone = lead.get("phone", "") if lead else ""
    address = lead.get("address", "") if lead else ""

    # Build prompt based on tool_id
    tool_prompts = {
        "booking_msg": f"Generate a professional booking confirmation message for {business_name} (a {category}). Include: guest name placeholder, dates, room/service details, check-in time, contact number {phone}. Make it warm and professional. Generate 2 variants (formal and friendly).",
        "review_reply": f"Write 3 professional reply templates for {business_name} ({category}): one for a 5-star positive review, one for a 3-star mixed review, and one for a 1-star negative review. Be empathetic, professional, and solution-oriented. Keep each under 100 words.",
        "social_caption": f"Generate 5 engaging social media captions for {business_name} ({category}). Include emojis, hashtags, and a call-to-action. Mix: 1 promotional, 1 behind-the-scenes, 1 customer appreciation, 1 tip/educational, 1 festive/seasonal. Phone: {phone}",
        "offer_msg": f"Create 3 promotional offer messages for {business_name} ({category}) suitable for WhatsApp broadcast. Include: catchy headline, offer details, urgency element, CTA with phone {phone}. Keep each under 150 words. Make them feel exclusive.",
        "guest_welcome": f"Generate 3 personalized welcome message templates for {business_name} ({category}). Include: warm greeting, key info (WiFi, breakfast time, checkout), contact for help. One formal, one casual, one festive.",
        "checkin_reminder": f"Create 2 pre-arrival reminder messages for {business_name}. Include: date confirmation, directions hint, what to bring, contact {phone}. Friendly tone.",
        "menu_post": f"Write 4 social media posts promoting menu items for {business_name} ({category}). Make them mouth-watering with emojis. Include hashtags and CTA to order/visit.",
        "event_announce": f"Create 2 event announcement posts for {business_name} ({category}). One for a weekend special, one for a live event. Include date placeholders, excitement, CTA.",
        "feedback_ask": f"Generate 3 polite feedback request messages for {business_name} after a customer visit. One for WhatsApp, one for SMS, one for email. Keep short and genuine.",
        "motivation_post": f"Write 5 fitness motivation posts for {business_name} ({category}). Mix quotes, tips, and challenges. Include emojis and hashtags. Make them shareable.",
        "class_announce": f"Create 3 class/session announcement posts for {business_name}. Include: class name, time, benefits, CTA to book. Energetic tone.",
        "transformation": f"Write 2 client transformation story templates for {business_name}. Include: before situation, journey, results, quote from client. Inspiring tone.",
        "tips_post": f"Generate 5 educational tip posts for {business_name} ({category}). Short, actionable tips relevant to the business. Include emojis and hashtags.",
        "reminder_msg": f"Create 3 renewal/reminder messages for {business_name}. One for membership expiry, one for appointment, one for follow-up. Friendly, not pushy.",
        "health_tip": f"Write 5 health/wellness tip posts for {business_name} ({category}). Educational, trustworthy tone. Include emojis and relevant hashtags.",
        "appointment_remind": f"Generate 3 appointment reminder templates for {business_name}. One for 24h before, one for same-day morning, one for rescheduling. Include phone {phone}.",
        "awareness_post": f"Create 3 health awareness day posts for {business_name} ({category}). Pick relevant awareness days. Educational with CTA to visit.",
        "followup_msg": f"Write 3 patient/customer follow-up messages for {business_name}. Post-visit care instructions, satisfaction check, next appointment reminder.",
        "style_post": f"Write 4 style showcase captions for {business_name} ({category}). For before/after photos, new styles, trending looks. Glamorous tone with hashtags.",
        "trend_post": f"Create 3 trend alert posts for {business_name} ({category}). What's trending this season, why customers should try it, CTA to book.",
        "bridal_pkg": f"Write 2 bridal/wedding package promotional posts for {business_name}. Include services, why choose them, emotional appeal, CTA.",
        "whatsapp_broadcast": f"Generate 3 WhatsApp broadcast messages for {business_name} ({category}). One weekly update, one special offer, one festive greeting. Keep under 100 words each.",
        "ad_copy": f"Write Google Ads and Facebook Ads copy for {business_name} ({category}) in {address}. Include: 3 Google Ad headlines (30 chars each), 2 descriptions (90 chars each), and 1 Facebook ad (primary text + headline + description).",
        "email_template": f"Create 2 professional email templates for {business_name}: one welcome email for new customers, one promotional email for an offer. Include subject lines.",
        "before_after": f"Write 3 before/after transformation captions for {business_name} ({category}). Highlight the change, process, and invite others to try.",
        "kids_dental": f"Create 3 fun, parent-friendly posts about kids dental care for {business_name}. Educational but light-hearted. Include tips and CTA.",
    }

    base_prompt = tool_prompts.get(req.tool_id, f"Generate helpful marketing content for {business_name} ({category}). Phone: {phone}")

    if req.context:
        base_prompt += f"\n\nAdditional context from the user: {req.context}"

    base_prompt += "\n\nFormat the output clearly with headers and sections. Use emojis where appropriate."

    result = await chat_completion([{"role": "user", "content": base_prompt}])

    return {
        "tool_id": req.tool_id,
        "business": business_name,
        "content": result,
    }
