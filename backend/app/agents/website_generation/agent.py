from __future__ import annotations
import json
import httpx
from app.core.llm import chat_completion
from app.core.config import get_settings
from app.services.lead_service import LeadService
from app.services.website_service import WebsiteService
from app.schemas.websites import WebsiteCreate
from app.core.logging import get_logger
from app.services.usage_tracker import track_usage
from app.agents.design_systems import get_design_system
from app.agents.website_generation.system_prompt import SYSTEM_PROMPT, get_industry_prompt
from app.agents.system_prompt import WEBSITE_SYSTEM_PROMPT, CONTENT_GENERATION_FIELDS

logger = get_logger(__name__)


async def find_competitor_websites(category: str) -> list[dict]:
    """Search Google globally for best businesses in this category for inspiration."""
    settings = get_settings()
    api_key = settings.google_places_key
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient() as client:
            # Search globally - not restricted to location
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": f"best {category} website design inspiration", "key": api_key},
                timeout=10,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                competitors = []
                for r in results[:5]:
                    place_id = r.get("place_id")
                    if place_id:
                        detail_resp = await client.get(
                            "https://maps.googleapis.com/maps/api/place/details/json",
                            params={
                                "place_id": place_id,
                                "fields": "name,website,rating,user_ratings_total",
                                "key": api_key,
                            },
                            timeout=10,
                        )
                        if detail_resp.status_code == 200:
                            detail = detail_resp.json().get("result", {})
                            if detail.get("website"):
                                competitors.append({
                                    "name": detail.get("name"),
                                    "website": detail.get("website"),
                                    "rating": detail.get("rating"),
                                    "reviews": detail.get("user_ratings_total"),
                                })
                return competitors
    except Exception as e:
        logger.warning("Failed to find competitors", error=str(e))
    return []


async def get_pexels_images(category: str) -> list[str]:
    """Get free images from Pexels API for the category."""
    # Using Pexels free API
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.pexels.com/v1/search",
                params={"query": category, "per_page": 8, "orientation": "landscape"},
                headers={"Authorization": "563492ad6f91700001000001a1b2c3d4e5f6a7b8c9d0e1f2"},
                timeout=10,
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                return [p["src"]["large"] for p in photos]
    except Exception:
        pass
    return []


async def generate_website(lead_id: str, template: str = "store") -> dict:
    """Generate a professional AI website inspired by real competitor sites globally."""
    logger.info("Generating website", lead_id=lead_id, template=template)

    lead_service = LeadService()
    website_service = WebsiteService()

    lead = lead_service.get(lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    category = lead.get("category", template)

    # Get design system using UI UX Pro Max methodology
    # (67 styles, 161 color palettes, 57 font pairings, industry-specific reasoning)
    design_system = get_design_system(category)
    
    # Enhanced design intelligence (UI UX Pro Max methodology)
    design_reasoning = {
        "restaurant": {"style": "Organic Biophilic + Warm Editorial", "pattern": "Hero-Centric + Social Proof", "fonts": "Playfair Display / Lato", "mood": "Warm, inviting, appetizing", "effects": "Smooth transitions, parallax food images, warm color grading", "avoid": "Cold blues, tech-looking layouts, stock photos"},
        "cafe": {"style": "Nature Distilled + Soft UI", "pattern": "Storytelling-Driven", "fonts": "Cormorant Garamond / Montserrat", "mood": "Cozy, artisanal, relaxed", "effects": "Subtle animations, warm tones, handwritten accents", "avoid": "Corporate feel, harsh colors, grid-heavy layouts"},
        "gym": {"style": "Vibrant Block-based + Motion-Driven", "pattern": "Conversion-Optimized", "fonts": "Oswald / Inter", "mood": "Energetic, powerful, motivating", "effects": "Bold transitions, high contrast, dynamic imagery", "avoid": "Pastel colors, delicate fonts, static layouts"},
        "salon": {"style": "Soft UI Evolution + Glassmorphism", "pattern": "Hero-Centric + Social Proof", "fonts": "Cormorant Garamond / Montserrat", "mood": "Elegant, luxurious, calming", "effects": "Soft shadows, gentle hover states, smooth transitions", "avoid": "Bright neon, harsh animations, dark mode"},
        "dentist": {"style": "Minimalism + Accessible Design", "pattern": "Trust & Authority", "fonts": "DM Sans / Inter", "mood": "Clean, trustworthy, professional", "effects": "Subtle micro-interactions, clean transitions", "avoid": "Playful fonts, dark themes, complex animations"},
        "clinic": {"style": "Minimalism + Inclusive Design", "pattern": "Trust & Authority + Feature-Rich", "fonts": "Source Sans Pro / Inter", "mood": "Professional, calming, trustworthy", "effects": "Clean transitions, clear hierarchy, accessible contrast", "avoid": "Bright colors, playful elements, complex layouts"},
        "hotel": {"style": "Liquid Glass + Parallax Storytelling", "pattern": "Storytelling-Driven + Social Proof", "fonts": "Playfair Display / Raleway", "mood": "Luxurious, immersive, aspirational", "effects": "Parallax scrolling, smooth reveals, premium feel", "avoid": "Budget feel, cluttered layouts, generic stock"},
        "store": {"style": "Bento Grid + Flat Design", "pattern": "Feature-Rich Showcase", "fonts": "Poppins / Inter", "mood": "Modern, clean, shoppable", "effects": "Card hover effects, smooth transitions, clear CTAs", "avoid": "Overwhelming colors, tiny text, complex navigation"},
        "lawyer": {"style": "Swiss Modernism 2.0 + Editorial Grid", "pattern": "Trust & Authority", "fonts": "Libre Baskerville / Source Sans Pro", "mood": "Authoritative, sophisticated, trustworthy", "effects": "Minimal animations, strong typography, clean lines", "avoid": "Playful elements, bright colors, casual tone"},
        "photographer": {"style": "Exaggerated Minimalism + Motion-Driven", "pattern": "Hero-Centric + Interactive Demo", "fonts": "Space Grotesk / Inter", "mood": "Creative, bold, visual-first", "effects": "Image-focused, smooth galleries, cursor interactions", "avoid": "Text-heavy, corporate layouts, small images"},
        "solar": {"style": "Organic Biophilic + Conversion-Optimized", "pattern": "Feature-Rich + Social Proof", "fonts": "Manrope / Inter", "mood": "Eco-friendly, modern, trustworthy", "effects": "Green accents, clean data display, trust badges", "avoid": "Dark themes, complex jargon, cluttered layouts"},
        "school": {"style": "Vibrant Block-based + Inclusive Design", "pattern": "Feature-Rich + Social Proof", "fonts": "Nunito / Open Sans", "mood": "Friendly, approachable, educational", "effects": "Colorful accents, clear sections, easy navigation", "avoid": "Dark themes, complex layouts, corporate feel"},
    }
    
    category_design = design_reasoning.get(category, design_reasoning.get("store", {}))
    design_info = f"""
DESIGN SYSTEM TO FOLLOW (UI UX Pro Max methodology):
Style: {category_design.get("style", design_system["name"])}
Pattern: {category_design.get("pattern", "Hero-Centric")}
Typography: {category_design.get("fonts", "Inter / System")}
Mood: {category_design.get("mood", "Professional")}
Effects: {category_design.get("effects", "Smooth transitions")}
AVOID: {category_design.get("avoid", "Generic layouts")}
Base Rules: {design_system["rules"]}

PRE-DELIVERY CHECKLIST:
- No emojis as decorative icons (use descriptive emoji only in icon field)
- All text must have 4.5:1 contrast ratio minimum
- Responsive design: works on 375px mobile to 1440px desktop
- CTA above fold and repeated after testimonials
- Social proof near CTA (rating, review count)
- Location mentioned in hero or immediately visible"""

    # Find real competitor websites globally for inspiration
    competitors = await find_competitor_websites(category)
    competitor_info = ""
    if competitors:
        competitor_info = "\n\nHere are successful businesses in this category globally (study their websites for design inspiration):\n"
        for c in competitors[:3]:
            competitor_info += f"- {c['name']} ({c['website']}) - Rating: {c.get('rating', 'N/A')}, Reviews: {c.get('reviews', 'N/A')}\n"

    prompt = f"""You are a world-class web designer who creates stunning, high-converting business websites.
Study the best {category} websites globally and create something equally impressive.

BUSINESS DETAILS:
- Name: {lead['business_name']}
- Category: {category}
- Address: {lead.get('address', 'N/A')}
- Phone: {lead.get('phone', 'N/A')}
- Rating: {lead.get('rating', 'N/A')} ({lead.get('review_count', 0)} reviews)
- Existing Website: {lead.get('website') or 'NONE'}
{competitor_info}
{design_info}

REFERENCE: Study websites like solar-panel-india.com for structure inspiration.
Key sections that work well: trust badges, savings calculator concept, how-it-works steps, 
guarantee/promise section, FAQ, benefits list, brand logos, impact numbers.

Generate website content as JSON with ALL these sections:
{{
    "hero_title": "Bold headline, max 8 words. Create urgency or desire.",
    "hero_subtitle": "2 sentences. Unique value + social proof.",
    "hero_offer": "A special offer or hook (e.g., 'Free consultation worth Rs.2000' or '20% off this month')",
    "trust_badges": ["badge1", "badge2", "badge3"],
    "about": "4-5 sentences. Tell a compelling story about expertise and passion.",
    "services": [
        {{"name": "Service", "description": "2 sentences focusing on customer benefit", "tags": ["tag1", "tag2"], "icon": "emoji"}}
    ],
    "how_it_works": [
        {{"step": "1", "title": "Step title", "description": "What happens in this step"}}
    ],
    "benefits": ["Benefit 1 in one line", "Benefit 2", "Benefit 3", "Benefit 4", "Benefit 5", "Benefit 6"],
    "why_choose_us": [
        {{"icon": "emoji", "title": "Reason title", "description": "1 sentence why this matters"}}
    ],
    "impact_numbers": [
        {{"number": "500+", "label": "Happy Customers"}},
        {{"number": "4.8", "label": "Google Rating"}},
        {{"number": "5+", "label": "Years Experience"}},
        {{"number": "100%", "label": "Satisfaction"}}
    ],
    "testimonials": [
        {{"name": "Indian Name", "text": "Specific emotional review, 2-3 sentences", "rating": 5, "detail": "e.g., 3kW System, Kothrud"}}
    ],
    "faq": [
        {{"question": "Common question customers ask", "answer": "Clear helpful answer in 2-3 sentences"}}
    ],
    "cta_text": "Primary action button text",
    "cta_secondary": "Secondary action",
    "contact_info": {{
        "phone": "{lead.get('phone', '')}",
        "email": "professional email",
        "address": "{lead.get('address', '')}",
        "hours": "Realistic hours for {category}"
    }},
    "color_scheme": {{
        "primary": "#hex fitting for {category}",
        "secondary": "#hex lighter",
        "accent": "#hex bold contrast"
    }},
    "seo_title": "Primary Keyword - Business Name | City (under 60 chars, include main keyword first)",
    "seo_description": "Include primary keyword, location, USP, and CTA in under 155 chars. This appears in Google search results.",
    "seo_keywords": ["primary keyword", "location + service", "near me variant", "specific service 1", "specific service 2"],
    "seo_h1": "Main heading with primary keyword naturally included",
    "seo_description": "Under 155 chars"
}}

SEO RULES (Critical for Google ranking):
- hero_title should contain the PRIMARY keyword for this business type
- about section must mention: city name, service type, years of experience (Google loves E-E-A-T)
- Each service name should be a searchable keyword (what people actually Google)
- testimonials should mention specific services (adds keyword density naturally)
- FAQ questions should match "People Also Ask" queries for this business type
- Use location name (city) at least 3 times across all content
- seo_title format: "Primary Keyword in City - Business Name" (e.g., "Best Dentist in Pune - SmileCare Dental")
- seo_description must include: keyword + location + USP + CTA

RULES:
- Use actual emoji characters for icons (not text names)
- 5-6 services, 4 how_it_works steps, 6 benefits, 4 why_choose_us, 3 testimonials, 5-6 FAQs
- Make everything specific to {category} business
- Indian names for testimonials
- Return ONLY valid JSON

QUALITY SEO RULES (Critical for Google ranking):
- hero_title should contain the PRIMARY keyword for this business type
- about section must mention: city name, service type, years of experience (Google loves E-E-A-T)
- Each service name should be a searchable keyword (what people actually Google)
- testimonials should mention specific services (adds keyword density naturally)
- FAQ questions should match "People Also Ask" queries for this business type
- Use location name (city) at least 3 times across all content
- seo_title format: "Primary Keyword in City - Business Name" (e.g., "Best Dentist in Pune - SmileCare Dental")
- seo_description must include: keyword + location + USP + CTA

RULES:
- Return ONLY valid JSON
- No generic text like "Welcome to our business" or "We provide quality service"
- Every sentence should be specific to THIS type of business
- Testimonials must have Indian names and sound authentic
- Colors should feel premium (avoid basic red/blue unless it fits)
- Think: would a real business pay $5000 for this website? Make it worth that."""

    content = await chat_completion([{"role": "system", "content": WEBSITE_SYSTEM_PROMPT}, {"role": "user", "content": prompt}])

    # Parse the response
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        content_data = json.loads(cleaned)
    except json.JSONDecodeError:
        content_data = {"raw_content": content}

    website = website_service.create(
        WebsiteCreate(
            lead_id=lead_id,
            template=template,
            content=content_data,
        )
    )

    track_usage("gemini_website_gen", 1)

    # Auto-assign slug using AI for clean, short URL
    try:
        import re as _re
        def _make_slug(name):
            s = name.lower().strip()
            s = _re.sub(r'[^a-z0-9\s-]', '', s)
            s = _re.sub(r'[\s_]+', '-', s)
            s = _re.sub(r'-+', '-', s).strip('-')
            return s[:40] if s else 'business'
        
        # Try AI-generated slug (shorter, cleaner)
        try:
            slug_prompt = f"Suggest a short, clean URL slug for a {category} business named \"{lead.get('business_name', '')}\". Rules: lowercase, hyphens only, max 25 chars, no special chars, memorable. Return ONLY the slug, nothing else."
            ai_slug = await chat_completion([{"role": "user", "content": slug_prompt}])
            ai_slug = ai_slug.strip().lower().strip('"').strip("'")
            ai_slug = _re.sub(r'[^a-z0-9-]', '', ai_slug.replace(' ', '-'))
            ai_slug = _re.sub(r'-+', '-', ai_slug).strip('-')
            if len(ai_slug) > 3 and len(ai_slug) <= 30:
                base_slug = ai_slug
            else:
                base_slug = _make_slug(lead.get("business_name", "business"))
        except Exception:
            base_slug = _make_slug(lead.get("business_name", "business"))
        slug = base_slug
        # Check uniqueness
        from app.core.config import get_settings as _gs
        from supabase import create_client as _sc
        _settings = _gs()
        _sb = _sc(_settings.supabase_url, _settings.supabase_service_key)
        counter = 1
        while True:
            existing = _sb.table("websites").select("id").eq("slug", slug).execute()
            if not existing.data:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        _sb.table("websites").update({"slug": slug}).eq("id", website["id"]).execute()
        logger.info("Auto-assigned slug", slug=slug, website_id=website["id"])
    except Exception as e:
        logger.warning("Failed to assign slug", error=str(e))
    logger.info("Website generated", website_id=website["id"])

    # Auto-generate logo for the website
    try:
        from app.api.routes.logo_gen import generate_image_logo
        from pydantic import BaseModel
        class _LogoReq(BaseModel):
            style: str = "modern"
        logo_result = await generate_image_logo(website["id"], _LogoReq(style="modern"))
        if logo_result.get("logo_url"):
            # Store logo URL in website content
            if isinstance(content_data, dict):
                content_data["logo_url"] = logo_result["logo_url"]
                website_service.db.table("websites").update({"content": content_data}).eq("id", website["id"]).execute()
            logger.info("Auto-generated logo", url=logo_result["logo_url"])
    except Exception as e:
        logger.warning("Auto logo generation failed", error=str(e))
    # Auto-generate products for the store
    try:
        from app.core.supabase import get_supabase as _pdb
        db_p = _pdb()
        # Check if products already exist
        existing_prods = db_p.table("store_products").select("id").eq("website_id", website["id"]).limit(1).execute()
        if not existing_prods.data:
            category = lead.get("category", "general") if lead else "general"
            cat_lower = category.lower()
            # Category-specific products with images
            product_sets = {
                "salon": [
                    {"name": "Haircut & Styling", "price": 299, "category": "Hair", "image_url": "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=300&h=200&fit=crop"},
                    {"name": "Facial Treatment", "price": 599, "category": "Skin", "image_url": "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=300&h=200&fit=crop"},
                    {"name": "Hair Color", "price": 1499, "category": "Hair", "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=300&h=200&fit=crop"},
                    {"name": "Bridal Package", "price": 4999, "category": "Special", "image_url": "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=300&h=200&fit=crop"},
                ],
                "restaurant": [
                    {"name": "Veg Thali", "price": 149, "category": "Meals", "image_url": "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=300&h=200&fit=crop"},
                    {"name": "Special Biryani", "price": 249, "category": "Rice", "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=300&h=200&fit=crop"},
                    {"name": "Paneer Butter Masala", "price": 199, "category": "Main Course", "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=300&h=200&fit=crop"},
                    {"name": "Fresh Juice", "price": 79, "category": "Drinks", "image_url": "https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=300&h=200&fit=crop"},
                ],
                "gym": [
                    {"name": "Monthly Membership", "price": 999, "category": "Membership", "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=300&h=200&fit=crop"},
                    {"name": "Personal Training", "price": 4999, "category": "Training", "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=200&fit=crop"},
                    {"name": "Yoga Classes", "price": 1499, "category": "Classes", "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=300&h=200&fit=crop"},
                ],
                "default": [
                    {"name": "Service Package 1", "price": 499, "category": "Services", "image_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&h=200&fit=crop"},
                    {"name": "Premium Service", "price": 999, "category": "Premium", "image_url": "https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=300&h=200&fit=crop"},
                    {"name": "Consultation", "price": 299, "category": "General", "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=300&h=200&fit=crop"},
                    {"name": "Special Offer", "price": 199, "category": "Offers", "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=300&h=200&fit=crop"},
                ],
            }
            # Find matching products
            prods = product_sets.get("default")
            for key in product_sets:
                if key in cat_lower or cat_lower in key:
                    prods = product_sets[key]
                    break
            # Insert products
            for p in prods:
                db_p.table("store_products").insert({
                    "website_id": website["id"],
                    "name": p["name"],
                    "price": p["price"],
                    "category": p.get("category", "General"),
                    "image_url": p.get("image_url", ""),
                    "description": "",
                    "in_stock": True,
                    "stock_qty": 99,
                }).execute()
            logger.info("Auto-generated products", count=len(prods), website_id=website["id"])
    except Exception as e:
        logger.warning("Auto product generation failed", error=str(e))

    # Auto QA review after generation
    try:
        from app.agents.qa_review.agent import review_website as qa_review
        import asyncio
        asyncio.ensure_future(qa_review(website["id"]))
        logger.info("QA review scheduled", website_id=website["id"])
    except Exception as e:
        logger.warning("QA review scheduling failed", error=str(e))

    return website
