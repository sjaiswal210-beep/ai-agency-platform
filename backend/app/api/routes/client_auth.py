from __future__ import annotations
import hashlib
import secrets
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.core.supabase import get_supabase
from app.core.logging import get_logger

router = APIRouter(prefix="/client", tags=["client-portal"])
logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)


class ClientLogin(BaseModel):
    phone: str
    password: str


class ClientRegister(BaseModel):
    lead_id: str
    phone: str
    password: str
    name: str = ""


# ============ AUTH ENDPOINTS ============

@router.post("/register")
def register_client(req: ClientRegister):
    """Register a business owner as a client (called after they subscribe)."""
    db = get_supabase()

    # Check if already registered
    existing = db.table("clients").select("*").eq("phone", req.phone).execute()
    if existing.data:
        raise HTTPException(400, "Phone already registered")

    token = generate_token()
    client = db.table("clients").insert({
        "lead_id": req.lead_id,
        "phone": req.phone,
        "password_hash": hash_password(req.password),
        "name": req.name,
        "token": token,
        "plan": "starter",
        "plan_amount": 79,
        "status": "active",
    }).execute()

    return {"status": "registered", "token": token, "client_id": client.data[0]["id"]}


@router.post("/login")
def login_client(req: ClientLogin):
    """Client login with phone + password."""
    db = get_supabase()
    clients = db.table("clients").select("*").eq("phone", req.phone).execute()

    if not clients.data:
        raise HTTPException(401, "Invalid phone or password")

    client = clients.data[0]
    if client["password_hash"] != hash_password(req.password):
        raise HTTPException(401, "Invalid phone or password")

    # Generate new token
    token = generate_token()
    db.table("clients").update({"token": token}).eq("id", client["id"]).execute()

    return {
        "token": token,
        "client_id": client["id"],
        "name": client["name"],
        "phone": client["phone"],
        "plan": client["plan"],
        "lead_id": client["lead_id"],
    }


def get_current_client(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify client token and return client data."""
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    db = get_supabase()
    clients = db.table("clients").select("*").eq("token", credentials.credentials).execute()

    if not clients.data:
        raise HTTPException(401, "Invalid token")

    return clients.data[0]


@router.get("/me")
def get_my_profile(client=Depends(get_current_client)):
    """Get current client profile."""
    return {
        "id": client["id"],
        "name": client["name"],
        "phone": client["phone"],
        "plan": client["plan"],
        "plan_amount": client["plan_amount"],
        "status": client["status"],
        "lead_id": client["lead_id"],
    }


@router.get("/my-website")
def get_my_website(client=Depends(get_current_client)):
    """Get the client's website details."""
    from app.services.website_service import WebsiteService
    service = WebsiteService()
    websites = service.get_by_lead(client["lead_id"])
    if not websites:
        return {"website": None}
    return {"website": websites[0]}


@router.get("/my-tools")
def get_my_tools(client=Depends(get_current_client)):
    """Get available tools for the client."""
    from app.api.routes.toolkit import get_tools_for_category
    from app.services.lead_service import LeadService
    lead = LeadService().get(client["lead_id"])
    category = lead.get("category", "default") if lead else "default"
    tools = get_tools_for_category(category)
    return {"tools": tools, "category": category}
