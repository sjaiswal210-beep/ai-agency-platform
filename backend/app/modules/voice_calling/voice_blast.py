"""
Voice Blast Module - Scripted outbound calls via Vobiz
No AI needed - just plays pre-generated Hindi TTS audio with business name
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.core.supabase import get_supabase
from datetime import datetime
import httpx
import os
import hashlib

router = APIRouter(prefix="/api/voice-blast", tags=["voice-blast"])

# Vobiz config - reads from voice_call_config in Supabase
BACKEND_URL = os.environ.get("BACKEND_URL", "https://ai-agency-platform.onrender.com")


def get_vobiz_config():
    """Get Vobiz credentials from voice_call_config."""
    db = get_supabase()
    result = db.table("voice_call_config").select("*").eq("is_active", True).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Voice calling not configured")
    config = result.data[0]
    return {
        "auth_id": os.environ.get("VOBIZ_AUTH_ID", ""),
        "auth_token": os.environ.get("VOBIZ_AUTH_TOKEN", ""),
        "from_number": config.get("from_phone_number", "+918071579115"),
    }


def generate_hindi_script(business_name: str, owner_name: str = "", category: str = "") -> str:
    """Generate the Hindi call script with business name."""
    name = owner_name if owner_name else "Sir"
    script = (
        f"Namaste {name} ji! "
        f"Main Priya bol rahi hoon City Maps Online se. "
        f"Aapke business {business_name} ke liye humne ek professional website bilkul free mein taiyaar ki hai. "
        f"Is website se aapka business Google pe dikhai dega, "
        f"WhatsApp se direct orders aa sakte hain, "
        f"aur aapke products ka catalog bhi hoga. "
        f"Yeh sab bilkul free hai. "
        f"Agar aap interested hain toh hum aapko WhatsApp pe poori details bhej denge. "
        f"Dhanyavaad ji, aapka din shubh ho!"
    )
    return script


async def generate_tts_audio(text: str) -> str:
    """Generate Hindi TTS audio using Deepgram and return the public URL."""
    
    # Create a hash-based filename for caching
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    filename = f"voice_blast_{text_hash}.mp3"
    filepath = f"/app/static/audio/{filename}"
    
    # Check if already generated (cache)
    if os.path.exists(filepath):
        return f"{BACKEND_URL}/static/audio/{filename}"
    
    os.makedirs("/app/static/audio", exist_ok=True)
    
    # Use Deepgram TTS API
    deepgram_key = os.environ.get("DEEPGRAM_API_KEY", "da29097e0c0919ebb8317a16c7ba22fa925c724b")
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.deepgram.com/v1/speak?model=aura-asteria-en",
            headers={
                "Authorization": f"Token {deepgram_key}",
                "Content-Type": "application/json",
            },
            json={"text": text},
        )
        if response.status_code != 200:
            # Fallback to gTTS if Deepgram fails
            from gtts import gTTS
            tts = gTTS(text=text, lang='hi', slow=False)
            tts.save(filepath)
        else:
            with open(filepath, "wb") as f:
                f.write(response.content)
    
    return f"{BACKEND_URL}/static/audio/{filename}"


async def make_vobiz_call(phone: str, audio_url: str, config: dict) -> dict:
    """Make an outbound call via Vobiz that plays an audio file."""
    # Clean phone number
    phone_clean = phone.replace("-", "").replace(" ", "").replace("+", "")
    if len(phone_clean) == 10:
        phone_clean = "91" + phone_clean
    
    from_number = config["from_number"].replace("+", "")
    
    # The answer_url will be our endpoint that returns XML to play audio
    answer_url = f"{BACKEND_URL}/api/voice-blast/play-audio?audio_url={audio_url}"
    
    # Vobiz Call API
    endpoint = f"https://api.vobiz.ai/api/v1/Account/{config['auth_id']}/Call/"
    headers = {
        "X-Auth-ID": config["auth_id"],
        "X-Auth-Token": config["auth_token"],
        "Content-Type": "application/json",
    }
    data = {
        "from": from_number,
        "to": phone_clean,
        "answer_url": answer_url,
        "answer_method": "GET",
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(endpoint, json=data, headers=headers)
        if response.status_code not in (200, 201):
            raise HTTPException(500, f"Vobiz error: {response.text[:200]}")
        return response.json()


# ============ ENDPOINTS ============

@router.get("/play-audio")
async def play_audio_xml(audio_url: str):
    """Returns Vobiz XML to play an audio file. Called by Vobiz when call is answered."""
    from fastapi.responses import Response
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Hangup/>
</Response>'''
    return Response(content=xml, media_type="application/xml")


@router.post("/call")
async def blast_call(data: dict, background_tasks: BackgroundTasks):
    """Make a single scripted voice call to a business."""
    phone = data.get("phone")
    business_name = data.get("business_name", "")
    owner_name = data.get("owner_name", "")
    category = data.get("category", "")
    lead_id = data.get("lead_id")
    
    if not phone:
        raise HTTPException(400, "Phone number required")
    if not business_name:
        raise HTTPException(400, "Business name required")
    
    # Generate script and audio
    script = generate_hindi_script(business_name, owner_name, category)
    audio_url = await generate_tts_audio(script)
    
    # Make the call
    config = get_vobiz_config()
    result = await make_vobiz_call(phone, audio_url, config)
    
    # Log the call
    db = get_supabase()
    org_id = data.get("organization_id")
    if not org_id:
        # Get default org from voice_call_config
        cfg = db.table("voice_call_config").select("organization_id").eq("is_active", True).limit(1).execute()
        org_id = cfg.data[0]["organization_id"] if cfg.data else None
    db.table("voice_calls").insert({
        "organization_id": org_id,
        "lead_id": lead_id,
        "bolna_execution_id": result.get("request_uuid"),
        "recipient_phone": phone,
        "recipient_name": owner_name,
        "business_name": business_name,
        "business_category": category,
        "call_status": "queued",
        "trigger_type": data.get("trigger_type", "manual"),
        "called_at": datetime.utcnow().isoformat(),
    }).execute()
    
    return {
        "message": "Call initiated",
        "call_id": result.get("request_uuid"),
        "audio_url": audio_url,
        "script": script,
    }


@router.post("/batch")
async def blast_batch(data: dict):
    """Call multiple leads with scripted messages."""
    lead_ids = data.get("lead_ids", [])
    if not lead_ids:
        raise HTTPException(400, "Provide lead_ids array")
    
    db = get_supabase()
    leads = db.table("leads").select("*").in_("id", lead_ids).execute()
    
    config = get_vobiz_config()
    results = {"called": 0, "failed": 0, "errors": []}
    
    for lead in (leads.data or []):
        phone = lead.get("phone", "")
        if not phone or len(phone.replace("-", "").replace(" ", "")) < 10:
            results["failed"] += 1
            continue
        try:
            business_name = lead.get("business_name", "Business")
            owner_name = lead.get("owner_name", "")
            script = generate_hindi_script(business_name, owner_name, lead.get("category", ""))
            audio_url = await generate_tts_audio(script)
            result = await make_vobiz_call(phone, audio_url, config)
            
            db.table("voice_calls").insert({
                "lead_id": lead["id"],
                "bolna_execution_id": result.get("request_uuid"),
                "recipient_phone": phone,
                "recipient_name": owner_name,
                "business_name": business_name,
                "call_status": "queued",
                "trigger_type": "batch",
                "called_at": datetime.utcnow().isoformat(),
            }).execute()
            results["called"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{lead.get('business_name')}: {str(e)[:50]}")
    
    return results


@router.post("/auto-call-new-leads")
async def auto_blast_new_leads():
    """Auto-call new leads that haven't been called yet."""
    db = get_supabase()
    
    # Get leads with phone that haven't been called
    called_leads = db.table("voice_calls").select("lead_id").execute()
    called_ids = [c["lead_id"] for c in (called_leads.data or []) if c.get("lead_id")]
    
    leads = db.table("leads").select("*").eq("status", "new").not_.is_("phone", "null").limit(5).execute()
    new_leads = [l for l in (leads.data or []) if l["id"] not in called_ids]
    
    if not new_leads:
        return {"message": "No new leads to call"}
    
    config = get_vobiz_config()
    results = {"called": 0, "failed": 0}
    
    for lead in new_leads[:3]:
        phone = lead.get("phone", "")
        if not phone or len(phone.replace("-", "").replace(" ", "")) < 10:
            continue
        try:
            script = generate_hindi_script(
                lead.get("business_name", "Business"),
                lead.get("owner_name", ""),
                lead.get("category", "")
            )
            audio_url = await generate_tts_audio(script)
            await make_vobiz_call(phone, audio_url, config)
            results["called"] += 1
        except Exception:
            results["failed"] += 1
    
    return {"message": f"Called {results['called']} leads", **results}