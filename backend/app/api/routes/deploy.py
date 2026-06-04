from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/deploy", tags=["deployment"])
logger = get_logger(__name__)


class DeployRequest(BaseModel):
    subdomain: str = ""  # e.g., "knd-bakery" -> knd-bakery.yourdomain.com


@router.post("/{website_id}")
async def deploy_website(website_id: str, req: DeployRequest):
    """Deploy a website to a live URL."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "business") if lead else "business"

    # Generate subdomain from business name if not provided
    if not req.subdomain:
        subdomain = business_name.lower().replace(" ", "-").replace("'", "").replace(".", "")[:30]
    else:
        subdomain = req.subdomain

    settings = get_settings()

    # For now, the "deployed" URL is the preview URL
    # When Vercel is configured, this would push to Vercel
    deployed_url = f"{settings.backend_url}/api/preview/{website_id}"

    # Update website status
    service.update_status(website_id, "deployed", deployed_url=deployed_url)

    logger.info("Website deployed", website_id=website_id, url=deployed_url)

    return {
        "status": "deployed",
        "url": deployed_url,
        "subdomain": subdomain,
        "business": business_name,
        "note": "Currently served from backend. For custom domain, configure Vercel deployment."
    }


@router.get("/list")
def list_deployments():
    """List all deployed websites."""
    db = WebsiteService().db
    deployed = db.table("websites").select("*").eq("status", "deployed").execute()
    return {"deployments": deployed.data, "count": len(deployed.data)}
