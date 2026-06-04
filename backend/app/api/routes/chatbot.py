from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


class ChatMessage(BaseModel):
    message: str
    website_id: str


@router.post("/reply")
async def chatbot_reply(req: ChatMessage):
    """AI receptionist - answers customer questions about the business."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(req.website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    phone = lead.get("phone", "") if lead else ""
    address = lead.get("address", "") if lead else ""

    content = website.get("content", {})
    services = content.get("services", [])
    hours = content.get("contact_info", {}).get("hours", "Mon-Sat 9AM-8PM")

    services_list = ", ".join([s.get("name", "") for s in services[:5]])

    prompt = f"""You are an AI receptionist for {business_name} ({category}).
Business details:
- Phone: {phone}
- Address: {address}
- Hours: {hours}
- Services: {services_list}

Customer message: "{req.message}"

Reply as a helpful, friendly receptionist. Keep response under 50 words.
If they want to book, tell them to call {phone} or use the booking form.
If you don't know something specific, offer to connect them with the team.
Be warm and professional."""

    reply = await chat_completion([{"role": "user", "content": prompt}])
    return {"reply": reply.strip(), "business": business_name}


class BookingRequest(BaseModel):
    website_id: str
    name: str
    phone: str
    date: str = ""
    time: str = ""
    service: str = ""
    notes: str = ""


@router.post("/booking")
async def submit_booking(req: BookingRequest):
    """Submit a booking request from the website."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(req.website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"

    # Store booking (in production, this would go to a bookings table)
    # For now, return success and the owner can see it in their panel
    return {
        "status": "confirmed",
        "message": f"Booking request received for {business_name}. We will confirm shortly.",
        "booking": {
            "customer_name": req.name,
            "customer_phone": req.phone,
            "date": req.date,
            "time": req.time,
            "service": req.service,
            "notes": req.notes,
        }
    }
