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

@router.get("/dashboard", response_class=HTMLResponse)
async def qa_dashboard():
    """QA Review Dashboard - readable format."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    
    # Get recent websites with their QA data
    websites = db.table("websites").select("id,slug,content,lead_id").order("created_at", desc=True).limit(20).execute().data or []
    leads_data = db.table("leads").select("id,business_name").execute().data or []
    leads = {l["id"]: l.get("business_name", "Unknown") for l in leads_data if isinstance(l.get("id"), str)}
    
    cards = ""
    for w in websites:
        name = leads.get(w.get("lead_id", ""), "Unknown")
        slug = w.get("slug", "")
        content = w.get("content", {})
        review = content.get("_qa_review", {}) if isinstance(content, dict) else {}
        score = review.get("overall_score", "?")
        summary = review.get("summary", "Not reviewed yet")
        issues = review.get("issues", [])
        color = "#22c55e" if isinstance(score, int) and score >= 7 else "#f59e0b" if isinstance(score, int) and score >= 5 else "#ef4444" if isinstance(score, int) else "#64748b"
        
        issues_html = ""
        for iss in issues[:3]:
            sev_color = "#ef4444" if iss.get("severity") == "high" else "#f59e0b" if iss.get("severity") == "medium" else "#3b82f6"
            issues_html += f'<div style="font-size:.68rem;color:#94a3b8;padding:4px 0;border-left:2px solid {sev_color};padding-left:8px;margin-top:4px">[{iss.get("area","")}] {iss.get("detail","")[:80]}...</div>'
        
        cards += f'<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px;margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:center"><div><b style="font-size:.82rem">{name}</b><br><span style="font-size:.65rem;color:#64748b">{slug}.city-maps.online</span></div><div style="font-size:1.3rem;font-weight:900;color:{color}">{score}</div></div><p style="font-size:.7rem;color:#94a3b8;margin-top:8px">{summary[:120]}</p>{issues_html}</div>'
    
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>QA Dashboard</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:700px;margin:0 auto}}</style></head><body><h1 style="font-size:1.2rem;margin-bottom:4px">QA Review Dashboard</h1><p style="font-size:.75rem;color:#64748b;margin-bottom:16px">{len(websites)} recent sites</p><a href="/api/qa/review-all" style="display:inline-block;padding:8px 16px;background:#6366f1;color:#fff;border-radius:8px;font-size:.75rem;font-weight:700;text-decoration:none;margin-bottom:16px">Run QA on All</a>{cards}</body></html>'''
    return HTMLResponse(content=html)