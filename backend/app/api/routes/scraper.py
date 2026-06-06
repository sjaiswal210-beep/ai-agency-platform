from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.core.llm import chat_completion
import httpx
import re

router = APIRouter(prefix="/scraper", tags=["scraper"])


async def fetch_page(url: str) -> str:
    """Fetch a webpage and return cleaned text content."""
    if not url.startswith("http"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

    # Strip scripts, styles, and HTML tags to get clean text
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    # Keep some structure
    html = re.sub(r'<(h[1-6])[^>]*>', r'\n### ', html)
    html = re.sub(r'<li[^>]*>', r'\n- ', html)
    html = re.sub(r'<br[^>]*>', r'\n', html)
    html = re.sub(r'<p[^>]*>', r'\n', html)
    html = re.sub(r'<[^>]+>', '', html)

    # Clean up whitespace
    html = re.sub(r'\n\s*\n', '\n\n', html)
    html = html.strip()

    # Limit to 4000 chars for LLM context
    return html[:4000]


@router.post("/analyze-url")
async def analyze_business_url(url: str):
    """Scrape a business website and extract structured intelligence using AI."""
    if not url:
        raise HTTPException(400, "URL is required")

    try:
        page_text = await fetch_page(url)
    except Exception as e:
        raise HTTPException(400, f"Could not fetch URL: {str(e)}")

    if len(page_text) < 50:
        raise HTTPException(400, "Page has too little content to analyze")

    prompt = f"""Analyze this business website content and extract ALL available information.
Return a structured JSON with everything you can find.

WEBSITE CONTENT:
{page_text}

Extract and return as JSON:
{{
    "business_name": "exact business name",
    "category": "business type/industry",
    "tagline": "their tagline or slogan if any",
    "services": ["service 1", "service 2", "..."],
    "phone": "phone number if found",
    "email": "email if found", 
    "address": "full address if found",
    "city": "city name",
    "social_links": {{
        "facebook": "url or null",
        "instagram": "url or null",
        "youtube": "url or null",
        "twitter": "url or null",
        "linkedin": "url or null"
    }},
    "team_members": ["name - role"],
    "pricing": ["any pricing info found"],
    "working_hours": "hours if mentioned",
    "usp": ["unique selling points"],
    "awards": ["certifications or awards"],
    "year_established": "year if mentioned",
    "reviews_mentioned": "any review counts or ratings",
    "technologies": ["tools/tech they mention using"],
    "target_audience": "who they serve",
    "areas_served": ["locations/areas they serve"],
    "summary": "2 sentence summary of what this business does and their key strength"
}}

RULES:
- Extract ONLY what's actually on the page (don't invent)
- Use null for fields not found
- Return ONLY valid JSON"""

    import json
    result = await chat_completion([{"role": "user", "content": prompt}])

    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(cleaned)
    except Exception:
        data = {"raw_extraction": cleaned[:1000]}

    return {"url": url, "extracted": data, "content_length": len(page_text)}


@router.post("/enrich-lead/{lead_id}")
async def enrich_lead_from_website(lead_id: str):
    """If a lead has a website URL, scrape it and enrich the lead data."""
    from app.services.lead_service import LeadService
    from app.core.supabase import get_supabase

    lead_service = LeadService()
    lead = lead_service.get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    website_url = lead.get("website")
    if not website_url:
        raise HTTPException(400, "Lead has no website URL to scrape")

    try:
        page_text = await fetch_page(website_url)
    except Exception as e:
        raise HTTPException(400, f"Could not fetch website: {str(e)}")

    if len(page_text) < 50:
        raise HTTPException(400, "Website has too little content")

    prompt = f"""Extract business intelligence from this website for lead enrichment.

WEBSITE ({website_url}):
{page_text}

Current lead data:
- Name: {lead.get("business_name")}
- Category: {lead.get("category")}
- Phone: {lead.get("phone")}
- Address: {lead.get("address")}

Extract NEW information not already in the lead. Return JSON:
{{
    "services_found": ["list of services"],
    "social_facebook": "facebook url or null",
    "social_instagram": "instagram url or null",
    "email_found": "email or null",
    "team_info": "key team members",
    "pricing_info": "any pricing found",
    "usp": "their main differentiator",
    "additional_phones": ["other phone numbers"],
    "working_hours": "hours",
    "year_established": "year or null",
    "enrichment_notes": "2 sentences about what makes this business unique"
}}

Return ONLY valid JSON."""

    import json
    result = await chat_completion([{"role": "user", "content": prompt}])

    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        enrichment = json.loads(cleaned)
    except Exception:
        enrichment = {"raw": cleaned[:500]}

    # Update lead notes with enrichment data
    db = get_supabase()
    current_notes = lead.get("notes") or ""
    enrichment_summary = enrichment.get("enrichment_notes", "")
    services_str = ", ".join(enrichment.get("services_found", [])[:5])
    new_notes = f"{current_notes}\n[AI Enriched] {enrichment_summary} Services: {services_str}".strip()

    db.table("leads").update({"notes": new_notes}).eq("id", lead_id).execute()

    return {
        "lead_id": lead_id,
        "business": lead.get("business_name"),
        "enrichment": enrichment,
        "notes_updated": True,
    }


@router.post("/bulk-discover")
async def bulk_discover_social(category: str = "", city: str = ""):
    """Search Google for business social media profiles in a category+city."""
    if not category:
        raise HTTPException(400, "Category is required")

    from app.core.config import get_settings
    settings = get_settings()
    api_key = settings.google_places_key

    if not api_key:
        raise HTTPException(500, "Google API key not configured")

    query = f"{category} {city}" if city else category

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": api_key},
            timeout=15,
        )
        if resp.status_code != 200:
            raise HTTPException(500, "Google search failed")

        results = resp.json().get("results", [])

    businesses = []
    for r in results[:10]:
        place_id = r.get("place_id")
        if not place_id:
            continue

        # Get details including website
        async with httpx.AsyncClient() as client:
            detail_resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={"place_id": place_id, "fields": "name,website,formatted_phone_number,formatted_address,rating,user_ratings_total,url", "key": api_key},
                timeout=10,
            )
            if detail_resp.status_code == 200:
                detail = detail_resp.json().get("result", {})
                businesses.append({
                    "name": detail.get("name"),
                    "website": detail.get("website"),
                    "phone": detail.get("formatted_phone_number"),
                    "address": detail.get("formatted_address"),
                    "rating": detail.get("rating"),
                    "reviews": detail.get("user_ratings_total"),
                    "google_maps": detail.get("url"),
                })

    return {
        "query": query,
        "found": len(businesses),
        "businesses": businesses,
    }
