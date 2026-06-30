from __future__ import annotations
import os
try:
    import replicate
except ImportError:
    replicate = None
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
from app.core.logging import get_logger
import json

router = APIRouter(prefix="/logo-gen", tags=["logo-generation"])
logger = get_logger(__name__)

REPLICATE_TOKEN = os.environ.get("REPLICATE_TOKEN", "")

LOGO_COST = 5  # Rs.5 per AI logo, charged to the business credits


def _get_credits(website_id: str) -> float:
    from app.core.supabase import get_supabase
    try:
        r = get_supabase().table("owner_credits").select("balance").eq("website_id", website_id).limit(1).execute()
        return float(r.data[0]["balance"]) if r.data else 0.0
    except Exception:
        return 0.0


def _deduct_credit(website_id: str, amount: float):
    from app.core.supabase import get_supabase
    db = get_supabase()
    bal = _get_credits(website_id)
    new_bal = max(0, bal - amount)
    try:
        existing = db.table("owner_credits").select("id").eq("website_id", website_id).limit(1).execute()
        if existing.data:
            db.table("owner_credits").update({"balance": new_bal}).eq("website_id", website_id).execute()
        else:
            db.table("owner_credits").insert({"website_id": website_id, "balance": new_bal}).execute()
    except Exception:
        pass


async def _pollinations_logo(prompt: str) -> str:
    """Free AI image logo via Pollinations (no API key)."""
    import urllib.parse
    enc = urllib.parse.quote(prompt[:300])
    return f"https://image.pollinations.ai/prompt/{enc}?width=900&height=300&nologo=true"


class LogoGenRequest(BaseModel):
    style: str = "modern"  # modern, minimal, vintage, playful, luxury, bold


@router.post("/{website_id}/generate")
async def generate_image_logo(website_id: str, req: LogoGenRequest):
    """Generate an AI image logo using FLUX model."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    content = website.get("content", {})
    if "raw_content" in content:
        raw = content["raw_content"]
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        try:
            content = json.loads(raw)
        except json.JSONDecodeError:
            pass
    colors = content.get("color_scheme", {"primary": "#6366f1"})
    primary = colors.get("primary", "#6366f1")

    # Generate a logo prompt using AI
    prompt_gen = f"""Create a text-to-image prompt for generating a professional logo:
Business: {business_name}
Category: {category}
Style: {req.style}
Primary color: {primary}

Write a detailed prompt for an AI image generator to create a logo. Include:
- Logo type (icon + text, icon only, lettermark, etc.)
- Visual elements relevant to {category}
- Color scheme
- Style ({req.style})
- Background: white/transparent
- Professional quality

Return ONLY the image generation prompt, 1-2 sentences. No explanation."""

    logo_prompt = await chat_completion([{"role": "user", "content": prompt_gen}])
    logo_prompt = logo_prompt.strip().strip('"')

    # Add logo-specific keywords
    full_prompt = f"Professional horizontal rectangular business logo design, {logo_prompt}, wide format, clean vector style, white background, high quality, minimalist, includes business name text in the logo"

    logger.info("Generating logo", business=business_name, style=req.style)

    # Charge Rs.5 only when payments are live (Razorpay configured). Pre-launch: free.
    from app.core.config import get_settings as _gs
    _payments_live = bool(getattr(_gs(), "razorpay_key_id", ""))
    if _payments_live and _get_credits(website_id) < LOGO_COST:
        raise HTTPException(402, f"Logo costs Rs.{LOGO_COST}. Please buy credits.")

    logo_url = ""
    # 1. Try Replicate FLUX (premium) if configured
    if REPLICATE_TOKEN and replicate is not None:
        try:
            client = replicate.Client(api_token=REPLICATE_TOKEN)
            output = client.run(
                "black-forest-labs/flux-schnell",
                input={"prompt": full_prompt, "num_outputs": 1, "aspect_ratio": "3:1", "output_format": "png"},
            )
            if isinstance(output, list) and len(output) > 0:
                logo_url = str(output[0])
            elif hasattr(output, "url"):
                logo_url = output.url
            else:
                logo_url = str(output)
        except Exception as e:
            logger.warning(f"FLUX failed, using free fallback: {e}")

    # 2. Free fallback: Pollinations AI (always works, no key, no admin cost)
    if not logo_url:
        logo_url = await _pollinations_logo(full_prompt)

    # Deduct only when payments are live
    if _payments_live:
        _deduct_credit(website_id, LOGO_COST)

    return {
        "logo_url": logo_url,
        "prompt": full_prompt,
        "business": business_name,
        "style": req.style,
        "credits_left": _get_credits(website_id),
    }


@router.get("/{website_id}/preview", response_class=HTMLResponse)
async def preview_logos(website_id: str):
    """AI logo maker page."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    credits = _get_credits(website_id)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI Logo Maker - {business_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#020817;color:#fff;padding:20px;max-width:560px;margin:0 auto;min-height:100vh}}
.hero{{text-align:center;margin-bottom:18px}}
.hero h1{{font-size:1.45rem;font-weight:800;background:linear-gradient(135deg,#a78bfa,#22d3ee);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero p{{font-size:.8rem;color:#94a3b8;margin-top:4px}}
.pill{{display:inline-block;margin-top:10px;background:rgba(34,197,94,.12);color:#22c55e;border:1px solid rgba(34,197,94,.3);padding:5px 14px;border-radius:999px;font-size:.72rem;font-weight:700}}
.label{{font-size:.68rem;font-weight:800;color:#7c8aa5;text-transform:uppercase;letter-spacing:.1em;margin:20px 0 10px}}
.styles{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.style-btn{{background:rgba(255,255,255,.03);border:1.5px solid rgba(255,255,255,.08);border-radius:16px;padding:16px 8px;text-align:center;cursor:pointer;transition:all .2s}}
.style-btn:hover{{border-color:rgba(124,58,237,.5)}}
.style-btn.active{{border-color:#7c3aed;background:rgba(124,58,237,.14);box-shadow:0 0 20px rgba(124,58,237,.18)}}
.style-btn .ic{{font-size:1.6rem;display:block;margin-bottom:6px}}
.style-btn .nm{{font-size:.72rem;font-weight:600;color:#e2e8f0}}
.gen-btn{{width:100%;margin-top:22px;padding:16px;background:linear-gradient(135deg,#7c3aed,#6366f1);border:none;border-radius:14px;color:#fff;font-size:.95rem;font-weight:800;cursor:pointer;box-shadow:0 8px 24px rgba(124,58,237,.3)}}
.gen-btn:disabled{{opacity:.6}}
#result{{margin-top:24px}}
.logo-card{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:16px;text-align:center}}
.logo-card img{{width:100%;max-width:380px;height:auto;border-radius:12px;background:#fff;padding:10px}}
.use-btn{{margin-top:14px;display:inline-block;background:#10b981;color:#fff;border:none;padding:12px 28px;border-radius:10px;font-size:.85rem;font-weight:700;cursor:pointer;text-decoration:none}}
.loading{{text-align:center;color:#a78bfa;padding:34px;font-size:.85rem}}
.spin{{width:38px;height:38px;border:3px solid rgba(124,58,237,.2);border-top:3px solid #7c3aed;border-radius:50%;animation:sp 1s linear infinite;margin:0 auto 12px}}
@keyframes sp{{to{{transform:rotate(360deg)}}}}
</style></head><body>
<div class="hero">
<h1>AI Logo Maker</h1>
<p>{business_name}</p>
<span class="pill">&#9889; Rs.5 per logo</span>
</div>
<div class="label">Choose a style</div>
<div class="styles" id="styles">
<div class="style-btn active" data-style="modern"><span class="ic">&#127919;</span><span class="nm">Modern</span></div>
<div class="style-btn" data-style="minimal"><span class="ic">&#9633;</span><span class="nm">Minimal</span></div>
<div class="style-btn" data-style="vintage"><span class="ic">&#127963;</span><span class="nm">Vintage</span></div>
<div class="style-btn" data-style="playful"><span class="ic">&#127912;</span><span class="nm">Playful</span></div>
<div class="style-btn" data-style="luxury"><span class="ic">&#128081;</span><span class="nm">Luxury</span></div>
<div class="style-btn" data-style="bold"><span class="ic">&#128170;</span><span class="nm">Bold</span></div>
</div>
<button class="gen-btn" id="genBtn" onclick="generateLogo()">Generate AI Logo &mdash; Rs.5</button>
<div id="result"></div>
<script>
let selectedStyle='modern';
document.querySelectorAll('.style-btn').forEach(function(b){{b.onclick=function(){{document.querySelectorAll('.style-btn').forEach(function(x){{x.classList.remove('active')}});b.classList.add('active');selectedStyle=b.dataset.style;}}}});
async function useLogo(url){{
  const res=await fetch('/api/logo-gen/{website_id}/set-logo?logo_url='+encodeURIComponent(url),{{method:'POST'}});
  if(res.ok){{alert('Logo applied to your website!');}}else{{alert('Error applying logo');}}
}}
async function generateLogo(){{
  const btn=document.getElementById('genBtn');
  btn.disabled=true;btn.textContent='Starting payment...';
  try{{
    const r=await fetch('/api/credits/create-order',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{website_id:'{website_id}',amount:5}})}});
    if(r.status===503){{doGenerateLogo();return;}}
    const o=await r.json();
    if(!o.order_id){{alert(o.detail||'Could not start payment');btn.disabled=false;btn.textContent='Generate AI Logo \u2014 Rs.5';return;}}
    if(typeof Razorpay==='undefined'){{alert('Payment not ready. Refresh and try again.');btn.disabled=false;btn.textContent='Generate AI Logo \u2014 Rs.5';return;}}
    const rzp=new Razorpay({{key:o.key_id,amount:o.amount,currency:'INR',name:'City Maps',description:'AI Logo (Rs.5)',order_id:o.order_id,
      handler:function(resp){{btn.textContent='Verifying...';fetch('/api/credits/verify',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{website_id:'{website_id}',amount:5,razorpay_order_id:resp.razorpay_order_id,razorpay_payment_id:resp.razorpay_payment_id,razorpay_signature:resp.razorpay_signature}})}}).then(function(v){{return v.json()}}).then(function(d){{if(d.status==='success'){{doGenerateLogo();}}else{{alert('Payment verification failed.');btn.disabled=false;btn.textContent='Generate AI Logo \u2014 Rs.5';}}}});}},
      modal:{{ondismiss:function(){{btn.disabled=false;btn.textContent='Generate AI Logo \u2014 Rs.5';}}}},theme:{{color:'#7c3aed'}}}});
    rzp.open();
  }}catch(e){{alert('Error starting payment');btn.disabled=false;btn.textContent='Generate AI Logo \u2014 Rs.5';}}
}}
async function doGenerateLogo(){{
  const btn=document.getElementById('genBtn');const result=document.getElementById('result');
  btn.disabled=true;btn.textContent='Generating...';
  result.innerHTML='<div class="loading"><div class="spin"></div>Creating your logo...</div>';
  try{{
    const res=await fetch('/api/logo-gen/{website_id}/generate',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{style:selectedStyle}})}});
    const data=await res.json();
    if(data.logo_url){{
      result.innerHTML='<div class="logo-card"><img src="'+data.logo_url+'" alt="Logo"><div style="margin-top:8px;font-size:.72rem;color:#94a3b8;text-transform:capitalize">'+selectedStyle+' style</div><a class="use-btn" href="'+data.logo_url+'" download style="background:#6366f1;margin-right:8px">Download</a><button class="use-btn" onclick="useLogo(\\''+data.logo_url+'\\')">Use This Logo</button></div>';
    }}else{{
      result.innerHTML='<p style="color:#ef4444;text-align:center">'+(data.detail||'Failed')+'</p>';
    }}
  }}catch(e){{result.innerHTML='<p style="color:#ef4444;text-align:center">Error generating logo</p>';}}
  btn.disabled=false;btn.textContent='Generate Another \u2014 Rs.5';
}}
</script>
</body></html>"""
    return HTMLResponse(content=html)

@router.post("/{website_id}/set-logo")
async def set_logo(website_id: str, logo_url: str):
    """Set/update the logo URL for a website."""
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    content = website.get("content", {})
    if isinstance(content, dict):
        content["logo_url"] = logo_url
        service.db.table("websites").update({"content": content}).eq("id", website_id).execute()

    return {"status": "updated", "logo_url": logo_url}


@router.get("/{website_id}/current")
def get_current_logo(website_id: str):
    """Get the current logo for a website."""
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    content = website.get("content", {})
    logo_url = content.get("logo_url", "") if isinstance(content, dict) else ""
    return {"logo_url": logo_url, "has_logo": bool(logo_url)}



