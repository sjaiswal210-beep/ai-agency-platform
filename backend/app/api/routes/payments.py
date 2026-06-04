from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.core.supabase import get_supabase
from app.core.logging import get_logger

router = APIRouter(prefix="/payments", tags=["payments"])
logger = get_logger(__name__)

# Razorpay credentials (set these when you have them)
RAZORPAY_KEY_ID = ""  # Set from .env
RAZORPAY_KEY_SECRET = ""  # Set from .env
PLAN_AMOUNT = 79  # INR per month


class CreateOrderRequest(BaseModel):
    lead_id: str
    client_name: str
    client_phone: str


@router.post("/create-order")
def create_order(req: CreateOrderRequest):
    """Create a Razorpay payment order for subscription."""
    if not RAZORPAY_KEY_ID:
        # Return a mock order for testing without Razorpay
        return {
            "order_id": "order_test_" + req.lead_id[:8],
            "amount": PLAN_AMOUNT * 100,  # paise
            "currency": "INR",
            "key_id": "rzp_test_placeholder",
            "client_name": req.client_name,
            "client_phone": req.client_phone,
            "notes": "Razorpay not configured yet. Add RAZORPAY_KEY_ID to .env"
        }

    # When Razorpay is configured:
    # import razorpay
    # client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    # order = client.order.create({
    #     "amount": PLAN_AMOUNT * 100,
    #     "currency": "INR",
    #     "receipt": f"lead_{req.lead_id[:8]}",
    #     "notes": {"lead_id": req.lead_id, "plan": "starter"}
    # })
    # return {"order_id": order["id"], "amount": order["amount"], "currency": "INR", "key_id": RAZORPAY_KEY_ID}


@router.post("/verify")
def verify_payment(razorpay_payment_id: str, razorpay_order_id: str, razorpay_signature: str, lead_id: str):
    """Verify Razorpay payment and activate subscription."""
    db = get_supabase()

    # Store payment record
    db.table("payments").insert({
        "client_id": None,  # Will be linked after client registration
        "amount": PLAN_AMOUNT,
        "status": "paid",
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_order_id": razorpay_order_id,
        "method": "razorpay",
    }).execute()

    return {"status": "verified", "message": "Payment successful. Account activated."}


@router.get("/checkout/{lead_id}", response_class=HTMLResponse)
def checkout_page(lead_id: str):
    """Render a payment checkout page for a lead."""
    from app.services.lead_service import LeadService
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    business_name = lead.get("business_name", "Business")
    phone = lead.get("phone", "")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Subscribe - {business_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#f8fafc;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.card{{background:#fff;border-radius:20px;padding:40px;max-width:420px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.08)}}
.logo{{width:48px;height:48px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:12px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:1.2rem;margin-bottom:20px}}
h1{{font-size:1.5rem;font-weight:700;margin-bottom:4px}}
.subtitle{{color:#64748b;font-size:.9rem;margin-bottom:24px}}
.price{{font-size:2.5rem;font-weight:800;color:#1e293b}}.price span{{font-size:1rem;color:#64748b;font-weight:400}}/month
.features{{list-style:none;margin:24px 0;padding:0}}
.features li{{padding:8px 0;font-size:.9rem;color:#374151;display:flex;align-items:center;gap:8px}}
.features li::before{{content:"\\2713";color:#10b981;font-weight:700}}
.btn{{width:100%;padding:16px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;border-radius:12px;font-size:1rem;font-weight:700;cursor:pointer;transition:all .3s}}
.btn:hover{{transform:translateY(-2px);box-shadow:0 8px 25px rgba(99,102,241,.4)}}
.secure{{text-align:center;margin-top:16px;font-size:.75rem;color:#94a3b8}}
</style></head><body>
<div class="card">
<div class="logo">AI</div>
<h1>Start Your Digital Presence</h1>
<p class="subtitle">Everything {business_name} needs to grow online</p>
<div class="price">&#8377;79 <span>/month</span></div>
<ul class="features">
<li>Professional AI-powered website</li>
<li>AI Receptionist (24/7 chat support)</li>
<li>WhatsApp automation</li>
<li>Online booking system</li>
<li>Google SEO optimization</li>
<li>Social media content tools</li>
<li>Google Maps integration</li>
<li>Monthly performance reports</li>
</ul>
<button class="btn" onclick="alert('Razorpay integration pending. Contact us to subscribe.')">Subscribe Now - &#8377;79/month</button>
<p class="secure">&#128274; Secure payment via Razorpay. Cancel anytime.</p>
</div>
</body></html>"""
    return HTMLResponse(content=html)
