from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date, datetime
import httpx

router = APIRouter(prefix="/api/org/{org_id}/whatsapp", tags=["whatsapp-automation"])


async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "whatsapp").single().execute()
    if not r.data or not r.data.get("enabled"):
        raise HTTPException(403, "WhatsApp module not enabled")


async def send_whatsapp_message(org_id: str, to_phone: str, message: str, to_name: str = "", trigger_event: str = "custom"):
    """Send WhatsApp message using the business owner's API credentials."""
    db = get_supabase()
    
    # Get config
    config = db.table("whatsapp_config").select("*").eq("organization_id", org_id).eq("is_active", True).single().execute()
    if not config.data:
        return {"success": False, "error": "WhatsApp not configured. Add your API key in settings."}
    
    cfg = config.data
    provider = cfg.get("provider", "meta_cloud")
    
    # Clean phone number
    phone = to_phone.replace("-", "").replace(" ", "").replace("+", "")
    if len(phone) == 10:
        phone = "91" + phone
    
    success = False
    error_msg = ""
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if provider == "meta_cloud":
                # Meta WhatsApp Cloud API
                url = f"https://graph.facebook.com/v18.0/{cfg['phone_number_id']}/messages"
                headers = {"Authorization": f"Bearer {cfg['access_token']}", "Content-Type": "application/json"}
                body = {
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "text",
                    "text": {"body": message}
                }
                r = await client.post(url, json=body, headers=headers)
                if r.status_code == 200:
                    success = True
                else:
                    error_msg = r.text[:200]
            
            elif provider == "wati":
                url = f"{cfg.get('base_url', 'https://live-server-108820.wati.io')}/api/v1/sendSessionMessage/{phone}"
                headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
                r = await client.post(url, json={"messageText": message}, headers=headers)
                success = r.status_code == 200
                if not success: error_msg = r.text[:200]
            
            elif provider == "aisensy":
                url = "https://backend.aisensy.com/campaign/t1/api/v2"
                body = {
                    "apiKey": cfg["api_key"],
                    "campaignName": trigger_event,
                    "destination": phone,
                    "userName": to_name or phone,
                    "templateParams": [message[:1024]],
                    "source": "city-maps",
                    "media": {}
                }
                r = await client.post(url, json=body)
                success = r.status_code == 200
                if not success: error_msg = r.text[:200]
            
            elif provider == "interakt":
                url = "https://api.interakt.ai/v1/public/message/"
                headers = {"Authorization": f"Basic {cfg['api_key']}", "Content-Type": "application/json"}
                body = {
                    "countryCode": "+91",
                    "phoneNumber": phone[-10:],
                    "callbackData": "city-maps",
                    "type": "Text",
                    "data": {"message": message}
                }
                r = await client.post(url, json=body, headers=headers)
                success = r.status_code in (200, 201, 202)
                if not success: error_msg = r.text[:200]
            
            elif provider == "gupshup":
                url = "https://api.gupshup.io/sm/api/v1/msg"
                headers = {"apikey": cfg["api_key"], "Content-Type": "application/x-www-form-urlencoded"}
                body = f"channel=whatsapp&source={cfg.get('phone_number_id','')}&destination={phone}&message={message}&src.name=city-maps"
                r = await client.post(url, content=body, headers=headers)
                success = r.status_code == 200
                if not success: error_msg = r.text[:200]
            
            elif provider == "custom":
                url = cfg.get("base_url", "")
                if url:
                    headers = {"Authorization": f"Bearer {cfg.get('api_key', '')}", "Content-Type": "application/json"}
                    r = await client.post(url, json={"phone": phone, "message": message}, headers=headers)
                    success = r.status_code in (200, 201, 202)
                    if not success: error_msg = r.text[:200]
    
    except Exception as e:
        error_msg = str(e)[:200]
    
    # Log message
    db.table("whatsapp_messages").insert({
        "organization_id": org_id,
        "to_phone": phone,
        "to_name": to_name,
        "message": message,
        "trigger_event": trigger_event,
        "status": "sent" if success else "failed",
        "error_message": error_msg if not success else None,
    }).execute()
    
    # Update daily counter
    db.table("whatsapp_config").update({
        "messages_sent_today": (cfg.get("messages_sent_today", 0) or 0) + (1 if success else 0)
    }).eq("organization_id", org_id).execute()
    
    return {"success": success, "error": error_msg}


# ============ CONFIG ============

@router.get("/config")
async def get_config(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("whatsapp_config").select("provider, phone_number_id, is_active, daily_limit, messages_sent_today, created_at").eq("organization_id", org_id).single().execute()
    if not result.data:
        return {"configured": False, "message": "WhatsApp not configured yet"}
    return {"configured": True, **result.data}


@router.post("/config")
async def save_config(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    config_data = {
        "organization_id": org_id,
        "provider": data["provider"],
        "api_key": data.get("api_key"),
        "phone_number_id": data.get("phone_number_id"),
        "business_account_id": data.get("business_account_id"),
        "access_token": data.get("access_token"),
        "base_url": data.get("base_url"),
        "is_active": True,
        "daily_limit": data.get("daily_limit", 1000),
    }
    db.table("whatsapp_config").upsert(config_data).execute()
    return {"message": "WhatsApp configured successfully"}


# ============ TEMPLATES ============

@router.get("/templates")
async def list_templates(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("whatsapp_templates").select("*").eq("organization_id", org_id).order("created_at").execute()
    return {"templates": result.data}


@router.post("/templates")
async def create_template(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("whatsapp_templates").insert({
        "organization_id": org_id,
        "name": data["name"],
        "category": data.get("category", "utility"),
        "trigger_event": data.get("trigger_event"),
        "message_body": data["message_body"],
        "variables": data.get("variables", []),
    }).execute()
    return {"template": result.data[0], "message": "Template created"}


# ============ SEND MESSAGE ============

@router.post("/send")
async def send_message(org_id: str, data: dict):
    """Send a single WhatsApp message."""
    await check_access(org_id)
    result = await send_whatsapp_message(
        org_id=org_id,
        to_phone=data["phone"],
        message=data["message"],
        to_name=data.get("name", ""),
        trigger_event=data.get("trigger_event", "custom")
    )
    return result


@router.post("/broadcast")
async def broadcast_message(org_id: str, data: dict):
    """Send message to multiple numbers."""
    await check_access(org_id)
    phones = data.get("phones", [])
    message = data["message"]
    sent = 0
    failed = 0
    for phone in phones:
        r = await send_whatsapp_message(org_id, phone, message, trigger_event="broadcast")
        if r["success"]:
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed, "total": len(phones)}


# ============ AUTOMATION ============

@router.get("/automations")
async def list_automations(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("whatsapp_automations").select("*, whatsapp_templates(name, message_body)").eq("organization_id", org_id).execute()
    return {"automations": result.data}


@router.post("/automations")
async def create_automation(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("whatsapp_automations").insert({
        "organization_id": org_id,
        "name": data["name"],
        "trigger_event": data["trigger_event"],
        "template_id": data.get("template_id"),
        "delay_minutes": data.get("delay_minutes", 0),
        "is_active": data.get("is_active", True),
    }).execute()
    return {"automation": result.data[0], "message": "Automation created"}


# ============ MESSAGE LOG ============

@router.get("/messages")
async def list_messages(org_id: str, limit: int = Query(default=50, le=200)):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("whatsapp_messages").select("*").eq("organization_id", org_id).order("sent_at", desc=True).limit(limit).execute()
    return {"messages": result.data}


# ============ DASHBOARD ============

@router.get("/dashboard")
async def whatsapp_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    
    config = db.table("whatsapp_config").select("is_active, daily_limit, messages_sent_today, provider").eq("organization_id", org_id).single().execute()
    messages = db.table("whatsapp_messages").select("status").eq("organization_id", org_id).execute()
    automations = db.table("whatsapp_automations").select("is_active").eq("organization_id", org_id).execute()
    
    total_sent = len(messages.data)
    delivered = sum(1 for m in messages.data if m["status"] in ("delivered", "read"))
    failed = sum(1 for m in messages.data if m["status"] == "failed")
    active_automations = sum(1 for a in automations.data if a["is_active"])
    
    return {
        "configured": bool(config.data),
        "provider": config.data.get("provider") if config.data else None,
        "today_sent": config.data.get("messages_sent_today", 0) if config.data else 0,
        "daily_limit": config.data.get("daily_limit", 0) if config.data else 0,
        "total_messages": total_sent,
        "delivered": delivered,
        "failed": failed,
        "active_automations": active_automations,
    }
