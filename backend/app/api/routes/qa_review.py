"""QA Review API routes."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/qa", tags=["qa-review"])


@router.post("/review/{website_id}")
async def trigger_review(website_id: str):
    """Trigger QA review for a specific website."""
    from app.agents.qa_review.agent import review_website
    result = await review_website(website_id)
    return result


@router.get("/review/{website_id}")
async def get_review(website_id: str):
    """Get QA review results for a website."""
    from app.core.supabase import get_supabase
    from app.services.website_service import WebsiteService
    
    db = get_supabase()
    
    # Try qa_reviews table first
    try:
        result = db.table("qa_reviews").select("*").eq("website_id", website_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    
    # Fallback to content._qa_review
    ws = WebsiteService()
    website = ws.get(website_id)
    if website and isinstance(website.get("content"), dict):
        review = website["content"].get("_qa_review")
        if review:
            return review
    
    return {"error": "No review found", "website_id": website_id}


@router.get("/review-all")
async def review_all(limit: int = 5):
    """Review recent websites that haven't been reviewed."""
    from app.agents.qa_review.agent import review_all_recent
    results = await review_all_recent(limit)
    return {"reviewed": len(results), "results": results}


@router.get("/lead/{lead_id}")
async def get_review_for_lead(lead_id: str):
    """Get QA review for a lead's website."""
    from app.core.supabase import get_supabase
    from app.services.website_service import WebsiteService
    
    db = get_supabase()
    ws = WebsiteService()
    
    websites = ws.get_by_lead(lead_id)
    if not websites:
        return {"error": "No website found for this lead"}
    
    website_id = websites[0]["id"]
    
    # Try qa_reviews table
    try:
        result = db.table("qa_reviews").select("*").eq("website_id", website_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    
    # Check content
    website = ws.get(website_id)
    if website and isinstance(website.get("content"), dict):
        review = website["content"].get("_qa_review")
        if review:
            return review
    
    # No review yet - trigger one
    from app.agents.qa_review.agent import review_website
    result = await review_website(website_id)
    return result