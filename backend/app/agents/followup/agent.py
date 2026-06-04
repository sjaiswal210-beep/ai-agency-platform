from app.core.llm import chat_completion
from app.services.lead_service import LeadService
from app.services.outreach_service import OutreachService
from app.schemas.leads import LeadUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_and_followup(lead_id: str) -> dict:
    """Check lead status and send follow-up if needed."""
    logger.info("Checking follow-up", lead_id=lead_id)

    lead_service = LeadService()
    outreach_service = OutreachService()

    lead = lead_service.get(lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    messages = outreach_service.list_by_lead(lead_id)

    if not messages:
        return {"action": "none", "reason": "no outreach sent yet"}

    last_msg = messages[0]  # Most recent first

    # If they replied or read, send a follow-up
    if last_msg["status"] in ("replied", "read"):
        prompt = f"""The business {lead['business_name']} has shown interest.
Previous messages sent: {len(messages)}
Last message status: {last_msg['status']}
Channel: {last_msg['channel']}

Generate a brief follow-up message that:
- References our previous conversation
- Offers to schedule a quick call or demo
- Keeps it under 100 words
- Sounds natural and not pushy"""

        followup = await chat_completion([{"role": "user", "content": prompt}])
        record = outreach_service.create(lead_id, last_msg["channel"], followup)

        # Update lead to interested if they replied
        if last_msg["status"] == "replied":
            lead_service.update(lead_id, LeadUpdate(status="interested"))

        logger.info("Follow-up sent", lead_id=lead_id)
        return {"action": "followup_sent", "message_id": record["id"]}

    # If delivered but no response after 48h, send reminder
    if last_msg["status"] == "delivered":
        from datetime import datetime, timezone, timedelta
        sent_at = last_msg.get("sent_at")
        if sent_at:
            sent_time = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - sent_time > timedelta(hours=48):
                prompt = f"""Send a gentle reminder to {lead['business_name']}.
We previously sent them a message about their website.
Keep it under 50 words, friendly tone."""
                reminder = await chat_completion([{"role": "user", "content": prompt}])
                record = outreach_service.create(lead_id, last_msg["channel"], reminder)
                return {"action": "reminder_sent", "message_id": record["id"]}

    return {"action": "waiting", "last_status": last_msg["status"]}
