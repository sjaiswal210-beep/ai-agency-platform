from app.api.routes.preview import generate_html
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService

ws = WebsiteService()
ls = LeadService()
website = ws.get("a44416cd-7a12-42b5-a864-647861d3c1e1")
if website:
    lead = ls.get(website["lead_id"])
    content = website.get("content", {})
    print(f"Content keys: {list(content.keys())[:5]}")
    try:
        html = generate_html(content, website.get("template", "store"), lead)
        print(f"HTML generated: {len(html)} chars")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Website not found")
