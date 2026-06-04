from __future__ import annotations
import httpx
from app.services.lead_service import LeadService
from app.schemas.leads import LeadCreate
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.usage_tracker import track_usage

logger = get_logger(__name__)

GOOGLE_PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_PLACES_DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"


async def get_place_details(place_id: str, api_key: str) -> dict:
    """Get full details (phone, website) for a place."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_PLACES_DETAIL_URL,
            params={
                "place_id": place_id,
                "fields": "name,formatted_phone_number,international_phone_number,website,formatted_address,rating,user_ratings_total,types,opening_hours",
                "key": api_key,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("result", {})
    return {}


async def run_discovery(location: str, category: str, max_results: int = 10) -> list[dict]:
    """Search Google Maps for real businesses by keyword and location."""
    settings = get_settings()
    api_key = settings.google_places_key

    if not api_key:
        logger.error("Google Places API key not configured")
        raise ValueError("Google Places API key not configured. Set GOOGLE_PLACES_KEY in .env")

    logger.info("Searching Google Maps", location=location, category=category)

    # Step 1: Text search for businesses
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_PLACES_SEARCH_URL,
            params={
                "query": f"{category} in {location}",
                "key": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        logger.warning("No results found", location=location, category=category)
        return []

    logger.info("Found places", count=len(results))
    track_usage("google_places_search", 1)

    # Step 2: Get details (phone numbers) for each place
    leads = []
    service = LeadService()

    for place in results[:max_results]:  # Limit based on user request
        place_id = place.get("place_id")
        if not place_id:
            continue

        track_usage("google_places_details", 1)
        # Get detailed info including phone
        details = await get_place_details(place_id, api_key)

        phone = details.get("international_phone_number") or details.get("formatted_phone_number") or ""
        website = details.get("website") or ""
        address = details.get("formatted_address") or place.get("formatted_address", "")
        name = details.get("name") or place.get("name", "Unknown")
        rating = place.get("rating")
        review_count = details.get("user_ratings_total") or place.get("user_ratings_total", 0)

        lead = LeadCreate(
            business_name=name,
            phone=phone,
            email="",  # Not available from Google Maps
            website=website if website else None,
            address=address,
            category=category,
            rating=rating,
            review_count=review_count,
            source="google_maps",
        )
        leads.append(lead)

    # Store in database
    if leads:
        stored = service.bulk_create(leads)
        logger.info("Stored leads from Google Maps", count=len(stored))
        return stored

    return []
