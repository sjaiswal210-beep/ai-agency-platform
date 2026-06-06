from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
import urllib.parse

router = APIRouter(prefix="/qr", tags=["qr"])


@router.get("/{website_id}", response_class=HTMLResponse)
def get_qr_page(website_id: str):
    """Generate a QR code page for a website (uses Google Charts API)."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    slug = website.get("slug", "")
    site_url = f"https://city-maps.online/{slug}" if slug else f"https://city-maps.online/api/preview/{website_id}"

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={urllib.parse.quote(site_url)}"

    html = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>QR Code - {business_name}</title>'
        '<style>'
        "*{margin:0;padding:0;box-sizing:border-box}"
        "body{font-family:system-ui,sans-serif;background:#0f172a;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center}"
        ".card{background:#fff;border-radius:24px;padding:40px;text-align:center;max-width:420px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,.3)}"
        ".card h2{color:#1e293b;font-size:1.3rem;margin-bottom:8px}"
        ".card p{color:#64748b;font-size:.9rem;margin-bottom:24px}"
        ".qr{border-radius:12px;margin-bottom:20px}"
        ".url{background:#f1f5f9;border-radius:8px;padding:10px;font-size:.8rem;color:#475569;word-break:break-all;margin-bottom:16px}"
        ".dl{display:inline-block;background:#7c3aed;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:700;font-size:.9rem}"
        ".dl:hover{background:#6d28d9}"
        ".brand{margin-top:20px;font-size:.75rem;color:#94a3b8}"
        '</style></head><body>'
        '<div class="card">'
        f'<h2>{business_name}</h2>'
        '<p>Scan to visit website</p>'
        f'<img src="{qr_url}" alt="QR Code" class="qr" width="280" height="280">'
        f'<div class="url">{site_url}</div>'
        f'<a href="{qr_url}" download="qr-{slug or website_id}.png" class="dl">Download QR</a>'
        '<p class="brand">Powered by City Maps</p>'
        '</div></body></html>'
    )
    return HTMLResponse(content=html)


@router.get("/{website_id}/image")
def get_qr_image_url(website_id: str):
    """Get just the QR code image URL."""
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    slug = website.get("slug", "")
    site_url = f"https://city-maps.online/{slug}" if slug else f"https://city-maps.online/api/preview/{website_id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={urllib.parse.quote(site_url)}"

    return {"website_id": website_id, "website_url": site_url, "qr_image_url": qr_url}
