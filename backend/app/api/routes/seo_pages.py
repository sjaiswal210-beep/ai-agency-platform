from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase
from app.core.llm import chat_completion
from app.services.lead_service import LeadService
from app.services.website_service import WebsiteService

router = APIRouter(prefix="/seo-pages", tags=["seo-pages"])


@router.get("/best-{category}-in-{city}", response_class=HTMLResponse)
def seo_landing_page(category: str, city: str):
    """Programmatic SEO page: Best {category} in {city} with real businesses."""
    db = get_supabase()
    lead_service = LeadService()
    website_service = WebsiteService()

    # Find businesses matching this category in this city
    all_leads = db.table("leads").select("*").ilike("category", f"%{category}%").execute()

    # Filter by city in address
    matching = []
    for lead in (all_leads.data or []):
        addr = (lead.get("address") or "").lower()
        if city.lower() in addr:
            matching.append(lead)

    # If no exact city match, use all in category
    if not matching:
        matching = (all_leads.data or [])[:10]

    # Sort by rating
    matching.sort(key=lambda x: float(x.get("rating") or 0), reverse=True)
    businesses = matching[:8]

    # Build listing cards
    cards = ""
    for i, biz in enumerate(businesses, 1):
        name = biz.get("business_name", "")
        rating = biz.get("rating", "N/A")
        reviews = biz.get("review_count", 0)
        phone = biz.get("phone", "")
        address = biz.get("address", "")

        # Find website slug
        slug = ""
        try:
            ws = db.table("websites").select("slug").eq("lead_id", biz["id"]).limit(1).execute()
            if ws.data:
                slug = ws.data[0].get("slug", "")
        except Exception:
            pass

        site_link = f'<a href="https://city-maps.online/{slug}" target="_blank" class="visit-btn">Visit Website</a>' if slug else ""
        call_link = f'<a href="tel:{phone}" class="call-btn">Call Now</a>' if phone else ""

        cards += f'''<div class="biz-card">
<div class="rank">#{i}</div>
<div class="biz-info">
<h3>{name}</h3>
<div class="meta"><span class="stars">{"★" * min(int(float(rating) if rating != "N/A" else 0), 5)} {rating}</span><span class="rev">({reviews} reviews)</span></div>
<p class="addr">{address}</p>
<div class="biz-actions">{call_link}{site_link}</div>
</div>
</div>'''

    title = f"Best {category.title()} in {city.title()}"
    desc = f"Find the top rated {category} businesses in {city.title()}. Compare ratings, reviews, and contact the best {category} near you."

    html = (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>{title} - Top {len(businesses)} Rated | City Maps</title>'
        f'<meta name="description" content="{desc}">'
        '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
        '<style>'
        "*{margin:0;padding:0;box-sizing:border-box}"
        "body{font-family:'Plus Jakarta Sans',sans-serif;background:#f8fafc;color:#1e293b;line-height:1.7}"
        ".hero-seo{background:linear-gradient(135deg,#0f172a,#1e293b);color:#fff;padding:60px 24px;text-align:center}"
        ".hero-seo h1{font-size:clamp(1.8rem,4vw,2.8rem);font-weight:800;margin-bottom:12px}"
        ".hero-seo p{color:#94a3b8;font-size:1rem;max-width:600px;margin:0 auto}"
        ".hero-seo .count{display:inline-block;background:rgba(124,58,237,.2);color:#a78bfa;padding:6px 14px;border-radius:50px;font-size:.82rem;font-weight:700;margin-bottom:16px}"
        ".wrap{max-width:800px;margin:0 auto;padding:32px 24px}"
        ".biz-card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:24px;margin-bottom:16px;display:flex;gap:20px;align-items:flex-start;transition:transform .2s,box-shadow .2s}"
        ".biz-card:hover{transform:translateY(-3px);box-shadow:0 12px 30px rgba(15,23,42,.08)}"
        ".rank{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#a78bfa);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.9rem;flex-shrink:0}"
        ".biz-info{flex:1}"
        ".biz-info h3{font-size:1.1rem;font-weight:700;margin-bottom:6px}"
        ".meta{display:flex;gap:10px;align-items:center;margin-bottom:6px}"
        ".stars{color:#f59e0b;font-weight:700;font-size:.9rem}"
        ".rev{color:#64748b;font-size:.82rem}"
        ".addr{color:#64748b;font-size:.85rem;margin-bottom:10px}"
        ".biz-actions{display:flex;gap:8px;flex-wrap:wrap}"
        ".call-btn,.visit-btn{display:inline-flex;align-items:center;gap:4px;padding:8px 14px;border-radius:8px;font-size:.8rem;font-weight:700;text-decoration:none;transition:transform .2s}"
        ".call-btn{background:#059669;color:#fff}.call-btn:hover{transform:translateY(-1px)}"
        ".visit-btn{background:#7c3aed;color:#fff}.visit-btn:hover{transform:translateY(-1px)}"
        ".footer-seo{text-align:center;padding:32px 24px;font-size:.8rem;color:#94a3b8;border-top:1px solid #e2e8f0}"
        ".footer-seo a{color:#7c3aed}"
        ".seo-text{max-width:800px;margin:24px auto;padding:0 24px;color:#64748b;font-size:.92rem;line-height:1.9}"
        ".seo-text h2{color:#1e293b;font-size:1.3rem;font-weight:700;margin:24px 0 8px}"
        "@media(max-width:640px){.biz-card{flex-direction:column;gap:12px}.rank{align-self:flex-start}}"
        '</style></head><body>'
        f'<section class="hero-seo"><div class="count">{len(businesses)} businesses found</div>'
        f'<h1>{title}</h1>'
        f'<p>{desc}</p></section>'
        f'<div class="wrap">{cards}</div>'
        f'<div class="seo-text">'
        f'<h2>About {category.title()} in {city.title()}</h2>'
        f'<p>Looking for the best {category} in {city.title()}? We have curated a list of top-rated {category} businesses based on Google ratings, customer reviews, and service quality. '
        f'Whether you need a {category} near you or want to compare options, our directory helps you find the perfect match in {city.title()}.</p>'
        f'<h2>How We Rank</h2>'
        f'<p>Businesses are ranked by their Google rating, number of reviews, and overall reputation. We verify all listings and only feature businesses with real customer feedback.</p>'
        '</div>'
        '<div class="footer-seo">Powered by <a href="https://city-maps.online">City Maps</a> | Free business listings for local businesses</div>'
        '</body></html>'
    )
    return HTMLResponse(content=html)


@router.get("/near-me/{category}", response_class=HTMLResponse)
def near_me_page(category: str):
    """Generic near-me page for a category."""
    db = get_supabase()

    all_leads = db.table("leads").select("*").ilike("category", f"%{category}%").order("rating", desc=True).limit(12).execute()
    businesses = all_leads.data or []

    cards = ""
    for i, biz in enumerate(businesses, 1):
        name = biz.get("business_name", "")
        rating = biz.get("rating", "N/A")
        address = biz.get("address", "")[:60]
        phone = biz.get("phone", "")
        call_link = f'<a href="tel:{phone}" style="color:#059669;font-weight:700;font-size:.82rem;text-decoration:none">Call</a>' if phone else ""
        cards += f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;display:flex;justify-content:space-between;align-items:center"><div><strong>{name}</strong><br><span style="font-size:.8rem;color:#64748b">{address}</span></div><div style="text-align:right"><span style="color:#f59e0b;font-weight:700">{rating}★</span><br>{call_link}</div></div>'

    title = f"Best {category.title()} Near Me"

    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>{title} | City Maps</title>'
        '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">'
        "<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Plus Jakarta Sans',sans-serif;background:#f8fafc;color:#1e293b}</style>"
        '</head><body>'
        f'<div style="background:#0f172a;color:#fff;padding:48px 24px;text-align:center"><h1 style="font-size:2rem;font-weight:800">{title}</h1><p style="color:#94a3b8;margin-top:8px">Top rated {category} businesses near your location</p></div>'
        f'<div style="max-width:700px;margin:24px auto;padding:0 16px;display:flex;flex-direction:column;gap:12px">{cards}</div>'
        '<div style="text-align:center;padding:24px;font-size:.8rem;color:#94a3b8">Powered by <a href="https://city-maps.online" style="color:#7c3aed">City Maps</a></div>'
        '</body></html>'
    )
    return HTMLResponse(content=html)
