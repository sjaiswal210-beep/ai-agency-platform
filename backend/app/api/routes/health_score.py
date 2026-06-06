from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.supabase import get_supabase
from datetime import datetime, timedelta

router = APIRouter(prefix="/health-score", tags=["health-score"])


@router.get("/{website_id}")
def get_health_score(website_id: str):
    """Calculate a business health score (0-100) with improvement suggestions."""
    service = WebsiteService()
    lead_service = LeadService()
    db = get_supabase()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")

    score = 0
    max_score = 100
    factors = []

    # 1. Has website (20 points)
    score += 20
    factors.append({"factor": "Website Created", "score": 20, "max": 20, "status": "good"})

    # 2. Google rating (15 points)
    rating = float(lead.get("rating", 0) or 0)
    rating_score = min(15, int(rating * 3))
    score += rating_score
    factors.append({"factor": "Google Rating", "score": rating_score, "max": 15, "status": "good" if rating >= 4 else "needs_work", "detail": f"{rating}/5"})

    # 3. Review count (15 points)
    reviews = int(lead.get("review_count", 0) or 0)
    review_score = min(15, reviews // 10)
    score += review_score
    factors.append({"factor": "Reviews", "score": review_score, "max": 15, "status": "good" if reviews >= 50 else "needs_work", "detail": f"{reviews} reviews"})

    # 4. Phone number (10 points)
    has_phone = bool(lead.get("phone"))
    phone_score = 10 if has_phone else 0
    score += phone_score
    factors.append({"factor": "Phone Listed", "score": phone_score, "max": 10, "status": "good" if has_phone else "missing"})

    # 5. Website has content (10 points)
    content = website.get("content", {})
    has_services = bool(content.get("services"))
    has_testimonials = bool(content.get("testimonials"))
    content_score = 5 * (int(has_services) + int(has_testimonials))
    score += content_score
    factors.append({"factor": "Website Content", "score": content_score, "max": 10, "status": "good" if content_score == 10 else "needs_work"})

    # 6. Traffic (15 points)
    since_30d = (datetime.utcnow() - timedelta(days=30)).isoformat()
    try:
        views = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).gte("created_at", since_30d).execute()).count or 0
    except Exception:
        views = 0
    traffic_score = min(15, views // 5)
    score += traffic_score
    factors.append({"factor": "Website Traffic", "score": traffic_score, "max": 15, "status": "good" if views >= 50 else "needs_work", "detail": f"{views} visits/30d"})

    # 7. Has slug/public URL (5 points)
    has_slug = bool(website.get("slug"))
    slug_score = 5 if has_slug else 0
    score += slug_score
    factors.append({"factor": "Public URL", "score": slug_score, "max": 5, "status": "good" if has_slug else "missing"})

    # 8. Has blog posts (10 points)
    try:
        blogs = (db.table("blog_posts").select("*", count="exact").eq("website_id", website_id).execute()).count or 0
    except Exception:
        blogs = 0
    blog_score = min(10, blogs * 3)
    score += blog_score
    factors.append({"factor": "Blog Content", "score": blog_score, "max": 10, "status": "good" if blogs >= 3 else "needs_work", "detail": f"{blogs} posts"})

    # Cap at 100
    score = min(score, 100)

    # Generate suggestions
    suggestions = []
    for f in factors:
        if f["status"] != "good":
            if f["factor"] == "Google Rating":
                suggestions.append("Improve your Google rating by asking satisfied customers for reviews")
            elif f["factor"] == "Reviews":
                suggestions.append("Get more Google reviews - aim for 50+ reviews for credibility")
            elif f["factor"] == "Phone Listed":
                suggestions.append("Add your phone number to improve contact rate")
            elif f["factor"] == "Website Content":
                suggestions.append("Add services and testimonials to your website")
            elif f["factor"] == "Website Traffic":
                suggestions.append("Share your website link daily on WhatsApp status and social media")
            elif f["factor"] == "Public URL":
                suggestions.append("Your website needs a public URL for sharing")
            elif f["factor"] == "Blog Content":
                suggestions.append("Add blog posts to improve SEO and Google ranking")

    # Grade
    if score >= 80:
        grade = "A"
        label = "Excellent"
    elif score >= 60:
        grade = "B"
        label = "Good"
    elif score >= 40:
        grade = "C"
        label = "Average"
    else:
        grade = "D"
        label = "Needs Work"

    return {
        "business": lead.get("business_name"),
        "score": score,
        "max_score": max_score,
        "grade": grade,
        "label": label,
        "factors": factors,
        "suggestions": suggestions,
    }
