from fastapi import APIRouter
from app.core.supabase import get_supabase
from datetime import date, timedelta

router = APIRouter(prefix="/api/cron", tags=["cron"])


@router.post("/send-reminders")
async def cron_send_reminders(pwd: str = ""):
    """Cron job: Send WhatsApp reminders for due today/overdue. Call daily."""
    if pwd != "kalpdev2024":
        return {"error": "unauthorized"}
    
    db = get_supabase()
    today = str(date.today())
    
    # Get all active reminders due today or overdue
    reminders = db.table("reminders").select("*, organizations(name, slug)").eq("status", "active").lte("due_date", today).execute()
    
    sent = 0
    failed = 0
    
    for reminder in (reminders.data or []):
        org_id = reminder.get("organization_id")
        phone = reminder.get("customer_phone", "")
        name = reminder.get("customer_name", "")
        item = reminder.get("item_description", "")
        due = reminder.get("due_date", "")
        
        if not phone or not org_id:
            continue
        
        # Get WhatsApp config for this org
        config = db.table("whatsapp_config").select("*").eq("organization_id", org_id).eq("is_active", True).single().execute()
        if not config.data:
            continue  # No WhatsApp configured, skip
        
        # Build message
        msg = reminder.get("message_template", "")
        if not msg:
            org_name = reminder.get("organizations", {}).get("name", "")
            msg = f"Hi {name}, this is a reminder from {org_name}. Your {item} is due ({due}). Please contact us to renew/schedule. Thank you!"
        else:
            msg = msg.replace("{{name}}", name).replace("{{item}}", item).replace("{{due_date}}", due)
        
        # Send via WhatsApp (reuse the send function logic)
        try:
            from app.modules.whatsapp_automation.router import send_whatsapp_message
            result = await send_whatsapp_message(org_id, phone, msg, name, "renewal_reminder")
            if result.get("success"):
                sent += 1
                # Update reminder status
                db.table("reminders").update({"status": "reminded", "last_reminded_at": today}).eq("id", reminder["id"]).execute()
            else:
                failed += 1
        except Exception:
            failed += 1
    
    return {"message": f"Reminder cron completed", "sent": sent, "failed": failed, "total_due": len(reminders.data or [])}


@router.post("/send-subscription-bills")
async def cron_send_bills(pwd: str = ""):
    """Cron job: Send subscription bills via WhatsApp. Call monthly."""
    if pwd != "kalpdev2024":
        return {"error": "unauthorized"}
    
    db = get_supabase()
    today = date.today()
    month = today.month
    year = today.year
    
    # Get all unpaid bills for this month
    bills = db.table("subscription_bills").select("*").eq("month", month).eq("year", year).eq("status", "generated").execute()
    
    sent = 0
    for bill in (bills.data or []):
        org_id = bill.get("organization_id")
        phone = bill.get("customer_phone", "")
        name = bill.get("customer_name", "")
        amount = bill.get("final_amount", 0)
        
        if not phone or not org_id:
            continue
        
        config = db.table("whatsapp_config").select("is_active").eq("organization_id", org_id).eq("is_active", True).single().execute()
        if not config.data:
            continue
        
        msg = f"Hi {name}, your monthly bill of Rs.{amount:.0f} is ready. Please pay at your convenience. Thank you!"
        
        try:
            from app.modules.whatsapp_automation.router import send_whatsapp_message
            result = await send_whatsapp_message(org_id, phone, msg, name, "subscription_bill")
            if result.get("success"):
                sent += 1
                db.table("subscription_bills").update({"status": "sent"}).eq("id", bill["id"]).execute()
        except Exception:
            pass
    
    return {"message": "Bill sending completed", "sent": sent, "total_bills": len(bills.data or [])}


@router.post("/booking-reminders")
async def cron_booking_reminders(pwd: str = ""):
    """Send reminders for tomorrow's appointments."""
    if pwd != "kalpdev2024":
        return {"error": "unauthorized"}
    
    db = get_supabase()
    tomorrow = str(date.today() + timedelta(days=1))
    
    # Get tomorrow's appointments
    appointments = db.table("booking_appointments").select("*, organizations!inner(id, name)").eq("date", tomorrow).eq("status", "confirmed").execute()
    
    sent = 0
    for appt in (appointments.data or []):
        org_id = appt.get("organization_id")
        phone = appt.get("customer_phone", "")
        name = appt.get("customer_name", "")
        time = appt.get("start_time", "")
        
        if not phone or not org_id:
            continue
        
        config = db.table("whatsapp_config").select("is_active").eq("organization_id", org_id).eq("is_active", True).single().execute()
        if not config.data:
            continue
        
        msg = f"Hi {name}, reminder: You have an appointment tomorrow at {time}. See you there!"
        
        try:
            from app.modules.whatsapp_automation.router import send_whatsapp_message
            result = await send_whatsapp_message(org_id, phone, msg, name, "booking_reminder")
            if result.get("success"):
                sent += 1
        except Exception:
            pass
    
    return {"message": "Booking reminders sent", "sent": sent}