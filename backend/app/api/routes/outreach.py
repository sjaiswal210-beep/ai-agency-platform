from __future__ import annotations
from fastapi import APIRouter
from app.services.outreach_service import OutreachService

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.post("/send")
async def send(lead_id: str, channel: str = "email"):
    """Generate and send AI-crafted outreach to a lead."""
    from app.agents.outreach.agent import send_outreach
    return await send_outreach(lead_id, channel)


@router.post("/followup/{lead_id}")
async def followup(lead_id: str):
    """Check and send follow-up for a lead."""
    from app.agents.followup.agent import check_and_followup
    return await check_and_followup(lead_id)


@router.get("/lead/{lead_id}")
def get_outreach_history(lead_id: str):
    """Get all outreach messages for a lead."""
    return OutreachService().list_by_lead(lead_id)


@router.get("/pending")
def get_pending():
    """Get all pending outreach messages."""
    return OutreachService().list_pending()
