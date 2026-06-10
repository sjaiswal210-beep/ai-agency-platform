from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService

router = APIRouter(prefix="/google-profile", tags=["google-profile"])


@router.get("/{website_id}/setup-guide", response_class=HTMLResponse)
def google_profile_guide(website_id: str):
    """Instructions for the business owner to add their website to Google Business Profile."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    slug = website.get("slug", "")
    site_url = f"https://{slug}.city-maps.online" if slug else ""

    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Add Website to Google - {business_name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:#f8fafc;color:#1e293b;padding:20px;max-width:600px;margin:0 auto}}
h1{{font-size:1.4rem;font-weight:800;margin-bottom:8px}}
.url-box{{background:#ecfdf5;border:2px solid #10b981;border-radius:12px;padding:16px;margin:16px 0;text-align:center}}
.url-box a{{color:#059669;font-weight:700;font-size:1.1rem;word-break:break-all}}
.steps{{margin:20px 0}}
.step{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin-bottom:12px;display:flex;gap:12px;align-items:flex-start}}
.step-num{{width:32px;height:32px;border-radius:50%;background:#7c3aed;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;flex-shrink:0}}
.step-content h3{{font-size:.95rem;font-weight:700;margin-bottom:4px}}
.step-content p{{font-size:.85rem;color:#64748b}}
.cta{{background:#4285f4;color:#fff;padding:14px 24px;border-radius:10px;text-decoration:none;display:inline-block;font-weight:700;margin-top:16px}}
.copy-btn{{background:#f1f5f9;border:1px solid #e2e8f0;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:.85rem;margin-top:8px}}
.note{{background:#fef3c7;border:1px solid #fde68a;border-radius:8px;padding:12px;font-size:.82rem;margin-top:16px}}
</style></head><body>
<h1>Add Your Website to Google Maps</h1>
<p style="color:#64748b;margin-bottom:16px">Hi {business_name}! Your free website is ready. Add it to your Google Business Profile to get more customers.</p>

<div class="url-box">
<p style="font-size:.8rem;color:#64748b;margin-bottom:4px">Your Website URL:</p>
<a href="{site_url}" target="_blank">{site_url}</a>
<br><button class="copy-btn" onclick="navigator.clipboard.writeText('{site_url}');this.textContent='Copied!'">Copy URL</button>
</div>

<div class="steps">
<div class="step"><div class="step-num">1</div><div class="step-content"><h3>Open Google Business Profile</h3><p>Go to <a href="https://business.google.com" target="_blank">business.google.com</a> and sign in with the Google account linked to your business.</p></div></div>
<div class="step"><div class="step-num">2</div><div class="step-content"><h3>Select Your Business</h3><p>Click on your business name "{business_name}" from the list.</p></div></div>
<div class="step"><div class="step-num">3</div><div class="step-content"><h3>Click "Edit Profile"</h3><p>Find the "Edit profile" or "Edit" button on your business info.</p></div></div>
<div class="step"><div class="step-num">4</div><div class="step-content"><h3>Add Website URL</h3><p>Find the "Website" field and paste: <strong>{site_url}</strong></p></div></div>
<div class="step"><div class="step-num">5</div><div class="step-content"><h3>Save Changes</h3><p>Click "Save" and your website will appear on Google Maps within 24 hours!</p></div></div>
</div>

<a href="https://business.google.com" target="_blank" class="cta">Open Google Business Profile &rarr;</a>

<div class="note">
<strong>Don't have a Google Business Profile?</strong> Create one for free at <a href="https://business.google.com/create" target="_blank">business.google.com/create</a>. It helps customers find you on Google Maps and Search.
</div>

<p style="margin-top:20px;font-size:.75rem;color:#94a3b8;text-align:center">Powered by City Maps | Made with care by Kalpdev Digitals</p>
</body></html>'''
    return HTMLResponse(content=html)


@router.get("/{website_id}/whatsapp-message")
def get_google_profile_message(website_id: str):
    """Get a ready WhatsApp message to send to the business owner about adding their website to Google."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""
    slug = website.get("slug", "")
    site_url = f"https://{slug}.city-maps.online" if slug else ""
    guide_url = f"https://city-maps.online/api/google-profile/{website_id}/setup-guide"

    message = f"""Hi {business_name}! 

We've created a FREE professional website for your business:
{site_url}

To get more customers from Google, add this website to your Google Business Profile. Here's a simple guide:
{guide_url}

It takes just 2 minutes and helps customers find you on Google Maps!

- Team City Maps"""

    whatsapp_num = "".join(ch for ch in phone if ch.isdigit())
    import urllib.parse
    wa_url = f"https://wa.me/{whatsapp_num}?text={urllib.parse.quote(message)}" if whatsapp_num else ""

    return {
        "message": message,
        "whatsapp_link": wa_url,
        "guide_url": guide_url,
        "site_url": site_url,
        "business": business_name,
    }
