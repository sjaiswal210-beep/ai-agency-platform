from __future__ import annotations
import httpx
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

GOOGLE_PLACES_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_PLACES_DETAIL = "https://maps.googleapis.com/maps/api/place/details/json"
GOOGLE_PLACES_PHOTO = "https://maps.googleapis.com/maps/api/place/photo"


async def get_business_photos(business_name: str, address: str = "", max_photos: int = 6) -> list[str]:
    """Fetch real photos of a business from Google Maps."""
    settings = get_settings()
    api_key = settings.google_places_key
    if not api_key:
        return []

    try:
        query = f"{business_name} {address}".strip()
        async with httpx.AsyncClient() as client:
            # Search for the business
            resp = await client.get(
                GOOGLE_PLACES_SEARCH,
                params={"query": query, "key": api_key},
                timeout=10,
            )
            if resp.status_code != 200:
                return []

            results = resp.json().get("results", [])
            if not results:
                return []

            place_id = results[0]["place_id"]

            # Get photo references
            detail_resp = await client.get(
                GOOGLE_PLACES_DETAIL,
                params={"place_id": place_id, "fields": "photos", "key": api_key},
                timeout=10,
            )
            if detail_resp.status_code != 200:
                return []

            photos = detail_resp.json().get("result", {}).get("photos", [])

            # Build photo URLs
            photo_urls = []
            for p in photos[:max_photos]:
                ref = p.get("photo_reference")
                if ref:
                    url = f"{GOOGLE_PLACES_PHOTO}?maxwidth=600&photo_reference={ref}&key={api_key}"
                    photo_urls.append(url)

            logger.info("Fetched business photos", business=business_name, count=len(photo_urls))
            return photo_urls

    except Exception as e:
        logger.warning("Failed to fetch photos", error=str(e))
        return []
