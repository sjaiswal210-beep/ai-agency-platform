from __future__ import annotations
from app.core.supabase import get_supabase
from app.core.llm import chat_completion
from app.core.logging import get_logger

logger = get_logger(__name__)


class OutreachService:
    def __init__(self):
        self.db = get_supabase()
        self.table = "outreach_messages"

    async def generate_message(self, lead: dict, channel: str) -> str:
        """Use AI to generate a personalized outreach message."""
        prompt = f"""Generate a short, personalized {channel} outreach message for:
Business: {lead['business_name']}
Category: {lead.get('category', 'local business')}
Issues found: {lead.get('notes', 'outdated website')}

The message should:
- Be friendly and professional
- Mention we built a free demo website for them
- Include a call to action
- Be under 200 words for email, under 50 words for WhatsApp"""

        return await chat_completion([{"role": "user", "content": prompt}])

    def create(self, lead_id: str, channel: str, message: str) -> dict:
        logger.info("Creating outreach", lead_id=lead_id, channel=channel)
        return (
            self.db.table(self.table)
            .insert({"lead_id": lead_id, "channel": channel, "message": message, "status": "pending"})
            .execute()
            .data[0]
        )

    def list_by_lead(self, lead_id: str) -> list[dict]:
        return self.db.table(self.table).select("*").eq("lead_id", lead_id).order("created_at", desc=True).execute().data

    def update_status(self, message_id: str, status: str) -> dict:
        return self.db.table(self.table).update({"status": status}).eq("id", message_id).execute().data[0]

    def list_pending(self, limit: int = 50) -> list[dict]:
        return self.db.table(self.table).select("*").eq("status", "pending").limit(limit).execute().data

