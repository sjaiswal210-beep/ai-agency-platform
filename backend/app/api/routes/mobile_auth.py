from __future__ import annotations
import random
import time
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


@router.post("/send-otp")
async def send_otp(req: SendOTPRequest):
    """Send OTP to phone number. For now, returns OTP in response (dev mode)."""
    phone = req.phone.strip().replace(" ", "")
    if not phone or len(phone) < 10:
        raise HTTPException(400, "Invalid phone number")

    # Check if this phone belongs to an organization
    db = get_supabase()
    orgs = db.table("organizations").select("id, name, slug, plan, owner_phone").eq("owner_phone", phone).execute()

    if not orgs.data:
        # Also check leads table
        leads = db.table("leads").select("id, business_name, phone").eq("phone", phone).execute()
        if not leads.data:
            raise HTTPException(404, "No business found with this phone number")

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    otp_store[phone] = {"otp": otp, "expires": time.time() + 300}  # 5 min expiry

    # TODO: Send via WhatsApp or SMS (Vobiz/MSG91)
    # For now, return in response for development
    logger.info(f"OTP for {phone}: {otp}")

    return {"status": "sent", "message": "OTP sent to your phone", "dev_otp": otp}


@router.post("/verify-otp")
async def verify_otp(req: VerifyOTPRequest):
    """Verify OTP and return auth token + org details."""
    phone = req.phone.strip().replace(" ", "")
    otp = req.otp.strip()

    # Check OTP
    stored = otp_store.get(phone)
    if not stored:
        raise HTTPException(400, "No OTP requested for this number")
    if time.time() > stored["expires"]:
        del otp_store[phone]
        raise HTTPException(400, "OTP expired. Request a new one")
    if stored["otp"] != otp:
        raise HTTPException(400, "Invalid OTP")

    # OTP valid - clear it
    del otp_store[phone]

    # Find organization
    db = get_supabase()
    orgs = db.table("organizations").select("*").eq("owner_phone", phone).execute()

    if orgs.data:
        org = orgs.data[0]
        # Generate session token
        import secrets
        token = secrets.token_urlsafe(32)
        # Store token
        db.table("mobile_sessions").insert({
            "phone": phone,
            "org_id": org["id"],
            "token": token,
        }).execute()

        return {
            "status": "verified",
            "token": token,
            "org_id": org["id"],
            "org_name": org["name"],
            "org_slug": org["slug"],
            "plan": org["plan"],
        }

    # Fallback: check leads
    leads = db.table("leads").select("*").eq("phone", phone).execute()
    if leads.data:
        lead = leads.data[0]
        import secrets
        token = secrets.token_urlsafe(32)
        return {
            "status": "verified",
            "token": token,
            "lead_id": lead["id"],
            "business_name": lead["business_name"],
            "message": "Business found but no dashboard yet",
        }

    raise HTTPException(404, "No business found")
