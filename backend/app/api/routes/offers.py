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
    """Offer creator UI - upload image, build creative, share directly."""
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
    site_url = f"https://{slug}.city-maps.online" if slug else ""

    html = f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Create Offer - {business_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:520px;margin:0 auto;min-height:100vh}}
h1{{font-size:1.1rem;font-weight:800;text-align:center;margin-bottom:4px}}
.sub{{text-align:center;font-size:.72rem;color:#64748b;margin-bottom:20px}}
.form-group{{margin-bottom:12px}}
label{{display:block;font-size:.7rem;font-weight:600;color:#94a3b8;margin-bottom:4px}}
input,textarea,select{{width:100%;padding:10px 12px;border:1px solid #334155;border-radius:10px;font-size:.8rem;outline:none;font-family:inherit;background:#1e293b;color:#fff;transition:border .2s}}
input:focus,textarea:focus{{border-color:#6366f1}}
textarea{{resize:vertical;min-height:70px}}
.upload-area{{border:2px dashed #334155;border-radius:12px;padding:24px;text-align:center;cursor:pointer;transition:all .2s;margin-bottom:12px}}
.upload-area:hover{{border-color:#6366f1;background:rgba(99,102,241,.05)}}
.upload-area p{{font-size:.75rem;color:#64748b}}
.upload-area .icon{{font-size:1.5rem;margin-bottom:6px}}

/* Creative Preview */
.creative-wrap{{margin:16px 0;border-radius:14px;overflow:hidden;box-shadow:0 12px 40px rgba(0,0,0,.4)}}
.creative{{position:relative;width:100%;aspect-ratio:1;background:#1e293b;overflow:hidden;display:flex;align-items:flex-end}}
.creative .bg-img{{position:absolute;inset:0;object-fit:cover;width:100%;height:100%}}
.creative .overlay{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.1) 0%,rgba(0,0,0,.7) 100%)}}
.creative .content{{position:relative;z-index:2;padding:24px;width:100%}}
.creative .brand{{position:absolute;top:16px;left:16px;z-index:2;background:rgba(255,255,255,.95);padding:6px 14px;border-radius:50px;font-weight:800;font-size:.75rem;color:#6366f1}}
.creative .badge{{position:absolute;top:16px;right:16px;z-index:2;background:#ef4444;color:#fff;padding:5px 12px;border-radius:50px;font-size:.68rem;font-weight:700}}
.creative h2{{color:#fff;font-size:1.4rem;font-weight:800;margin-bottom:8px;text-shadow:0 2px 8px rgba(0,0,0,.5)}}
.creative p{{color:rgba(255,255,255,.85);font-size:.82rem;margin-bottom:10px}}
.creative .cta-bar{{display:flex;justify-content:space-between;align-items:center;margin-top:8px}}
.creative .cta-btn{{background:#fff;color:#6366f1;padding:8px 16px;border-radius:50px;font-weight:700;font-size:.72rem}}
.creative .url{{color:rgba(255,255,255,.7);font-size:.68rem}}

/* Buttons */
.btn-row{{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}}
.btn{{flex:1;min-width:100px;padding:12px;border:none;border-radius:10px;font-weight:700;font-size:.78rem;cursor:pointer;text-align:center;transition:all .2s;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:6px}}
.btn-save{{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff}}
.btn-wa{{background:#25D366;color:#fff}}
.btn-dl{{background:#334155;color:#fff}}
.btn-fb{{background:#1877F2;color:#fff}}
.btn:hover{{transform:translateY(-1px);opacity:.9}}
.toast{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#22c55e;color:#fff;padding:10px 20px;border-radius:50px;font-size:.78rem;font-weight:600;display:none;z-index:99}}
</style></head><body>
<h1>Create Offer</h1>
<p class="sub">{business_name}</p>

<!-- Upload Image -->
<div class="upload-area" onclick="document.getElementById('fileInput').click()" id="uploadArea">
<div class="icon">&#128247;</div>
<p>Tap to upload image from gallery/camera</p>
<p style="font-size:.65rem;color:#475569;margin-top:4px">JPG, PNG supported</p>
</div>
<input type="file" id="fileInput" accept="image/*" style="display:none" onchange="handleUpload(event)">

<div class="form-group">
<label>Offer Title</label>
<input id="ofTitle" placeholder="e.g., 50% OFF this weekend!" oninput="updateCreative()">
</div>

<div class="form-group">
<label>Description</label>
<textarea id="ofDesc" placeholder="Offer details..." oninput="updateCreative()"></textarea>
</div>

<div style="display:flex;gap:8px">
<div class="form-group" style="flex:1">
<label>Discount Badge</label>
<input id="ofDiscount" placeholder="50% OFF" oninput="updateCreative()">
</div>
<div class="form-group" style="flex:1">
<label>Valid Till</label>
<input id="ofValid" placeholder="30 June" oninput="updateCreative()">
</div>
</div>

<!-- Creative Preview -->
<p style="font-size:.7rem;font-weight:600;color:#64748b;margin-bottom:6px">LIVE PREVIEW</p>
<div class="creative-wrap">
<div class="creative" id="creativeCard">
<img class="bg-img" id="creativeBg" src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&h=600&fit=crop">
<div class="overlay"></div>
<div class="brand">{business_name}</div>
<div class="badge" id="creativeBadge" style="display:none"></div>
<div class="content">
<h2 id="creativeTitle">Your Offer Title</h2>
<p id="creativeDesc">Offer details appear here</p>
<div class="cta-bar">
<span class="cta-btn">Visit Now</span>
<span class="url">{slug}.city-maps.online</span>
</div>
</div>
</div>
</div>

<!-- Action Buttons -->
<div class="btn-row">
<button class="btn btn-dl" onclick="downloadCreative()">&#11015; Download</button>
<button class="btn btn-wa" onclick="shareWhatsApp()">&#128172; WhatsApp</button>
</div>
<div class="btn-row">
<button class="btn btn-fb" onclick="shareFacebook()">&#128077; Facebook</button>
<button class="btn btn-save" onclick="saveOffer()">&#10003; Save Offer</button>
</div>

<div class="toast" id="toast">Saved!</div>

<script>
var siteUrl = "{site_url}";
var bizName = "{business_name}";
var slug = "{slug}";

function handleUpload(e) {{
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(ev) {{
        document.getElementById('creativeBg').src = ev.target.result;
        document.getElementById('uploadArea').innerHTML = '<div class="icon">&#10003;</div><p style="color:#22c55e">Image uploaded! Tap to change</p>';
    }};
    reader.readAsDataURL(file);
}}

function updateCreative() {{
    var title = document.getElementById('ofTitle').value || 'Your Offer Title';
    var desc = document.getElementById('ofDesc').value || 'Offer details appear here';
    var discount = document.getElementById('ofDiscount').value;
    document.getElementById('creativeTitle').textContent = title;
    document.getElementById('creativeDesc').textContent = desc;
    if (discount) {{
        document.getElementById('creativeBadge').style.display = 'block';
        document.getElementById('creativeBadge').textContent = discount;
    }} else {{
        document.getElementById('creativeBadge').style.display = 'none';
    }}
}}

function downloadCreative() {{
    html2canvas(document.getElementById('creativeCard'), {{useCORS:true, scale:2, allowTaint:true}}).then(function(canvas) {{
        var a = document.createElement('a');
        a.download = bizName.replace(/\\s/g,'-') + '-offer.png';
        a.href = canvas.toDataURL('image/png');
        a.click();
    }});
}}

function shareWhatsApp() {{
    var title = document.getElementById('ofTitle').value || 'Special Offer';
    var desc = document.getElementById('ofDesc').value || '';
    var discount = document.getElementById('ofDiscount').value || '';
    var msg = '*' + bizName + ' - ' + title + '*';
    if (desc) msg += '\\n' + desc;
    if (discount) msg += '\\n\\n' + discount;
    msg += '\\n\\nVisit: ' + siteUrl;
    window.open('https://wa.me/?text=' + encodeURIComponent(msg), '_blank');
}}

function shareFacebook() {{
    window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(siteUrl) + '&quote=' + encodeURIComponent(document.getElementById('ofTitle').value || bizName + ' Offer'), '_blank');
}}

function saveOffer() {{
    var data = {{
        title: document.getElementById('ofTitle').value,
        description: document.getElementById('ofDesc').value,
        discount: document.getElementById('ofDiscount').value,
        valid_till: document.getElementById('ofValid').value,
        date: new Date().toISOString()
    }};
    var saved = JSON.parse(localStorage.getItem('offers_' + slug) || '[]');
    saved.unshift(data);
    if (saved.length > 20) saved = saved.slice(0, 20);
    localStorage.setItem('offers_' + slug, JSON.stringify(saved));
    document.getElementById('toast').style.display = 'block';
    setTimeout(function() {{ document.getElementById('toast').style.display = 'none'; }}, 2500);
}}
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