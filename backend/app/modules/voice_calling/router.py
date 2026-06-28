from fastapi import APIRouter, HTTPException, Query, Request, BackgroundTasks
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date, datetime, timedelta
import httpx
import json
import os

router = APIRouter(prefix="/api/voice-calling", tags=["voice-calling"])

BOLNA_API_BASE = "https://api.bolna.ai"


# ============ HELPERS ============

def get_provider_config(config: dict) -> dict:
    """Get Bolna API base URL and headers."""
    api_key = config.get("bolna_api_key", "")
    return {
        "base_url": BOLNA_API_BASE,
        "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        "provider": "bolna"
    }


async def get_voice_config(org_id: str = None):
    db = get_supabase()
    if org_id:
        result = db.table("voice_call_config").select("*").eq("organization_id", org_id).single().execute()
    else:
        result = db.table("voice_call_config").select("*").eq("is_active", True).limit(1).single().execute()
    if not result.data:
        raise HTTPException(404, "Voice calling not configured. Add API key first.")
    config = result.data
    config["provider"] = "bolna"
    return config


def clean_phone(phone: str) -> str:
    phone = phone.replace("-", "").replace(" ", "").replace("+", "")
    if len(phone) == 10:
        phone = "91" + phone
    return "+" + phone


async def send_whatsapp_after_call(org_id: str, phone: str, name: str, business_name: str, slug: str, language: str = "hi"):
    from app.modules.whatsapp_automation.router import send_whatsapp_message
    db = get_supabase()
    script = db.table("voice_call_scripts").select("whatsapp_template").eq("language", language).eq("script_type", "sales").eq("is_default", True).limit(1).execute()
    template = "Namaste! City Maps Online se. Aapki website ready hai!"
    if script.data and script.data[0].get("whatsapp_template"):
        template = script.data[0]["whatsapp_template"]
    message = template.replace("{{name}}", name or "").replace("{{business_name}}", business_name or "").replace("{{slug}}", slug or "")
    await send_whatsapp_message(org_id=org_id, to_phone=phone, message=message, to_name=name, trigger_event="voice_call_followup")


async def make_provider_call(config: dict, phone: str, user_data: dict) -> dict:
    """Make a call using Bolna."""
    prov = get_provider_config(config)
    clean_number = clean_phone(phone)

    call_payload = {
        "agent_id": config.get("bolna_agent_id", ""),
        "recipient_phone_number": clean_number,
        "user_data": user_data,
    }
    if config.get("from_phone_number"):
        call_payload["from_phone_number"] = config["from_phone_number"]
    endpoint = f"{prov['base_url']}/call"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(endpoint, json=call_payload, headers=prov["headers"])
            if response.status_code not in (200, 201):
                raise HTTPException(500, f"API error: {response.text[:200]}")
            result = response.json()
    except httpx.TimeoutException:
        raise HTTPException(504, "Voice API timeout")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Call failed: {str(e)[:200]}")
    
    # Normalize response
    execution_id = (
        result.get("execution_id") or 
        result.get("call_id") or 
        result.get("id")
    )
    status = result.get("status", "queued")
    if status == "pending":
        status = "queued"
    return {"execution_id": str(execution_id) if execution_id else None, "status": status}


# ============ CONFIG ENDPOINTS ============

@router.get("/config")
async def get_config(org_id: Optional[str] = None):
    db = get_supabase()
    query = db.table("voice_call_config").select("id, organization_id, bolna_agent_id, from_phone_number, language, auto_call_enabled, auto_call_delay_minutes, call_start_hour, call_end_hour, max_calls_per_day, calls_made_today, is_active, created_at")
    if org_id:
        query = query.eq("organization_id", org_id)
    result = query.limit(1).execute()
    if not result.data:
        return {"configured": False}
    return {"configured": True, **result.data[0]}


@router.post("/config")
async def save_config(data: dict):
    db = get_supabase()
    config_data = {
        "organization_id": data.get("organization_id"),
        "bolna_api_key": data["bolna_api_key"],
        "bolna_agent_id": data.get("bolna_agent_id"),
        "from_phone_number": data.get("from_phone_number"),
        "language": data.get("language", "hi"),
        "auto_call_enabled": data.get("auto_call_enabled", False),
        "auto_call_delay_minutes": data.get("auto_call_delay_minutes", 30),
        "call_start_hour": data.get("call_start_hour", 10),
        "call_end_hour": data.get("call_end_hour", 19),
        "max_calls_per_day": data.get("max_calls_per_day", 50),
        "is_active": True,
    }
    db.table("voice_call_config").upsert(config_data, on_conflict="organization_id").execute()
    return {"message": "Voice calling configured successfully"}


@router.post("/config/toggle-auto")
async def toggle_auto_calling(data: dict):
    db = get_supabase()
    org_id = data.get("organization_id")
    enabled = data.get("auto_call_enabled", False)
    db.table("voice_call_config").update({"auto_call_enabled": enabled}).eq("organization_id", org_id).execute()
    return {"message": f"Auto-calling {'enabled' if enabled else 'disabled'}", "auto_call_enabled": enabled}

# ============ MAKE CALL ============

@router.post("/call")
async def make_call(data: dict, background_tasks: BackgroundTasks):
    """Make a single voice call to a lead via Bolna."""
    db = get_supabase()
    config = await get_voice_config(data.get("organization_id"))
    
    lead_id = data.get("lead_id")
    phone = data.get("phone")
    name = data.get("name", "")
    business_name = data.get("business_name", "")
    category = data.get("category", "")
    language = data.get("language", config.get("language", "hi"))
    
    if lead_id and not phone:
        lead = db.table("leads").select("*").eq("id", lead_id).single().execute()
        if not lead.data:
            raise HTTPException(404, "Lead not found")
        lead_data = lead.data
        phone = lead_data.get("phone", "")
        name = lead_data.get("owner_name") or lead_data.get("business_name", "")
        business_name = lead_data.get("business_name", "")
        category = lead_data.get("category", "")
    
    if not phone:
        raise HTTPException(400, "Phone number is required")
    
    user_data = {
        "business_name": business_name,
        "owner_name": name,
        "category": category,
        "language": language,
    }
    
    result = await make_provider_call(config, phone, user_data)
    
    call_record = {
        "organization_id": config["organization_id"],
        "lead_id": lead_id,
        "bolna_execution_id": result.get("execution_id"),
        "recipient_phone": phone,
        "recipient_name": name,
        "business_name": business_name,
        "business_category": category,
        "call_status": result.get("status", "queued"),
        "trigger_type": data.get("trigger_type", "manual"),
        "called_at": datetime.utcnow().isoformat(),
    }
    db.table("voice_calls").insert(call_record).execute()
    
    db.table("voice_call_config").update({
        "calls_made_today": (config.get("calls_made_today", 0) or 0) + 1
    }).eq("organization_id", config["organization_id"]).execute()
    
    return {
        "message": "Call initiated",
        "execution_id": result.get("execution_id"),
        "status": result.get("status", "queued"),
        "phone": phone,
        "business": business_name,
        "provider": config.get("provider", "bolna"),
    }


# ============ BATCH CALLS ============

@router.post("/batch")
async def batch_call(data: dict):
    """Call multiple leads at once."""
    db = get_supabase()
    config = await get_voice_config(data.get("organization_id"))
    
    lead_ids = data.get("lead_ids", [])
    if not lead_ids:
        raise HTTPException(400, "Provide lead_ids array")
    
    batch = db.table("voice_call_batches").insert({
        "organization_id": config["organization_id"],
        "name": data.get("name", f"Batch {datetime.now().strftime('%d-%b %H:%M')}"),
        "total_calls": len(lead_ids),
        "status": "running",
    }).execute()
    batch_id = batch.data[0]["id"]
    
    leads = db.table("leads").select("*").in_("id", lead_ids).execute()
    results = {"queued": 0, "failed": 0, "errors": []}
    
    for lead in (leads.data or []):
        phone = lead.get("phone", "")
        if not phone:
            results["failed"] += 1
            results["errors"].append(f"{lead.get('business_name')}: no phone")
            continue
        try:
            user_data = {
                "business_name": lead.get("business_name", ""),
                "owner_name": lead.get("owner_name", ""),
                "category": lead.get("category", ""),
                "language": config.get("language", "hi"),
            }
            result = await make_provider_call(config, phone, user_data)
            db.table("voice_calls").insert({
                "organization_id": config["organization_id"],
                "lead_id": lead["id"],
                "bolna_execution_id": result.get("execution_id"),
                "recipient_phone": phone,
                "recipient_name": lead.get("owner_name") or lead.get("business_name", ""),
                "business_name": lead.get("business_name", ""),
                "business_category": lead.get("category", ""),
                "call_status": "queued",
                "trigger_type": "batch",
                "called_at": datetime.utcnow().isoformat(),
            }).execute()
            results["queued"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{lead.get('business_name')}: {str(e)[:50]}")
    
    return {"batch_id": batch_id, "total": len(lead_ids), "queued": results["queued"], "failed": results["failed"], "errors": results["errors"][:10]}

# ============ WEBHOOK (Bolna posts here) ============

@router.post("/webhook")
async def voice_webhook(request: Request):
    """Webhook endpoint - receives call results from Bolna."""
    db = get_supabase()
    payload = await request.json()
    
    execution_id = payload.get("execution_id") or payload.get("call_id") or payload.get("id")
    if execution_id is not None:
        execution_id = str(execution_id)
    if not execution_id:
        return {"status": "ignored", "reason": "no execution_id"}
    
    call = db.table("voice_calls").select("*").eq("bolna_execution_id", execution_id).limit(1).execute()
    if not call.data:
        return {"status": "ignored", "reason": "call not found"}
    
    call_data = call.data[0]
    
    status = payload.get("status", "completed")
    transcript = payload.get("transcript", "") or payload.get("conversation_transcript", "")
    duration = payload.get("duration") or payload.get("call_duration", 0) or payload.get("call_duration_seconds", 0)
    summary = payload.get("summary", "") or payload.get("call_summary", "")
    
    status_map = {"completed": "completed", "failed": "failed", "no-answer": "no_answer", "busy": "busy", "voicemail": "voicemail", "in-progress": "in_progress"}
    mapped_status = status_map.get(status, status if status in ("completed","failed","no_answer","busy","voicemail","in_progress") else "completed")
    
    # Analyze transcript
    outcome = "other"
    sentiment = "neutral"
    plan_interested = None
    should_send_whatsapp = False
    should_followup = False
    
    transcript_lower = (transcript or "").lower()
    
    if any(w in transcript_lower for w in ["subscribe", "plan", "lena hai", "chahiye", "haan", "yes", "interested", "batao", "whatsapp bhej", "details bhej", "send"]):
        outcome = "interested"
        sentiment = "interested"
        should_send_whatsapp = True
        if "premium" in transcript_lower:
            plan_interested = "premium"
        elif "business" in transcript_lower or "999" in transcript_lower:
            plan_interested = "business"
    elif any(w in transcript_lower for w in ["whatsapp", "bhejo", "pathav", "send details"]):
        outcome = "interested"
        sentiment = "interested"
        should_send_whatsapp = True
    elif any(w in transcript_lower for w in ["baad mein", "later", "kal", "phir", "callback", "samay"]):
        outcome = "callback_requested"
        sentiment = "neutral"
        should_followup = True
    elif any(w in transcript_lower for w in ["nahi", "no", "nako", "not interested", "mat karo", "zaroorat nahi"]):
        outcome = "not_interested"
        sentiment = "not_interested"
    elif mapped_status == "no_answer":
        outcome = "no_answer"
        should_followup = True
    elif mapped_status == "voicemail":
        outcome = "voicemail"
        should_followup = True
    
    update_data = {
        "call_status": mapped_status,
        "call_duration_seconds": int(duration) if duration else 0,
        "transcript": transcript[:5000] if transcript else None,
        "call_summary": summary[:1000] if summary else None,
        "sentiment": sentiment,
        "outcome": outcome,
        "plan_interested": plan_interested,
        "completed_at": datetime.utcnow().isoformat(),
    }
    
    if should_followup and call_data.get("attempt_number", 1) < call_data.get("max_attempts", 3):
        update_data["followup_scheduled"] = True
        update_data["followup_date"] = (date.today() + timedelta(days=2)).isoformat()
    
    db.table("voice_calls").update(update_data).eq("id", call_data["id"]).execute()
    
    if should_send_whatsapp and call_data.get("organization_id"):
        try:
            slug = ""
            if call_data.get("lead_id"):
                website = db.table("websites").select("slug").eq("lead_id", call_data["lead_id"]).limit(1).execute()
                if website.data:
                    slug = website.data[0].get("slug", "")
            await send_whatsapp_after_call(
                org_id=call_data["organization_id"],
                phone=call_data["recipient_phone"],
                name=call_data.get("recipient_name", ""),
                business_name=call_data.get("business_name", ""),
                slug=slug,
                language=config.get("language", "hi") if 'config' in dir() else "hi",
            )
            db.table("voice_calls").update({"whatsapp_sent": True}).eq("id", call_data["id"]).execute()
        except Exception:
            pass
    
    if call_data.get("lead_id"):
        if outcome in ("interested", "callback_requested"):
            db.table("leads").update({"status": "interested"}).eq("id", call_data["lead_id"]).execute()
        elif outcome == "subscribed":
            db.table("leads").update({"status": "converted"}).eq("id", call_data["lead_id"]).execute()
        elif outcome == "not_interested":
            db.table("leads").update({"status": "rejected"}).eq("id", call_data["lead_id"]).execute()
    
    return {"status": "processed", "outcome": outcome, "whatsapp_sent": should_send_whatsapp}

# ============ AUTO-CALL NEW LEADS ============

@router.post("/auto-call-new-leads")
async def auto_call_new_leads():
    """Triggered by cron/n8n - calls leads that haven't been called yet."""
    db = get_supabase()
    configs = db.table("voice_call_config").select("*").eq("auto_call_enabled", True).eq("is_active", True).execute()
    if not configs.data:
        return {"message": "No auto-call configs active"}
    
    config = configs.data[0]
    now_hour = datetime.now().hour
    if now_hour < config.get("call_start_hour", 10) or now_hour >= config.get("call_end_hour", 19):
        return {"message": "Outside calling hours", "hour": now_hour}
    
    if (config.get("calls_made_today", 0) or 0) >= config.get("max_calls_per_day", 50):
        return {"message": "Daily limit reached"}
    
    org_id = config["organization_id"]
    called_leads = db.table("voice_calls").select("lead_id").eq("organization_id", org_id).execute()
    called_ids = [c["lead_id"] for c in (called_leads.data or []) if c.get("lead_id")]
    
    query = db.table("leads").select("*").eq("status", "new").not_.is_("phone", "null")
    if org_id:
        query = query.eq("organization_id", org_id)
    leads = query.limit(5).execute()
    
    new_leads = [l for l in (leads.data or []) if l["id"] not in called_ids]
    if not new_leads:
        return {"message": "No new leads to call"}
    
    results = {"called": 0, "failed": 0}
    for lead in new_leads[:3]:
        try:
            phone = lead.get("phone", "")
            if not phone or len(phone.replace("-","").replace(" ","")) < 10:
                continue
            user_data = {
                "business_name": lead.get("business_name", ""),
                "owner_name": lead.get("owner_name", ""),
                "category": lead.get("category", ""),
                "language": config.get("language", "hi"),
            }
            result = await make_provider_call(config, phone, user_data)
            db.table("voice_calls").insert({
                "organization_id": org_id,
                "lead_id": lead["id"],
                "bolna_execution_id": result.get("execution_id"),
                "recipient_phone": phone,
                "recipient_name": lead.get("owner_name") or lead.get("business_name", ""),
                "business_name": lead.get("business_name", ""),
                "business_category": lead.get("category", ""),
                "call_status": "queued",
                "trigger_type": "auto",
                "called_at": datetime.utcnow().isoformat(),
            }).execute()
            results["called"] += 1
            db.table("voice_call_config").update({
                "calls_made_today": (config.get("calls_made_today", 0) or 0) + 1
            }).eq("organization_id", org_id).execute()
        except Exception:
            results["failed"] += 1
    
    return {"message": f"Auto-called {results['called']} leads", **results}


# ============ FOLLOW-UP CALLS ============

@router.post("/followup-due")
async def process_followup_calls():
    """Process follow-up calls that are due today."""
    db = get_supabase()
    today = date.today().isoformat()
    due_calls = db.table("voice_calls").select("*").eq("followup_scheduled", True).lte("followup_date", today).neq("outcome", "subscribed").neq("outcome", "not_interested").execute()
    
    if not due_calls.data:
        return {"message": "No follow-ups due"}
    
    results = {"called": 0, "skipped": 0}
    for call in due_calls.data:
        if call.get("attempt_number", 1) >= call.get("max_attempts", 3):
            db.table("voice_calls").update({"followup_scheduled": False}).eq("id", call["id"]).execute()
            results["skipped"] += 1
            continue
        try:
            config = await get_voice_config(call.get("organization_id"))
            user_data = {
                "business_name": call.get("business_name", ""),
                "owner_name": call.get("recipient_name", ""),
                "category": call.get("business_category", ""),
                "language": config.get("language", "hi"),
                "is_followup": "true",
                "attempt_number": str(call.get("attempt_number", 1) + 1),
            }
            result = await make_provider_call(config, call["recipient_phone"], user_data)
            db.table("voice_calls").insert({
                "organization_id": call["organization_id"],
                "lead_id": call.get("lead_id"),
                "bolna_execution_id": result.get("execution_id"),
                "recipient_phone": call["recipient_phone"],
                "recipient_name": call.get("recipient_name", ""),
                "business_name": call.get("business_name", ""),
                "business_category": call.get("business_category", ""),
                "call_status": "queued",
                "trigger_type": "followup",
                "attempt_number": call.get("attempt_number", 1) + 1,
                "called_at": datetime.utcnow().isoformat(),
            }).execute()
            db.table("voice_calls").update({"followup_scheduled": False}).eq("id", call["id"]).execute()
            results["called"] += 1
        except Exception:
            results["skipped"] += 1
    
    return {"message": f"Processed {results['called']} follow-ups", **results}


# ============ CALL HISTORY & DASHBOARD ============

@router.get("/calls")
async def list_calls(org_id: Optional[str] = None, status: Optional[str] = None, limit: int = Query(default=50, le=200)):
    db = get_supabase()
    query = db.table("voice_calls").select("*").order("created_at", desc=True)
    if org_id:
        query = query.eq("organization_id", org_id)
    if status:
        query = query.eq("call_status", status)
    result = query.limit(limit).execute()
    return {"calls": result.data, "total": len(result.data)}


@router.get("/calls/{call_id}")
async def get_call(call_id: str):
    db = get_supabase()
    result = db.table("voice_calls").select("*").eq("id", call_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Call not found")
    return result.data


@router.get("/dashboard")
async def voice_dashboard(org_id: Optional[str] = None):
    db = get_supabase()
    query = db.table("voice_calls").select("*")
    if org_id:
        query = query.eq("organization_id", org_id)
    calls = query.execute()
    all_calls = calls.data or []
    total = len(all_calls)
    completed = sum(1 for c in all_calls if c.get("call_status") == "completed")
    interested = sum(1 for c in all_calls if c.get("outcome") == "interested")
    subscribed = sum(1 for c in all_calls if c.get("outcome") == "subscribed")
    callbacks = sum(1 for c in all_calls if c.get("outcome") == "callback_requested")
    not_interested = sum(1 for c in all_calls if c.get("outcome") == "not_interested")
    no_answer = sum(1 for c in all_calls if c.get("outcome") == "no_answer")
    whatsapp_sent = sum(1 for c in all_calls if c.get("whatsapp_sent"))
    avg_duration = sum(c.get("call_duration_seconds", 0) for c in all_calls if c.get("call_status") == "completed") / max(completed, 1)
    
    config_query = db.table("voice_call_config").select("auto_call_enabled, calls_made_today, max_calls_per_day, language")
    if org_id:
        config_query = config_query.eq("organization_id", org_id)
    config = config_query.limit(1).execute()
    
    return {
        "total_calls": total, "completed": completed, "interested": interested,
        "subscribed": subscribed, "callbacks": callbacks, "not_interested": not_interested,
        "no_answer": no_answer, "whatsapp_sent": whatsapp_sent,
        "avg_duration_seconds": round(avg_duration, 1),
        "conversion_rate": round((subscribed / max(completed, 1)) * 100, 1),
        "interest_rate": round((interested / max(completed, 1)) * 100, 1),
        "config": config.data[0] if config.data else None,
    }


# ============ SCRIPTS ============

@router.get("/scripts")
async def list_scripts(language: Optional[str] = None):
    db = get_supabase()
    query = db.table("voice_call_scripts").select("*")
    if language:
        query = query.eq("language", language)
    result = query.order("created_at").execute()
    return {"scripts": result.data}


@router.post("/scripts")
async def create_script(data: dict):
    db = get_supabase()
    result = db.table("voice_call_scripts").insert({
        "organization_id": data.get("organization_id"),
        "name": data["name"],
        "language": data.get("language", "hi"),
        "script_type": data.get("script_type", "sales"),
        "agent_prompt": data["agent_prompt"],
        "welcome_message": data.get("welcome_message"),
        "whatsapp_template": data.get("whatsapp_template"),
        "is_default": data.get("is_default", False),
    }).execute()
    return {"script": result.data[0], "message": "Script created"}


# ============ RESET DAILY COUNTER ============

@router.post("/reset-daily")
async def reset_daily_counter():
    db = get_supabase()
    db.table("voice_call_config").update({"calls_made_today": 0}).neq("calls_made_today", 0).execute()
    return {"message": "Daily counters reset"}