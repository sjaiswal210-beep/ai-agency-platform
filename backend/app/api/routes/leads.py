from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from app.schemas.leads import LeadCreate, LeadResponse, LeadUpdate
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/")
def list_leads(status: str | None = None, limit: int = 50, offset: int = 0):
    """List all leads with optional status filter."""
    return LeadService().list_leads(status=status, limit=limit, offset=offset)


@router.post("/", status_code=201)
def create_lead(lead: LeadCreate):
    """Create a new lead manually."""
    return LeadService().create(lead)


@router.get("/{lead_id}")
def get_lead(lead_id: str):
    """Get a single lead by ID."""
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


@router.patch("/{lead_id}")
def update_lead(lead_id: str, data: LeadUpdate):
    """Update a lead fields."""
    return LeadService().update(lead_id, data)


@router.post("/discover")
async def discover_leads(
    location: str = Query(..., description="City or area to search"),
    category: str = Query("restaurant", description="Business category"),
    count: int = Query(10, description="Number of leads to fetch"),
    background_tasks: BackgroundTasks = None,
):
    """Trigger AI-powered lead discovery for a location and category."""
    from app.agents.lead_discovery.agent import run_discovery
    leads = await run_discovery(location, category, max_results=min(count, 20))

    # Auto-process first lead: analyze + generate website
    auto_processed = None
    if leads:
        first_lead = leads[0]
        try:
            from app.agents.website_analysis.agent import analyze_website
            from app.agents.website_generation.agent import generate_website
            await analyze_website(first_lead["id"])
            site = await generate_website(first_lead["id"], category)
            auto_processed = {"lead": first_lead["business_name"], "website_id": site["id"]}
        except Exception:
            pass


    # Auto-generate websites in background



    if background_tasks:



        lead_ids = [l["id"] for l in leads if isinstance(l, dict) and l.get("id")][:1]



        if lead_ids:



            background_tasks.add_task(_auto_generate_websites_sync, lead_ids)




    return {"discovered": len(leads), "leads": leads, "auto_processed": auto_processed}


@router.post("/{lead_id}/analyze")
async def analyze_lead(lead_id: str):
    """Run AI website analysis on a lead."""
    from app.agents.website_analysis.agent import analyze_website
    return await analyze_website(lead_id)


@router.post("/search-specific")
async def search_specific_business(query: str = Query(..., description="Business name + pincode/area")):
    """Search for a specific business, analyze it, and create a website."""
    from app.core.config import get_settings
    from app.services.lead_service import LeadService
    from app.schemas.leads import LeadCreate
    from app.agents.website_analysis.agent import analyze_website
    from app.agents.website_generation.agent import generate_website
    import httpx

    settings = get_settings()
    api_key = settings.google_places_key
    if not api_key:
        raise HTTPException(400, "Google Places API key not configured")

    # Search Google Maps for the specific business
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            return {"error": "Google API error", "lead": None}

        results = resp.json().get("results", [])
        if not results:
            return {"error": "Business not found. Try a different name or add location.", "lead": None}

        # Get details for the first result
        place = results[0]
        place_id = place.get("place_id")

        detail_resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "name,formatted_phone_number,international_phone_number,website,formatted_address,rating,user_ratings_total,types",
                "key": api_key,
            },
            timeout=10,
        )
        detail = detail_resp.json().get("result", {}) if detail_resp.status_code == 200 else {}

    # Determine category from types
    types = detail.get("types", [])
    type_map = {
        "restaurant": "restaurant", "food": "restaurant", "cafe": "cafe",
        "bakery": "bakery", "gym": "gym", "spa": "spa", "beauty_salon": "salon",
        "hair_care": "salon", "dentist": "dentist", "doctor": "clinic",
        "hospital": "clinic", "lodging": "hotel", "store": "store",
        "school": "school", "lawyer": "lawyer",
    }
    category = "business"
    for t in types:
        if t in type_map:
            category = type_map[t]
            break

    # Create lead
    service = LeadService()
    lead_data = LeadCreate(
        business_name=detail.get("name", place.get("name", query)),
        phone=detail.get("international_phone_number") or detail.get("formatted_phone_number") or "",
        email="",
        website=detail.get("website") or None,
        address=detail.get("formatted_address") or place.get("formatted_address", ""),
        category=category,
        rating=place.get("rating"),
        review_count=detail.get("user_ratings_total") or place.get("user_ratings_total", 0),
        source="specific_search",
    )
    stored = service.create(lead_data)

    # Auto-analyze
    try:
        await analyze_website(stored["id"])
    except Exception:
        pass

    # Auto-generate website
    website_id = None
    try:
        site = await generate_website(stored["id"], category)
        website_id = site.get("id")
    except Exception:
        pass

    
    # Get slug for the website link
    _slug = ""
    if website_id:
        from app.core.supabase import get_supabase as _gs
        _db = _gs()
        _ws = _db.table("websites").select("slug").eq("id", website_id).limit(1).execute()
        if _ws.data:
            _slug = _ws.data[0].get("slug", "")
    return {
        "lead": stored,
        "website_id": website_id,
        "category": category,
        "slug": _slug,
    }


@router.post("/scrape-area")
async def scrape_area(location: str = Query(..., description="Area to scrape all businesses from")):
    """Scrape ALL businesses in an area and auto-categorize with AI."""
    from app.core.config import get_settings
    from app.core.llm import chat_completion
    from app.services.lead_service import LeadService
    from app.schemas.leads import LeadCreate
    import httpx
    import json

    settings = get_settings()
    api_key = settings.google_places_key
    if not api_key:
        raise HTTPException(400, "Google Places API key not configured")

    # Search for all businesses in the area (no category filter)
    all_leads = []
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": f"businesses in {location}", "key": api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            raise HTTPException(500, "Google Places API error")

        results = resp.json().get("results", [])

        for place in results[:20]:
            place_id = place.get("place_id")
            if not place_id:
                continue

            # Get details
            detail_resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={
                    "place_id": place_id,
                    "fields": "name,formatted_phone_number,international_phone_number,website,formatted_address,rating,user_ratings_total,types",
                    "key": api_key,
                },
                timeout=10,
            )
            if detail_resp.status_code == 200:
                detail = detail_resp.json().get("result", {})
                types = detail.get("types", [])

                # Use Google types to determine category
                type_to_category = {
                    "restaurant": "restaurant", "food": "restaurant", "cafe": "cafe",
                    "bakery": "bakery", "bar": "restaurant",
                    "gym": "gym", "spa": "spa", "beauty_salon": "salon",
                    "hair_care": "salon", "dentist": "dentist",
                    "doctor": "clinic", "hospital": "clinic", "pharmacy": "clinic",
                    "veterinary_care": "clinic", "lawyer": "lawyer",
                    "real_estate_agency": "realestate", "lodging": "hotel",
                    "school": "school", "store": "store", "clothing_store": "store",
                    "electronics_store": "store", "furniture_store": "store",
                    "car_repair": "automotive", "car_dealer": "automotive",
                    "plumber": "plumber", "electrician": "electrician",
                    "painter": "services", "moving_company": "services",
                }

                category = "business"
                for t in types:
                    if t in type_to_category:
                        category = type_to_category[t]
                        break

                all_leads.append({
                    "business_name": detail.get("name", place.get("name", "Unknown")),
                    "phone": detail.get("international_phone_number") or detail.get("formatted_phone_number") or "",
                    "website": detail.get("website") or None,
                    "address": detail.get("formatted_address") or place.get("formatted_address", ""),
                    "category": category,
                    "rating": place.get("rating"),
                    "review_count": detail.get("user_ratings_total") or place.get("user_ratings_total", 0),
                })

    # Store leads
    service = LeadService()
    stored = []
    if all_leads:
        leads_to_create = [
            LeadCreate(
                business_name=l["business_name"],
                phone=l["phone"],
                email="",
                website=l["website"],
                address=l["address"],
                category=l["category"],
                rating=l["rating"],
                review_count=l["review_count"],
                source="area_scrape",
            )
            for l in all_leads
        ]
        stored = service.bulk_create(leads_to_create)

    return {"discovered": len(stored), "leads": stored}

def _auto_generate_websites_sync(lead_ids: list):
    """Background task: auto-generate websites for ALL leads in batches of 3."""
    import asyncio
    import time
    from app.agents.website_generation.agent import generate_website
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    
    loop = asyncio.new_event_loop()
    total = len(lead_ids)
    done = 0
    
    for i in range(0, total, 1):
        batch = lead_ids[i:i+1]
        logger.info(f"Auto-gen batch {i//3 + 1}: generating {len(batch)} websites ({done}/{total} done)")
        
        for lead_id in batch:
            try:
                loop.run_until_complete(generate_website(lead_id))
                done += 1
                logger.info("Auto-generated website", lead_id=lead_id, progress=f"{done}/{total}")
            except Exception as e:
                logger.warning("Auto-gen failed", lead_id=lead_id, error=str(e))
        
        # Wait between batches
        if i + 1 < total:
            logger.info(f"Waiting 30s before next batch... ({done}/{total} done)")
            time.sleep(30)
    
    loop.close()
    logger.info(f"Auto-generation complete: {done}/{total} websites created")


@router.delete("/{lead_id}")
def delete_lead(lead_id: str):
    """Delete a lead and its associated websites."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    
    # Delete associated websites first
    db.table("websites").delete().eq("lead_id", lead_id).execute()
    # Delete the lead
    db.table("leads").delete().eq("id", lead_id).execute()
    
    return {"deleted": True, "lead_id": lead_id}


@router.delete("/website/{website_id}")
def delete_website(website_id: str):
    """Delete a specific website."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    db.table("websites").delete().eq("id", website_id).execute()
    return {"deleted": True, "website_id": website_id}
