from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.services.website_service import WebsiteService

router = APIRouter(prefix="/websites", tags=["websites"])


@router.post("/generate")
async def generate(lead_id: str, template: str = "store"):
    """Generate an AI-powered website for a lead."""
    from app.agents.website_generation.agent import generate_website
    return await generate_website(lead_id, template)


@router.get("/{website_id}")
def get_website(website_id: str):
    """Get a website by ID."""
    website = WebsiteService().get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")
    return website


@router.get("/lead/{lead_id}")
def get_websites_for_lead(lead_id: str):
    """Get all websites generated for a lead."""
    return WebsiteService().get_by_lead(lead_id)


@router.patch("/{website_id}/status")
def update_website_status(website_id: str, status: str):
    """Update website status."""
    return WebsiteService().update_status(website_id, status)


@router.post("/{website_id}/deploy")
async def deploy(website_id: str):
    """Deploy an approved website."""
    from app.agents.deployment.agent import deploy_website
    return await deploy_website(website_id)


@router.get("/")
def list_websites(limit: int = 30, offset: int = 0):
    """List all generated websites with business names."""
    from app.services.lead_service import LeadService
    websites = WebsiteService().list_all(limit=limit, offset=offset)
    lead_service = LeadService()
    for w in websites[:30]:  # Only enrich first 30
        if w.get("lead_id"):
            try:
                lead = lead_service.get(w["lead_id"])
                if lead:
                    w["business_name"] = lead.get("business_name", "")
                    w["category"] = lead.get("category", "")
                    w["phone"] = lead.get("phone", "")
                    w["address"] = lead.get("address", "")
            except Exception:
                pass
    return websites
