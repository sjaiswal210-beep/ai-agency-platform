from __future__ import annotations
from app.core.supabase import get_supabase
from app.schemas.leads import LeadCreate, LeadUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


class LeadService:
    def __init__(self):
        self.db = get_supabase()
        self.table = "leads"

    def create(self, lead: LeadCreate) -> dict:
        logger.info("Creating lead", business=lead.business_name)
        return self.db.table(self.table).insert(lead.model_dump()).execute().data[0]

    def get(self, lead_id: str) -> dict | None:
        res = self.db.table(self.table).select("*").eq("id", lead_id).execute()
        return res.data[0] if res.data else None

    def list_leads(self, status: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
        q = self.db.table(self.table).select("*").order("created_at", desc=True).range(offset, offset + limit - 1)
        if status:
            q = q.eq("status", status)
        return q.execute().data

    def update(self, lead_id: str, data: LeadUpdate) -> dict:
        payload = {k: v for k, v in data.model_dump().items() if v is not None}
        return self.db.table(self.table).update(payload).eq("id", lead_id).execute().data[0]

    def bulk_create(self, leads: list[LeadCreate]) -> list[dict]:
        logger.info("Bulk creating leads", count=len(leads))
        return self.db.table(self.table).insert([l.model_dump() for l in leads]).execute().data

    def count_by_status(self) -> dict:
        res = self.db.table(self.table).select("status").execute()
        counts = {}
        for row in res.data:
            s = row.get("status", "new")
            counts[s] = counts.get(s, 0) + 1
        return counts
