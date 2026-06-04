from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class WebsiteStatus(str, Enum):
    GENERATING = "generating"
    PREVIEW = "preview"
    APPROVED = "approved"
    DEPLOYED = "deployed"


class WebsiteCreate(BaseModel):
    lead_id: str
    template: str
    content: dict | None = None


class WebsiteResponse(BaseModel):
    id: str
    lead_id: str
    template: str
    preview_url: str | None = None
    deployed_url: str | None = None
    status: WebsiteStatus
    content: dict | None = None
    created_at: datetime


class AnalysisResult(BaseModel):
    lead_id: str
    performance_score: float
    mobile_friendly: bool
    has_cta: bool
    has_seo: bool
    has_contact_form: bool
    has_whatsapp: bool
    issues: list[str]
    opportunity_score: float
