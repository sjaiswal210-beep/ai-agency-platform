"""
Owner Voice Broadcast - Business owners can send scripted voice calls to their customers.
Free: 5 calls LIFETIME per business (no renewal). After that: Rs.1/call (deducted from credits).
Calls are max 30 seconds (short informational messages).
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from datetime import datetime, date
import httpx
import hashlib
import os

router = APIRouter(prefix="/api/owner-broadcast", tags=["owner-broadcast"])

FREE_CALLS_LIFETIME = 5  # lifetime free calls per business (NO daily/auto renewal)
COST_PER_CALL = 1  # Rs.1 per call after free tier


def _get_total_calls(db, website_id: str) -> int:
    """Count calls made today by this business."""
    today = date.today().isoformat()
    try:
        result = db.table("owner_broadcast_log").select("*", count="exact").eq("website_id", website_id).gte("created_at", today).execute()
        return result.count or 0
    except Exception:
        return 0


def _get_credits(db, website_id: str) -> float:
    """Get remaining credits for this business."""
    try:
        result = db.table("owner_credits").select("balance").eq("website_id", website_id).limit(1).execute()
        if result.data:
            return float(result.data[0].get("balance", 0))
    except Exception:
        pass
    return 0.0


def _deduct_credit(db, website_id: str, amount: float):
    """Deduct credit from business account."""
    current = _get_credits(db, website_id)
    new_balance = max(0, current - amount)
    try:
        existing = db.table("owner_credits").select("id").eq("website_id", website_id).limit(1).execute()
        if existing.data:
            db.table("owner_credits").update({"balance": new_balance}).eq("website_id", website_id).execute()
        else:
            db.table("owner_credits").insert({"website_id": website_id, "balance": new_balance}).execute()
    except Exception:
        pass


async def _generate_audio(text: str, lang: str = "hi") -> str:
    """Generate TTS audio and return public URL."""
    from gtts import gTTS
    BACKEND_URL = os.environ.get("BACKEND_URL", "https://ai-agency-platform.onrender.com")
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    filename = f"broadcast_{text_hash}.mp3"
    filepath = f"/app/static/audio/{filename}"
    if not os.path.exists(filepath):
        os.makedirs("/app/static/audio", exist_ok=True)
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filepath)
    return f"{BACKEND_URL}/static/audio/{filename}"


async def _make_call(phone: str, audio_url: str) -> dict:
    """Make outbound call via Vobiz."""
    auth_id = os.environ.get("VOBIZ_AUTH_ID", "")
    auth_token = os.environ.get("VOBIZ_AUTH_TOKEN", "")
    from_number = "918071579115"
    BACKEND_URL = os.environ.get("BACKEND_URL", "https://ai-agency-platform.onrender.com")

    phone_clean = phone.replace("-", "").replace(" ", "").replace("+", "")
    if len(phone_clean) == 10:
        phone_clean = "91" + phone_clean

    answer_url = f"{BACKEND_URL}/api/voice-blast/play-audio?audio_url={audio_url}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://api.vobiz.ai/api/v1/Account/{auth_id}/Call/",
            headers={"X-Auth-ID": auth_id, "X-Auth-Token": auth_token, "Content-Type": "application/json"},
            json={"from": from_number, "to": phone_clean, "answer_url": answer_url, "answer_method": "GET"},
        )
        if response.status_code not in (200, 201):
            raise HTTPException(500, f"Call failed: {response.text[:100]}")
        return response.json()


@router.get("/{website_id}", response_class=HTMLResponse)
def broadcast_page(website_id: str):
    """Owner broadcast page - type script, enter number, hit call."""
    db = get_supabase()
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"

    used_calls = _get_total_calls(db, website_id)
    credits = _get_credits(db, website_id)
    remaining_free = max(0, FREE_CALLS_LIFETIME - used_calls)
    content = website.get("content", {}) or {}
    colors = content.get("color_scheme", {}) or {}
    primary = colors.get("primary", "#7C3AED")

    html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0">
<title>Voice Broadcast - {business_name}</title>
<meta name="theme-color" content="{primary}">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
:root{{--p:{primary}}}
body{{font-family:'Plus Jakarta Sans',system-ui,sans-serif;background:#f0f3f8;color:#0f172a;padding-bottom:24px;-webkit-overflow-scrolling:touch}}
.appbar{{position:sticky;top:0;z-index:50;background:linear-gradient(135deg,var(--p),color-mix(in srgb,var(--p) 70%,#000));color:#fff;padding:16px 18px;box-shadow:0 2px 12px rgba(0,0,0,.12)}}
.appbar h1{{font-size:1.05rem;font-weight:800}}.appbar p{{font-size:.72rem;opacity:.85;margin-top:2px}}
.wrap{{max-width:560px;margin:0 auto;padding:16px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}}
.stat{{background:#fff;border-radius:14px;padding:14px 8px;text-align:center;border:1px solid #e8edf3}}
.stat .n{{font-size:1.3rem;font-weight:800;color:var(--p)}}.stat .l{{font-size:.6rem;color:#64748b;margin-top:2px;font-weight:600;text-transform:uppercase}}
.card{{background:#fff;border-radius:16px;padding:18px;border:1px solid #e8edf3;margin-bottom:14px}}
.card h3{{font-size:.85rem;font-weight:800;margin-bottom:12px;color:#0f172a}}
label{{display:block;font-size:.7rem;font-weight:700;color:#64748b;margin-bottom:5px;margin-top:12px}}
input,textarea,select{{width:100%;padding:12px;border:1px solid #e8edf3;border-radius:12px;font-size:.9rem;background:#f6f8fb;outline:none}}
input:focus,textarea:focus{{border-color:var(--p);background:#fff}}
textarea{{min-height:80px;resize:vertical}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.btn{{width:100%;padding:14px;background:var(--p);color:#fff;border:none;border-radius:14px;font-size:.95rem;font-weight:800;cursor:pointer;margin-top:14px}}
.btn:active{{transform:scale(.98)}}.btn:disabled{{opacity:.5;cursor:wait}}
.info{{background:#fffbeb;border:1px solid #fde68a;padding:12px;border-radius:12px;font-size:.74rem;color:#92400e;margin-bottom:14px}}
.toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(20px);background:#0f172a;color:#fff;padding:10px 20px;border-radius:50px;font-size:.78rem;font-weight:600;z-index:200;opacity:0;transition:all .3s;pointer-events:none}}
.toast.show{{opacity:1;transform:translateX(-50%) translateY(0)}}
</style></head><body>
<div class="appbar">
<h1>Voice Broadcast</h1>
<p>{business_name} &bull; Send voice messages to your customers</p>
</div>
<div class="wrap">
<div class="stats">
<div class="stat"><div class="n" id="s-free">{remaining_free}</div><div class="l">Free Left</div></div>
<div class="stat"><div class="n" id="s-used">{used_calls}</div><div class="l">Used</div></div>
<div class="stat"><div class="n" id="s-cred">Rs.{credits:.0f}</div><div class="l">Credits</div></div>
</div>
<div class="info">Free: {FREE_CALLS_LIFETIME} calls lifetime (one-time). After that Rs.{COST_PER_CALL}/call (max 30 sec each). <a href="/api/panel/{website_id}" style="color:#7c3aed;font-weight:700">Buy Credits</a></div>
<div class="card">
<h3>Send Voice Message</h3>
<label>Message Script (Hindi/English)</label>
<textarea id="script" placeholder="e.g. Namaste! Aaj hamare yahan 20% discount hai sabhi items pe. Jaldi aayein!">{business_name} ki taraf se ek khaas message: </textarea>
<label>Customer Phone Number</label>
<input id="phone" type="tel" placeholder="+91 or 10-digit number">
<div class="row">
<div><label>Language</label><select id="lang"><option value="hi">Hindi</option><option value="mr">Marathi</option><option value="en">English</option></select></div>
<div><label>Speed</label><select id="speed"><option value="1.0">Normal</option><option value="1.2">Fast</option></select></div>
</div>
<button class="btn" id="callBtn" onclick="makeCall()">Call Now</button>
</div>
</div>
<div class="toast" id="toast"></div>
<script>
var WID="{website_id}";
var API="https://ai-agency-platform.onrender.com";
function toast(m){{var t=document.getElementById("toast");t.textContent=m;t.classList.add("show");setTimeout(function(){{t.classList.remove("show")}},2500);}}
async function makeCall(){{
  var script=document.getElementById("script").value.trim();
  var phone=document.getElementById("phone").value.trim();
  var lang=document.getElementById("lang").value;
  if(!script||!phone){{toast("Enter script and phone number");return;}}
  if(phone.replace(/[^0-9]/g,"").length<10){{toast("Invalid phone number");return;}}
  var btn=document.getElementById("callBtn");btn.disabled=true;btn.textContent="Calling...";
  try{{
    var r=await fetch(API+"/api/owner-broadcast/"+WID+"/call",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{script:script,phone:phone,lang:lang}})}});
    var d=await r.json();
    if(r.ok){{toast("Call initiated!");document.getElementById("s-used").textContent=parseInt(document.getElementById("s-used").textContent)+1;var fr=parseInt(document.getElementById("s-free").textContent);if(fr>0)document.getElementById("s-free").textContent=fr-1;}}
    else{{toast(d.detail||"Failed");}}
  }}catch(e){{toast("Error. Try again");}}
  btn.disabled=false;btn.textContent="Call Now";
}}
</script></body></html>'''
    return HTMLResponse(content=html)


@router.post("/{website_id}/call")
async def owner_make_call(website_id: str, data: dict):
    """Business owner initiates a voice call to their customer."""
    db = get_supabase()
    script = data.get("script", "").strip()
    phone = data.get("phone", "").strip()
    lang = data.get("lang", "hi")

    if not script or not phone:
        raise HTTPException(400, "Script and phone required")
    if len(script) > 500:
        raise HTTPException(400, "Script too long (max 500 chars for 30 sec)")

    # Check limits
    used_calls = _get_total_calls(db, website_id)
    if used_calls < FREE_CALLS_LIFETIME:
        # Free call
        pass
    else:
        # Check credits
        credits = _get_credits(db, website_id)
        if credits < COST_PER_CALL:
            raise HTTPException(402, f"No credits. Buy credits to make more calls. Your {FREE_CALLS_LIFETIME} lifetime free calls are used.")
        _deduct_credit(db, website_id, COST_PER_CALL)

    # Generate audio
    audio_url = await _generate_audio(script, lang)

    # Make the call
    result = await _make_call(phone, audio_url)

    # Log the call
    try:
        db.table("owner_broadcast_log").insert({
            "website_id": website_id,
            "phone": phone,
            "script": script[:200],
            "call_id": result.get("request_uuid", ""),
            "cost": 0 if used_calls < FREE_CALLS_LIFETIME else COST_PER_CALL,
        }).execute()
    except Exception:
        pass

    return {"message": "Call initiated", "call_id": result.get("request_uuid", ""), "free_remaining": max(0, FREE_CALLS_LIFETIME - used_calls - 1)}