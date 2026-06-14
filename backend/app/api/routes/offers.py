"""Offer Section Creator - Business owners create and share offers/ads."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/offers", tags=["offers"])


class OfferCreate(BaseModel):
    title: str
    description: str
    image_url: str
    cta_text: str = "Grab This Offer"
    valid_till: str = ""
    discount: str = ""


@router.get("/{website_id}", response_class=HTMLResponse)
def offer_creator_page(website_id: str):
    """Offer creator UI for business owners."""
    from app.services.website_service import WebsiteService
    from app.services.lead_service import LeadService

    ws = WebsiteService()
    ls = LeadService()
    website = ws.get(website_id)
    if not website:
        return HTMLResponse("<h1>Not found</h1>", status_code=404)

    lead = ls.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""
    slug = website.get("slug", "")

    html = f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Create Offer - {business_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#f8fafc;color:#1e293b;padding:16px;max-width:500px;margin:0 auto}}
h1{{font-size:1.2rem;font-weight:800;text-align:center;margin-bottom:4px}}
.sub{{text-align:center;font-size:.75rem;color:#64748b;margin-bottom:20px}}
.form-group{{margin-bottom:14px}}
label{{display:block;font-size:.72rem;font-weight:600;color:#475569;margin-bottom:4px}}
input,textarea{{width:100%;padding:10px 12px;border:1px solid #e2e8f0;border-radius:10px;font-size:.82rem;outline:none;font-family:inherit;transition:border .2s}}
input:focus,textarea:focus{{border-color:#6366f1}}
textarea{{resize:vertical;min-height:80px}}
.preview{{margin:16px 0;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0;background:#fff}}
.preview-img{{width:100%;height:180px;object-fit:cover;background:#f1f5f9;display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:.8rem}}
.preview-img img{{width:100%;height:100%;object-fit:cover}}
.preview-body{{padding:14px}}
.preview-body h2{{font-size:1rem;font-weight:800;margin-bottom:4px}}
.preview-body p{{font-size:.78rem;color:#64748b;line-height:1.5;margin-bottom:8px}}
.preview-body .discount{{display:inline-block;background:#ef4444;color:#fff;font-size:.7rem;font-weight:700;padding:3px 10px;border-radius:50px;margin-bottom:8px}}
.preview-body .valid{{font-size:.65rem;color:#94a3b8}}
.btn{{display:block;width:100%;padding:12px;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer;text-align:center;transition:all .2s}}
.btn-primary{{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;box-shadow:0 4px 14px rgba(99,102,241,.25);margin-bottom:8px}}
.btn-primary:hover{{transform:translateY(-1px);box-shadow:0 6px 20px rgba(99,102,241,.35)}}
.btn-wa{{background:#25D366;color:#fff;margin-bottom:8px}}
.btn-copy{{background:#f1f5f9;color:#475569}}
.share-section{{margin-top:16px;padding:14px;background:#fff;border-radius:12px;border:1px solid #e2e8f0}}
.share-section h3{{font-size:.8rem;font-weight:700;margin-bottom:10px}}
.share-btns{{display:flex;gap:8px;flex-wrap:wrap}}
.share-btns a,.share-btns button{{flex:1;min-width:100px;padding:10px;border-radius:8px;font-size:.72rem;font-weight:600;text-align:center;border:none;cursor:pointer;text-decoration:none}}
.success{{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px;text-align:center;font-size:.8rem;color:#16a34a;font-weight:600;margin-top:12px;display:none}}
</style></head><body>
<h1>Create Offer</h1>
<p class="sub">{business_name}</p>

<div class="form-group">
<label>Offer Title</label>
<input id="ofTitle" placeholder="e.g., 50% OFF on all services this weekend!" oninput="updatePreview()">
</div>

<div class="form-group">
<label>Description</label>
<textarea id="ofDesc" placeholder="Describe your offer details, terms, etc." oninput="updatePreview()"></textarea>
</div>

<div class="form-group">
<label>Image URL (upload to Google Drive/Imgur and paste link)</label>
<input id="ofImg" placeholder="https://drive.google.com/... or https://i.imgur.com/..." oninput="updatePreview()">
</div>

<div class="form-group">
<label>Discount Badge (optional)</label>
<input id="ofDiscount" placeholder="e.g., 50% OFF, Buy 1 Get 1, etc." oninput="updatePreview()">
</div>

<div class="form-group">
<label>Valid Till (optional)</label>
<input id="ofValid" type="text" placeholder="e.g., 30 June 2026" oninput="updatePreview()">
</div>

<h3 style="font-size:.8rem;font-weight:700;margin:16px 0 8px;color:#475569">Live Preview</h3>
<div class="preview">
<div class="preview-img" id="previewImg"><span>Image preview will appear here</span></div>
<div class="preview-body">
<div class="discount" id="previewDiscount" style="display:none"></div>
<h2 id="previewTitle">Your Offer Title</h2>
<p id="previewDesc">Offer description will show here</p>
<p class="valid" id="previewValid"></p>
</div>
</div>

<div class="share-section">
<h3>Share This Offer</h3>
<div class="share-btns">
<a id="shareWa" href="#" target="_blank" class="btn-wa" style="color:#fff">WhatsApp Broadcast</a>
<button onclick="copyLink()" class="btn-copy">Copy Link</button>
</div>
<div class="share-btns" style="margin-top:8px">
<a id="shareFb" href="#" target="_blank" style="background:#1877F2;color:#fff">Facebook</a>
<a id="shareInsta" href="#" target="_blank" style="background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);color:#fff">Instagram</a>
</div>
</div>

<div class="success" id="successMsg">Offer saved & ready to share!</div>

<div style="margin-top:16px">
<button class="btn btn-primary" onclick="saveOffer()">Save & Publish Offer</button>
</div>

<script>
var wid = "{website_id}";
var slug = "{slug}";
var bizName = "{business_name}";
var phone = "{phone}";

function updatePreview() {{
    var title = document.getElementById("ofTitle").value || "Your Offer Title";
    var desc = document.getElementById("ofDesc").value || "Offer description";
    var img = document.getElementById("ofImg").value;
    var discount = document.getElementById("ofDiscount").value;
    var valid = document.getElementById("ofValid").value;

    document.getElementById("previewTitle").textContent = title;
    document.getElementById("previewDesc").textContent = desc;

    if (img) {{
        document.getElementById("previewImg").innerHTML = "<img src='" + img + "' onerror=\\"this.parentElement.innerHTML='<span>Image failed to load</span>'\\">";
    }} else {{
        document.getElementById("previewImg").innerHTML = "<span>Image preview</span>";
    }}

    if (discount) {{
        document.getElementById("previewDiscount").style.display = "inline-block";
        document.getElementById("previewDiscount").textContent = discount;
    }} else {{
        document.getElementById("previewDiscount").style.display = "none";
    }}

    document.getElementById("previewValid").textContent = valid ? "Valid till: " + valid : "";

    // Update share links
    var offerUrl = "https://" + slug + ".city-maps.online/offers";
    var waMsg = encodeURIComponent("*" + bizName + " - Special Offer!*\\n\\n" + title + "\\n" + desc + (discount ? "\\n\\n" + discount : "") + (valid ? "\\nValid till: " + valid : "") + "\\n\\nVisit: " + offerUrl);
    document.getElementById("shareWa").href = "https://wa.me/?text=" + waMsg;
    document.getElementById("shareFb").href = "https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent(offerUrl);
    document.getElementById("shareInsta").href = "https://www.instagram.com/";
}}

function copyLink() {{
    var offerUrl = "https://" + slug + ".city-maps.online";
    navigator.clipboard.writeText(offerUrl + " - " + document.getElementById("ofTitle").value);
    alert("Copied!");
}}

async function saveOffer() {{
    var data = {{
        title: document.getElementById("ofTitle").value,
        description: document.getElementById("ofDesc").value,
        image_url: document.getElementById("ofImg").value,
        discount: document.getElementById("ofDiscount").value,
        valid_till: document.getElementById("ofValid").value,
        cta_text: "Grab This Offer"
    }};
    try {{
        var resp = await fetch("/api/offers/" + wid + "/save", {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify(data)
        }});
        if (resp.ok) {{
            document.getElementById("successMsg").style.display = "block";
            setTimeout(function() {{ document.getElementById("successMsg").style.display = "none"; }}, 3000);
        }}
    }} catch(e) {{
        alert("Failed to save");
    }}
}}

updatePreview();
</script>
</body></html>'''
    return HTMLResponse(content=html)


@router.post("/{website_id}/save")
async def save_offer(website_id: str, offer: OfferCreate):
    """Save an offer for a business website."""
    from app.core.supabase import get_supabase
    db = get_supabase()

    offer_data = {
        "website_id": website_id,
        "title": offer.title,
        "description": offer.description,
        "image_url": offer.image_url,
        "cta_text": offer.cta_text,
        "valid_till": offer.valid_till,
        "discount": offer.discount,
        "active": True,
    }

    # Store in website content as offers array
    from app.services.website_service import WebsiteService
    ws = WebsiteService()
    website = ws.get(website_id)
    if website:
        content = website.get("content", {})
        if isinstance(content, dict):
            offers = content.get("offers", [])
            offers.append(offer_data)
            content["offers"] = offers
            db.table("websites").update({"content": content}).eq("id", website_id).execute()

    return {"status": "saved", "offer": offer_data}


@router.get("/{website_id}/list")
async def list_offers(website_id: str):
    """List all offers for a website."""
    from app.services.website_service import WebsiteService
    ws = WebsiteService()
    website = ws.get(website_id)
    if not website:
        return {"offers": []}
    content = website.get("content", {})
    if isinstance(content, dict):
        return {"offers": content.get("offers", [])}
    return {"offers": []}