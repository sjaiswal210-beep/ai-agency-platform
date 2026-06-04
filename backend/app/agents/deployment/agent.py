from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.schemas.leads import LeadUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


async def deploy_website(website_id: str) -> dict:
    """Deploy an approved website and update records."""
    logger.info("Deploying website", website_id=website_id)

    website_service = WebsiteService()
    lead_service = LeadService()

    website = website_service.get(website_id)
    if not website:
        raise ValueError(f"Website {website_id} not found")

    if website["status"] != "approved":
        raise ValueError(f"Website must be approved before deployment. Current status: {website['status']}")

    # In production, this would:
    # 1. Generate static HTML from the content JSON
    # 2. Push to a hosting provider (Vercel, Netlify, etc.)
    # 3. Configure custom domain if provided
    # 4. Return the live URL

    # For now, generate a preview URL
    preview_url = f"https://preview.aiagency.dev/{website_id}"

    website_service.update_status(
        website_id,
        status="deployed",
        deployed_url=preview_url,
    )

    # Update lead status to converted
    lead_service.update(website["lead_id"], LeadUpdate(status="converted"))

    logger.info("Website deployed", website_id=website_id, url=preview_url)
    return {
        "website_id": website_id,
        "deployed_url": preview_url,
        "status": "deployed",
    }
