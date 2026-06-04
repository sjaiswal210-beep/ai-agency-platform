from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.core.llm import chat_completion
from app.services.lead_service import LeadService
from app.services.website_service import WebsiteService
from app.core.logging import get_logger

router = APIRouter(prefix="/growth", tags=["growth"])
logger = get_logger(__name__)


class ContentRequest(BaseModel):
    topic: str = ""
    tone: str = "professional"  # professional, casual, funny, urgent


# ============ SEO TOOLS ============

@router.post("/{lead_id}/seo-keywords")
async def generate_seo_keywords(lead_id: str):
    """Generate SEO keywords for a business to rank on Google."""
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    prompt = f"""Generate a comprehensive SEO keyword strategy for:
Business: {lead['business_name']}
Category: {lead.get('category', 'business')}
Location: {lead.get('address', '')}

Provide:
1. PRIMARY KEYWORDS (5) - Main search terms with monthly search volume estimate
2. LONG-TAIL KEYWORDS (10) - Specific phrases people search
3. LOCAL SEO KEYWORDS (5) - Location-based searches
4. QUESTION KEYWORDS (5) - "How to", "Where to", "Best" queries
5. COMPETITOR KEYWORDS (3) - Terms competitors rank for
6. GOOGLE MY BUSINESS tips (3) - How to optimize their listing

Format clearly with headers."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    return {"business": lead["business_name"], "keywords": result}


# ============ GOOGLE ADS ============

@router.post("/{lead_id}/google-ads")
async def generate_google_ads(lead_id: str):
    """Generate Google Ads copy ready to use."""
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    prompt = f"""Create Google Ads campaigns for:
Business: {lead['business_name']}
Category: {lead.get('category', 'business')}
Location: {lead.get('address', '')}
Phone: {lead.get('phone', '')}

Generate 3 complete ad groups:
For each ad group provide:
- Campaign name
- 5 Headlines (max 30 chars each)
- 3 Descriptions (max 90 chars each)
- Display URL path
- Target keywords (5)
- Negative keywords (3)
- Suggested daily budget (INR)

Also provide:
- Recommended bid strategy
- Target audience settings
- Ad extensions to use (callout, sitelink, call)

Format clearly."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    return {"business": lead["business_name"], "ads": result}


# ============ SOCIAL MEDIA CALENDAR ============

@router.post("/{lead_id}/social-calendar")
async def generate_social_calendar(lead_id: str, days: int = Query(7, description="Number of days")):
    """Generate a social media content calendar."""
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    prompt = f"""Create a {days}-day social media content calendar for:
Business: {lead['business_name']}
Category: {lead.get('category', 'business')}

For each day provide:
- Day & date placeholder
- Platform (Instagram/Facebook/WhatsApp Status)
- Content type (Reel idea / Post / Story / Carousel)
- Caption (ready to copy-paste, with emojis and hashtags)
- Best posting time
- Visual description (what image/video to use)

Mix content types: educational, promotional, behind-the-scenes, testimonial, trending.
Make it specific to {lead.get('category', 'business')} industry.
Include relevant Indian festivals/events if applicable.

Format as a clear day-by-day calendar."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    return {"business": lead["business_name"], "calendar": result, "days": days}


# ============ COMPETITOR ANALYSIS ============

@router.post("/{lead_id}/competitor-analysis")
async def analyze_competitors(lead_id: str):
    """AI-powered competitor analysis and strategy."""
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    prompt = f"""Perform a competitor analysis for:
Business: {lead['business_name']}
Category: {lead.get('category', 'business')}
Location: {lead.get('address', '')}
Rating: {lead.get('rating', 'N/A')} ({lead.get('review_count', 0)} reviews)

Provide:
1. MARKET POSITION - Where this business likely stands
2. COMMON COMPETITORS - Types of competitors in this area
3. COMPETITIVE ADVANTAGES to highlight
4. WEAKNESSES to address
5. PRICING STRATEGY suggestions
6. DIFFERENTIATION IDEAS (5 unique selling points)
7. GROWTH OPPORTUNITIES (5 actionable ideas)
8. ONLINE PRESENCE SCORE (rate their digital presence 1-10)

Be specific to {lead.get('category', 'business')} in India."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    return {"business": lead["business_name"], "analysis": result}


# ============ EMAIL MARKETING ============

@router.post("/{lead_id}/email-sequence")
async def generate_email_sequence(lead_id: str):
    """Generate an email marketing sequence for customer retention."""
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    prompt = f"""Create a 5-email marketing sequence for:
Business: {lead['business_name']}
Category: {lead.get('category', 'business')}

Generate 5 emails:
1. WELCOME EMAIL - After first visit/purchase
2. VALUE EMAIL - Tips/education related to their service (Day 3)
3. OFFER EMAIL - Special discount/offer (Day 7)
4. SOCIAL PROOF - Testimonial/success story (Day 14)
5. RE-ENGAGEMENT - Win back inactive customers (Day 30)

For each email provide:
- Subject line (A/B test: 2 options)
- Preview text
- Email body (ready to send, with personalization tags like {{name}})
- CTA button text
- Best send time

Make it specific to {lead.get('category', 'business')}."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    return {"business": lead["business_name"], "emails": result}


# ============ BUSINESS PLAN ============

@router.post("/{lead_id}/growth-plan")
async def generate_growth_plan(lead_id: str):
    """Generate a 90-day business growth plan."""
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    prompt = f"""Create a 90-day growth plan for:
Business: {lead['business_name']}
Category: {lead.get('category', 'business')}
Location: {lead.get('address', '')}
Current Rating: {lead.get('rating', 'N/A')} ({lead.get('review_count', 0)} reviews)
Website: {lead.get('website') or 'None (we are building one)'}

Provide a week-by-week plan:

MONTH 1 (Foundation):
- Week 1-2: Quick wins
- Week 3-4: Systems setup

MONTH 2 (Growth):
- Week 5-6: Marketing launch
- Week 7-8: Customer acquisition

MONTH 3 (Scale):
- Week 9-10: Optimization
- Week 11-12: Expansion

For each week include:
- 3 specific action items
- Expected outcome
- Tools/resources needed
- Budget estimate (INR)

Also include:
- KPIs to track
- Revenue targets
- Customer acquisition cost estimate

Make it realistic for a small {lead.get('category', 'business')} in India."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    return {"business": lead["business_name"], "plan": result}


# ============ REVIEW MANAGEMENT ============

@router.post("/{lead_id}/review-strategy")
async def review_strategy(lead_id: str):
    """Generate a strategy to get more Google reviews."""
    lead = LeadService().get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    prompt = f"""Create a Google Review generation strategy for:
Business: {lead['business_name']}
Category: {lead.get('category', 'business')}
Current: {lead.get('rating', 'N/A')} rating, {lead.get('review_count', 0)} reviews

Provide:
1. REVIEW REQUEST TEMPLATES (3) - WhatsApp messages to ask for reviews
2. QR CODE STRATEGY - How to use QR codes for reviews
3. TIMING - Best moments to ask for reviews
4. INCENTIVE IDEAS (ethical, non-violating Google policy)
5. NEGATIVE REVIEW RESPONSE templates (3)
6. REVIEW GOALS - Monthly targets
7. GOOGLE REVIEW LINK format for their business
8. STAFF TRAINING tips for asking reviews

Target: Get to 100+ reviews in 90 days."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    return {"business": lead["business_name"], "strategy": result}
