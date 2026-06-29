from __future__ import annotations
import random
import time
import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.supabase import get_supabase
from app.core.logging import get_logger

router = APIRouter(prefix="/api/mobile-auth", tags=["mobile-auth"])
logger = get_logger(__name__)

# In-memory OTP store (use Redis in production)
otp_store: dict = {}


class SendOTPRequest(BaseModel):
    phone: str


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str


def _resolve_business(db, phone: str) -> dict | None:
    """Map a phone number to its business website + owner panel.

    Looks across leads, websites, dashboard_visitors and organizations.
    Returns dict with website_id, slug, business_name, panel_url (best effort).
    """
    # 1. Lead by phone -> its latest website
    try:
        leads = db.table("leads").select("id, business_name").eq("phone", phone).execute()
        if leads.data:
            lead = leads.data[0]
            ws = db.table("websites").select("id, slug").eq("lead_id", lead["id"]).order("created_at", desc=True).limit(1).execute()
            if ws.data and ws.data[0].get("slug"):
                w = ws.data[0]
                return {
                    "website_id": w["id"],
                    "slug": w["slug"],
                    "business_name": lead.get("business_name", ""),
                    "panel_url": f"https://{w['slug']}.city-maps.online/api/panel/{w['id']}",
                }
    except Exception as e:
        logger.warning(f"lead lookup failed: {e}")

    # 2. Dashboard visitor record (phone entered on web dashboard) -> website by slug
    try:
        dv = db.table("dashboard_visitors").select("org_slug, org_name").eq("phone", phone).order("created_at", desc=True).limit(1).execute()
        if dv.data and dv.data[0].get("org_slug"):
            slug = dv.data[0]["org_slug"]
            ws = db.table("websites").select("id, slug").eq("slug", slug).limit(1).execute()
            if ws.data:
                w = ws.data[0]
                return {
                    "website_id": w["id"],
                    "slug": w["slug"],
                    "business_name": dv.data[0].get("org_name", ""),
                    "panel_url": f"https://{w['slug']}.city-maps.online/api/panel/{w['id']}",
                }
    except Exception as e:
        logger.warning(f"visitor lookup failed: {e}")

    # 3. Organization by owner_phone (modules model)
    try:
        orgs = db.table("organizations").select("id, name, slug, plan").eq("owner_phone", phone).execute()
        if orgs.data:
            o = orgs.data[0]
            return {
                "org_id": o["id"],
                "slug": o.get("slug", ""),
                "business_name": o.get("name", ""),
                "plan": o.get("plan", ""),
            }
    except Exception as e:
        logger.warning(f"org lookup failed: {e}")

    return None


@router.post("/send-otp")
async def send_otp(req: SendOTPRequest):
    """Send OTP to phone (WhatsApp). Phone must belong to a known business."""
    phone = req.phone.strip().replace(" ", "")
    if not phone or len(phone) < 10:
        raise HTTPException(400, "Invalid phone number")

    db = get_supabase()
    business = _resolve_business(db, phone)
    if not business:
        raise HTTPException(404, "No business found with this phone number")

    otp = str(random.randint(100000, 999999))
    otp_store[phone] = {"otp": otp, "expires": time.time() + 300}

    from app.services.whatsapp_auto import send_whatsapp_otp
    send_result = await send_whatsapp_otp(phone, otp)
    logger.info(f"OTP send for {phone}: {send_result.get('method')}")

    response = {"status": "sent", "message": "OTP sent to your WhatsApp"}
    if not send_result.get("sent"):
        response["dev_otp"] = otp
        response["message"] = "OTP generated (dev mode - WhatsApp not configured)"
    return response


@router.post("/verify-otp")
async def verify_otp(req: VerifyOTPRequest):
    """Verify OTP and return the business + owner-panel URL for the app."""
    phone = req.phone.strip().replace(" ", "")
    otp = req.otp.strip()

    stored = otp_store.get(phone)
    if not stored:
        raise HTTPException(400, "No OTP requested for this number")
    if time.time() > stored["expires"]:
        del otp_store[phone]
        raise HTTPException(400, "OTP expired. Request a new one")
    if stored["otp"] != otp:
        raise HTTPException(400, "Invalid OTP")
    del otp_store[phone]

    db = get_supabase()
    business = _resolve_business(db, phone)
    if not business:
        raise HTTPException(404, "No business found")

    token = secrets.token_urlsafe(32)
    try:
        db.table("mobile_sessions").insert({
            "phone": phone,
            "org_id": business.get("org_id"),
            "token": token,
        }).execute()
    except Exception:
        pass

    return {"status": "verified", "token": token, **business}
