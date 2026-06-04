from app.services.outreach_service import OutreachService
from app.services.lead_service import LeadService
from app.schemas.leads import LeadUpdate
from app.core.logging import get_logger
from app.services.usage_tracker import track_usage

logger = get_logger(__name__)


async def send_outreach(lead_id: str, channel: str = "email") -> dict:
    """Generate and queue outreach message for a lead."""
    logger.info("Sending outreach", lead_id=lead_id, channel=channel)

    lead_service = LeadService()
    outreach_service = OutreachService()

    lead = lead_service.get(lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    # Generate personalized message using AI
    message = await outreach_service.generate_message(lead, channel)

    # Store the outreach record
    record = outreach_service.create(lead_id, channel, message)

    # Update lead status
    lead_service.update(lead_id, LeadUpdate(status="outreach_sent"))

    track_usage("gemini_outreach", 1)
    logger.info("Outreach queued", message_id=record["id"])
    return record
