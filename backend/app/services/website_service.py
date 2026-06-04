from __future__ import annotations
from app.core.supabase import get_supabase
from app.schemas.websites import WebsiteCreate
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebsiteService:
    def __init__(self):
        self.db = get_supabase()
        self.table = "websites"

    def create(self, website: WebsiteCreate) -> dict:
        logger.info("Creating website", lead_id=website.lead_id, template=website.template)
        return self.db.table(self.table).insert(website.model_dump()).execute().data[0]

    def get(self, website_id: str) -> dict | None:
        res = self.db.table(self.table).select("*").eq("id", website_id).execute()
        return res.data[0] if res.data else None

    def get_by_lead(self, lead_id: str) -> list[dict]:
        return self.db.table(self.table).select("*").eq("lead_id", lead_id).execute().data

    def update_status(self, website_id: str, status: str, **kwargs) -> dict:
        payload = {"status": status, **kwargs}
        return self.db.table(self.table).update(payload).eq("id", website_id).execute().data[0]

    def list_all(self, limit: int = 50, offset: int = 0) -> list[dict]:
        return (
            self.db.table(self.table)
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
            .data
        )

