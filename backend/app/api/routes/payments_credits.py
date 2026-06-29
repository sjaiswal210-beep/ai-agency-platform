from __future__ import annotations
import hmac
import hashlib
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.supabase import get_supabase
from app.services.credits import get_credits
from app.core.logging import get_logger

router = APIRouter(prefix="/api/credits", tags=["credits"])
logger = get_logger(__name__)


def _add_credit(website_id: str, amount: float) -> float:
    db = get_supabase()
    bal = get_credits(website_id)
    new_bal = bal + amount
    try:
        existing = db.table("owner_credits").select("id").eq("website_id", website_id).limit(1).execute()
        if existing.data:
            db.table("owner_credits").update({"balance": new_bal}).eq("website_id", website_id).execute()
        else:
            db.table("owner_credits").insert({"website_id": website_id, "balance": new_bal}).execute()
    except Exception as e:
        logger.warning(f"add_credit failed: {e}")
    return new_bal


class CreateOrder(BaseModel):
    website_id: str
    amount: int


class VerifyPayment(BaseModel):
    website_id: str
    amount: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/create-order")
async def create_order(req: CreateOrder):
    s = get_settings()
    key = getattr(s, "razorpay_key_id", "") or ""
    secret = getattr(s, "razorpay_key_secret", "") or ""
    if not key or not secret:
        raise HTTPException(503, "Payments not configured yet. Please contact support.")
    if req.amount < 10 or req.amount > 5000:
        raise HTTPException(400, "Amount must be between Rs.10 and Rs.5000")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.razorpay.com/v1/orders",
            auth=(key, secret),
            json={"amount": req.amount * 100, "currency": "INR", "notes": {"website_id": req.website_id}},
            timeout=20,
        )
    if resp.status_code not in (200, 201):
        logger.warning(f"razorpay order failed: {resp.text[:200]}")
        raise HTTPException(500, "Could not create payment order")
    order = resp.json()
    return {"order_id": order["id"], "amount": order["amount"], "key_id": key}


@router.post("/verify")
async def verify(req: VerifyPayment):
    s = get_settings()
    secret = getattr(s, "razorpay_key_secret", "") or ""
    if not secret:
        raise HTTPException(503, "Payments not configured")
    body = f"{req.razorpay_order_id}|{req.razorpay_payment_id}"
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, req.razorpay_signature):
        raise HTTPException(400, "Payment verification failed")
    new_bal = _add_credit(req.website_id, float(req.amount))
    try:
        get_supabase().table("credit_purchases").insert({
            "website_id": req.website_id,
            "amount": req.amount,
            "payment_id": req.razorpay_payment_id,
            "order_id": req.razorpay_order_id,
        }).execute()
    except Exception:
        pass
    return {"status": "success", "credits": new_bal}


@router.get("/{website_id}/buy", response_class=HTMLResponse)
async def buy_page(website_id: str):
    bal = get_credits(website_id)
    return HTMLResponse(content=_PAGE.replace("__WID__", website_id).replace("__BAL__", str(int(bal))))


_PAGE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Buy Credits - City Maps</title>
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
<style>
body{font-family:sans-serif;background:#020817;color:#fff;margin:0;padding:24px;max-width:480px;margin:0 auto}
h1{font-size:1.3rem;margin:8px 0}
.bal{background:#0f172a;border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:18px;text-align:center;margin:16px 0}
.bal .n{font-size:2rem;font-weight:900;color:#22c55e}
.bal .l{font-size:.75rem;color:#64748b}
.pks{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:16px 0}
.pk{background:#0f172a;border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:16px 8px;text-align:center;cursor:pointer;transition:all .2s}
.pk:hover,.pk.on{border-color:#6366f1;background:#1e1b4b}
.pk .a{font-size:1.2rem;font-weight:800}
.pk .b{font-size:.65rem;color:#64748b;margin-top:2px}
.btn{width:100%;padding:15px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;border-radius:12px;color:#fff;font-size:.95rem;font-weight:800;cursor:pointer;margin-top:8px}
.note{font-size:.7rem;color:#64748b;text-align:center;margin-top:14px;line-height:1.5}
</style></head><body>
<h1>Buy Credits</h1>
<p style="font-size:.8rem;color:#94a3b8">Use credits for AI logos (Rs.5), AI videos (Rs.5) and voice calls (Rs.1).</p>
<div class="bal"><div class="n">Rs.__BAL__</div><div class="l">Current balance</div></div>
<div class="pks">
<div class="pk on" data-amt="50"><div class="a">Rs.50</div><div class="b">starter</div></div>
<div class="pk" data-amt="100"><div class="a">Rs.100</div><div class="b">popular</div></div>
<div class="pk" data-amt="500"><div class="a">Rs.500</div><div class="b">best value</div></div>
</div>
<button class="btn" id="payBtn" onclick="pay()">Add Credits</button>
<p class="note">Secure payment via Razorpay. Credits are added instantly after payment.</p>
<script>
var WID="__WID__";var amt=50;
document.querySelectorAll(".pk").forEach(function(p){p.onclick=function(){document.querySelectorAll(".pk").forEach(function(x){x.classList.remove("on")});p.classList.add("on");amt=parseInt(p.dataset.amt);}});
async function pay(){
  var btn=document.getElementById("payBtn");btn.disabled=true;btn.textContent="Please wait...";
  try{
    var r=await fetch("/api/credits/create-order",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({website_id:WID,amount:amt})});
    if(!r.ok){var e=await r.json();alert(e.detail||"Could not start payment");btn.disabled=false;btn.textContent="Add Credits";return;}
    var o=await r.json();
    var rzp=new Razorpay({
      key:o.key_id,amount:o.amount,currency:"INR",name:"City Maps",description:"Wallet credits",order_id:o.order_id,
      handler:function(resp){
        fetch("/api/credits/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({website_id:WID,amount:amt,razorpay_order_id:resp.razorpay_order_id,razorpay_payment_id:resp.razorpay_payment_id,razorpay_signature:resp.razorpay_signature})}).then(function(v){return v.json()}).then(function(d){
          if(d.status==="success"){document.querySelector(".bal .n").textContent="Rs."+Math.round(d.credits);alert("Credits added! New balance: Rs."+Math.round(d.credits));}
          else{alert("Payment verification failed. Contact support if charged.");}
        });
      },
      theme:{color:"#6366f1"}
    });
    rzp.open();
    btn.disabled=false;btn.textContent="Add Credits";
  }catch(e){alert("Error starting payment");btn.disabled=false;btn.textContent="Add Credits";}
}
</script></body></html>"""