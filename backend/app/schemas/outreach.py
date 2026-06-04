from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class OutreachChannel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class OutreachStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    FAILED = "failed"


class OutreachCreate(BaseModel):
    lead_id: str
    channel: OutreachChannel
    message: str | None = None  # Auto-generated if None


class OutreachResponse(BaseModel):
    id: str
    lead_id: str
    channel: OutreachChannel
    message: str
    status: OutreachStatus
    sent_at: datetime | None = None
    created_at: datetime
