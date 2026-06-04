from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    ANALYZED = "analyzed"
    OUTREACH_SENT = "outreach_sent"
    RESPONDED = "responded"
    INTERESTED = "interested"
    CONVERTED = "converted"
    LOST = "lost"


class LeadCreate(BaseModel):
    business_name: str
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    category: str | None = None
    rating: float | None = None
    review_count: int | None = None
    source: str = "google_maps"


class LeadResponse(LeadCreate):
    id: str
    status: LeadStatus
    opportunity_score: float | None = None
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    opportunity_score: float | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
