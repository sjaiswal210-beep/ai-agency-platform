from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.supabase import get_supabase
from app.core.llm import chat_completion
from datetime import datetime, timedelta

router = APIRouter(prefix="/growth-agent", tags=["growth-agent"])


@router.get("/{website_id}/recommendations")
async def get_growth_recommendations(website_id: str):
    """AI analyzes business performance and gives actionable growth tips."""
    service = WebsiteService()
    lead_service = LeadService()
    db = get_supabase()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")

    business_name = lead.get("business_name", "Business")
    category = lead.get("category", "business")
    rating = lead.get("rating", 0)
    reviews = lead.get("review_count", 0)
    address = lead.get("address", "")
    phone = lead.get("phone", "")

    # Get analytics data
    since_30d = (datetime.utcnow() - timedelta(days=30)).isoformat()
    try:
        views = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "page_view").gte("created_at", since_30d).execute()).count or 0
        calls = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "call_click").gte("created_at", since_30d).execute()).count or 0
        wa_clicks = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "whatsapp_click").gte("created_at", since_30d).execute()).count or 0
        leads_count = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "lead_form").gte("created_at", since_30d).execute()).count or 0
    except Exception:
        views = calls = wa_clicks = leads_count = 0

    prompt = f"""You are an AI Growth Agent for local businesses. Analyze this business and provide 5 specific, actionable growth recommendations.

BUSINESS DATA:
- Name: {business_name}
- Category: {category}
- Rating: {rating}/5 ({reviews} reviews)
- Location: {address}
- Phone: {phone}
- Website Views (30d): {views}
- Call Clicks (30d): {calls}
- WhatsApp Clicks (30d): {wa_clicks}
- Form Leads (30d): {leads_count}

ANALYSIS RULES:
- Be specific (not generic advice)
- Include numbers and targets
- Prioritize by impact (highest first)
- Consider the business category
- Focus on actions that bring customers THIS WEEK
- Include both free and paid suggestions
- Reference Indian market context

Return as JSON array:
[
  {{"priority": 1, "title": "Short title", "action": "Specific action to take", "expected_impact": "What result to expect", "effort": "low/medium/high", "category": "seo/social/reviews/ads/content/local"}}
]

Return ONLY valid JSON array."""

    result = await chat_completion([{"role": "user", "content": prompt}])

    # Parse
    import json
    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        recommendations = json.loads(cleaned)
    except Exception:
        recommendations = [{"priority": 1, "title": "Growth Analysis", "action": cleaned[:500], "expected_impact": "Improved visibility", "effort": "medium", "category": "general"}]

    return {
        "business": business_name,
        "category": category,
        "metrics": {"views_30d": views, "calls_30d": calls, "whatsapp_30d": wa_clicks, "leads_30d": leads_count},
        "recommendations": recommendations,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/{website_id}/weekly-plan")
async def weekly_action_plan(website_id: str):
    """Generate a specific 7-day action plan for the business."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")

    business_name = lead.get("business_name", "Business")
    category = lead.get("category", "business")

    prompt = f"""Create a 7-day growth action plan for a {category} business named "{business_name}".
Each day should have ONE specific action that takes 15-30 minutes.
Focus on getting more customers through Google, WhatsApp, and social media.
Indian market context. Mix of free and low-cost actions.

Return as JSON:
{{
  "monday": {{"task": "...", "platform": "google/instagram/whatsapp/offline", "time_needed": "15 min"}},
  "tuesday": {{"task": "...", "platform": "...", "time_needed": "..."}},
  "wednesday": {{"task": "...", "platform": "...", "time_needed": "..."}},
  "thursday": {{"task": "...", "platform": "...", "time_needed": "..."}},
  "friday": {{"task": "...", "platform": "...", "time_needed": "..."}},
  "saturday": {{"task": "...", "platform": "...", "time_needed": "..."}},
  "sunday": {{"task": "...", "platform": "...", "time_needed": "..."}}
}}

Return ONLY valid JSON."""

    result = await chat_completion([{"role": "user", "content": prompt}])

    import json
    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        plan = json.loads(cleaned)
    except Exception:
        plan = {"error": "Could not generate plan", "raw": cleaned[:300]}

    return {"business": business_name, "category": category, "weekly_plan": plan}


@router.get("/{website_id}/competitor-snapshot")
async def competitor_snapshot(website_id: str):
    """Quick competitor analysis - find similar businesses nearby."""
    service = WebsiteService()
    lead_service = LeadService()
    db = get_supabase()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")

    category = lead.get("category", "")
    address = lead.get("address", "")
    rating = float(lead.get("rating", 0) or 0)

    # Find competitors in same category
    try:
        competitors = db.table("leads").select("business_name, rating, review_count, address, phone").ilike("category", f"%{category}%").neq("id", lead["id"]).order("rating", desc=True).limit(5).execute()
        comp_list = competitors.data or []
    except Exception:
        comp_list = []

    # Calculate position
    all_ratings = [float(c.get("rating", 0) or 0) for c in comp_list] + [rating]
    all_ratings.sort(reverse=True)
    position = all_ratings.index(rating) + 1 if rating in all_ratings else len(all_ratings)

    return {
        "business": lead.get("business_name"),
        "your_rating": rating,
        "your_reviews": lead.get("review_count", 0),
        "position": position,
        "total_competitors": len(comp_list),
        "competitors": [
            {"name": c.get("business_name"), "rating": c.get("rating"), "reviews": c.get("review_count"), "address": (c.get("address") or "")[:50]}
            for c in comp_list
        ],
        "insight": f"You rank #{position} out of {len(comp_list) + 1} {category} businesses in your area." if comp_list else "No competitors found in database yet.",
    }
