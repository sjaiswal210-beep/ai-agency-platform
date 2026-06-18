"""Website QA Review Agent - Reviews generated websites for quality and correctness."""
from __future__ import annotations
import json
from app.core.llm import chat_completion
from app.core.logging import get_logger
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.supabase import get_supabase

logger = get_logger(__name__)


async def review_website(website_id: str) -> dict:
    """Review a generated website for quality, correctness, and image issues."""
    ws = WebsiteService()
    ls = LeadService()
    
    website = ws.get(website_id)
    if not website:
        return {"error": "Website not found", "score": 0}
    
    content = website.get("content", {})
    if not content or not isinstance(content, dict):
        return {"error": "No content to review", "score": 0}
    
    lead = ls.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Unknown") if lead else "Unknown"
    category = lead.get("category", "business") if lead else "business"
    address = lead.get("address", "") if lead else ""
    
    # Build review prompt
    prompt = f"""You are a strict website QA agent. Review this generated website content for a real business.

BUSINESS INFO:
- Name: {business_name}
- Category: {category}
- Address: {address}
- Phone: {lead.get('phone', 'N/A') if lead else 'N/A'}

WEBSITE CONTENT (JSON):
{json.dumps(content, indent=2, default=str)[:4000]}

REVIEW CRITERIA (score each 1-10):
1. RELEVANCE: Does content match the business type? Are services accurate for this category?
2. IMAGES: Check hero_title, services - would stock images match? Flag if all services use same description pattern.
3. CONTENT QUALITY: Is the text specific (not generic)? Does it mention the city/location?
4. SEO: Does it have proper keywords for the business type and location?
5. STRUCTURE: Are all required sections present (hero, services, about, testimonials, FAQ, contact)?
6. PROFESSIONALISM: Would a business owner be proud of this website?

ISSUES TO FLAG:
- Generic text like "Welcome to our business" or "We provide quality service"
- Services that don't match the business category
- Missing phone number or address in contact
- Testimonials that sound fake or don't mention specific services
- FAQ questions not relevant to the business type
- Color scheme that doesn't fit the industry

RESPOND AS JSON:
{{
    "overall_score": 7,
    "scores": {{
        "relevance": 8,
        "images": 5,
        "content_quality": 7,
        "seo": 6,
        "structure": 9,
        "professionalism": 7
    }},
    "issues": [
        {{"severity": "high", "area": "images", "detail": "All services appear to use same generic image"}},
        {{"severity": "medium", "area": "content", "detail": "About section doesn't mention city name"}}
    ],
    "fixes_needed": [
        "Regenerate service images with category-specific queries",
        "Add city name to about section",
        "Make FAQ more specific to this business type"
    ],
    "summary": "Brief 2 sentence summary of the website quality"
}}"""

    try:
        response = await chat_completion([{"role": "user", "content": prompt}])
        
        # Parse response
        cleaned = response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        review = json.loads(cleaned)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("QA review parse failed", error=str(e))
        review = {
            "overall_score": 5,
            "scores": {},
            "issues": [{"severity": "medium", "area": "review", "detail": f"Could not parse review: {str(e)[:100]}"}],
            "fixes_needed": [],
            "summary": "Review could not be completed automatically."
        }
    
    # Store review in database
    db = get_supabase()
    review_data = {
        "website_id": website_id,
        "lead_id": website.get("lead_id", ""),
        "business_name": business_name,
        "overall_score": review.get("overall_score", 0),
        "scores": review.get("scores", {}),
        "issues": review.get("issues", []),
        "fixes_needed": review.get("fixes_needed", []),
        "summary": review.get("summary", ""),
        "status": "reviewed"
    }
    
    try:
        # Try to upsert into qa_reviews table
        existing = db.table("qa_reviews").select("id").eq("website_id", website_id).limit(1).execute()
        if existing.data:
            db.table("qa_reviews").update(review_data).eq("website_id", website_id).execute()
        else:
            db.table("qa_reviews").insert(review_data).execute()
    except Exception as e:
        # Table might not exist - store in website content instead
        logger.warning("Could not store QA review in table, storing in website content", error=str(e))
        try:
            content["_qa_review"] = review_data
            db.table("websites").update({"content": content}).eq("id", website_id).execute()
        except Exception:
            pass
    
    # Auto-fix if score is low
    if review.get("overall_score", 10) < 6:
        try:
            await auto_fix_website(website_id, review, content, lead)
            review["auto_fixed"] = True
        except Exception as e:
            logger.warning("Auto-fix failed", error=str(e))
            review["auto_fixed"] = False
    
    logger.info("QA review completed", website_id=website_id, score=review.get("overall_score"))
    return review


async def auto_fix_website(website_id: str, review: dict, content: dict, lead: dict) -> None:
    """Auto-fix issues found during QA review."""
    fixes = review.get("fixes_needed", [])
    if not fixes:
        return
    
    business_name = lead.get("business_name", "") if lead else ""
    category = lead.get("category", "business") if lead else "business"
    address = lead.get("address", "") if lead else ""
    
    fix_prompt = f"""You are a website content fixer. The QA agent found these issues with a {category} business website for "{business_name}" in {address}:

ISSUES:
{json.dumps(review.get('issues', []), indent=2)}

FIXES NEEDED:
{json.dumps(fixes, indent=2)}

CURRENT CONTENT:
{json.dumps(content, indent=2, default=str)[:3000]}

Fix the content. Only return the CHANGED fields as JSON. For example:
{{
    "about": "New improved about text mentioning the city...",
    "services": [... updated services with better descriptions ...],
    "faq": [... more relevant FAQ ...]
}}

Only include fields that need fixing. Keep everything else as-is."""

    try:
        response = await chat_completion([{"role": "user", "content": fix_prompt}])
        cleaned = response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        fixes_data = json.loads(cleaned)
        
        # Merge fixes into content
        for key, value in fixes_data.items():
            content[key] = value
        
        # Save updated content
        db = get_supabase()
        db.table("websites").update({"content": content}).eq("id", website_id).execute()
        logger.info("Auto-fixed website", website_id=website_id, fields_fixed=list(fixes_data.keys()))
    except Exception as e:
        logger.warning("Auto-fix content generation failed", error=str(e))


async def review_all_recent(limit: int = 10) -> list:
    """Review all recently generated websites that haven't been reviewed yet."""
    db = get_supabase()
    
    # Get recent websites
    websites = db.table("websites").select("id,content,lead_id").order("created_at", desc=True).limit(limit).execute()
    
    results = []
    for w in (websites.data or []):
        content = w.get("content", {})
        # Review all (re-review allowed)
        
        try:
            review = await review_website(w["id"])
            results.append({"website_id": w["id"], "review": review})
        except Exception as e:
            results.append({"website_id": w["id"], "error": str(e)})
    
    return results