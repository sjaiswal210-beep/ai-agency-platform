from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import Response
from app.core.supabase import get_supabase

router = APIRouter(tags=["sitemap"])


@router.get("/sitemap.xml")
def sitemap():
    """Generate XML sitemap with all published website slugs."""
    db = get_supabase()
    try:
        result = db.table("websites").select("slug").not_.is_("slug", "null").execute()
        slugs = [r["slug"] for r in (result.data or []) if r.get("slug")]
    except Exception:
        slugs = []

    base = "https://city-maps.online"
    urls = [f'<url><loc>{base}/{slug}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>' for slug in slugs]

    # Add SEO pages
    categories = ["salon", "dentist", "restaurant", "gym", "clinic", "hotel", "cafe", "store", "photographer", "solar"]
    cities = ["pune", "mumbai", "bangalore", "delhi", "hyderabad", "chennai"]
    for cat in categories:
        urls.append(f'<url><loc>{base}/api/seo-pages/near-me/{cat}</loc><changefreq>daily</changefreq><priority>0.7</priority></url>')
        for city in cities:
            urls.append(f'<url><loc>{base}/api/seo-pages/best-{cat}-in-{city}</loc><changefreq>daily</changefreq><priority>0.9</priority></url>')

    xml = '<?xml version="1.0" encoding="UTF-8"?>'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    xml += f'<url><loc>{base}</loc><changefreq>daily</changefreq><priority>1.0</priority></url>'
    xml += "".join(urls)
    xml += '</urlset>'

    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt")
def robots():
    """Serve robots.txt for SEO."""
    content = """User-agent: *
Allow: /
Allow: /api/seo-pages/
Allow: /api/preview/by-slug/

Disallow: /api/leads/
Disallow: /api/dashboard/
Disallow: /api/editor/
Disallow: /api/outreach/

Sitemap: https://city-maps.online/sitemap.xml
"""
    return Response(content=content.strip(), media_type="text/plain")
