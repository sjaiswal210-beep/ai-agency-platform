"""Ad Manager - Simple MVP for City Maps monetization."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/ads", tags=["ads"])


class AdCampaign(BaseModel):
    name: str
    advertiser_name: str
    creative_url: str  # image URL
    destination_url: str  # click target
    ad_format: str = "banner"  # banner, sticky_footer, in_content
    targeting_type: str = "all"  # all, area, category, website
    targeting_value: str = ""  # city name, category, or website_id
    pricing_model: str = "cpm"  # cpm or cpc
    rate: float = 10.0  # Rs per 1000 impressions or per click
    budget: float = 1000.0
    active: bool = False
    start_date: str = ""
    end_date: str = ""


@router.get("/manage", response_class=HTMLResponse)
def ad_manager_page(pwd: str = ""):
    if pwd != "kalpdev2024":
        return HTMLResponse("<html><body style=\"font-family:sans-serif;background:#0f172a;display:flex;align-items:center;justify-content:center;min-height:100vh;color:#fff\"><form style=\"background:#1e293b;padding:32px;border-radius:16px;width:300px;text-align:center\" onsubmit=\"event.preventDefault();location.href=\x27/api/ads/manage?pwd=\x27+document.getElementById(\x27p\x27).value\"><h2 style=\"margin-bottom:16px\">Ad Manager</h2><input id=\"p\" type=\"password\" placeholder=\"Password\" style=\"width:100%;padding:12px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#fff;margin-bottom:12px\"><button style=\"width:100%;padding:12px;background:#00e5ff;color:#000;border:none;border-radius:8px;font-weight:700;cursor:pointer\">Login</button></form></body></html>")
    """Ad Manager dashboard - create, manage, toggle campaigns."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    
    # Get all campaigns
    try:
        campaigns = db.table("ad_campaigns").select("*").order("created_at", desc=True).execute().data or []
    except Exception:
        campaigns = []
    
    # Get stats
    try:
        total_impressions = db.table("analytics_events").select("*", count="exact").eq("event_type", "ad_impression").execute().count or 0
        total_clicks = db.table("analytics_events").select("*", count="exact").eq("event_type", "ad_click").execute().count or 0
    except Exception:
        total_impressions = 0
        total_clicks = 0

    campaign_rows = ""
    for c in campaigns:
        status_color = "#22c55e" if c.get("active") else "#64748b"
        status_text = "Active" if c.get("active") else "Paused"
        campaign_rows += f"""<tr>
        <td style="padding:10px;font-size:.8rem;font-weight:600">{c.get('name','')}</td>
        <td style="padding:10px;font-size:.75rem">{c.get('targeting_type','all')} {': ' + c.get('targeting_value','') if c.get('targeting_value') else ''}</td>
        <td style="padding:10px;font-size:.75rem">{c.get('ad_format','banner')}</td>
        <td style="padding:10px;font-size:.75rem">Rs.{c.get('rate',0)}/{c.get('pricing_model','cpm')}</td>
        <td style="padding:10px"><span style="color:{status_color};font-size:.72rem;font-weight:600">{status_text}</span></td>
        <td style="padding:10px;white-space:nowrap"><button onclick="toggleCampaign('{c.get('id','')}')" style="font-size:.7rem;padding:4px 8px;border-radius:6px;border:1px solid #334155;background:#1e293b;color:#fff;cursor:pointer;margin-right:4px">{'Pause' if c.get('active') else 'Activate'}</button><button onclick="deleteCampaign('{c.get('id','')}')" style="font-size:.7rem;padding:4px 8px;border-radius:6px;border:1px solid #ef4444;background:transparent;color:#ef4444;cursor:pointer">Del</button></td>
        </tr>"""

    html = f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Ad Manager - City Maps</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Inter',sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:1000px;margin:0 auto}}
h1{{font-size:1.3rem;font-weight:800;margin-bottom:4px}}
.sub{{font-size:.75rem;color:#64748b;margin-bottom:24px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}}
.stat-card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;text-align:center}}
.stat-card .n{{font-size:1.5rem;font-weight:800;color:#00e5ff}}.stat-card .l{{font-size:.65rem;color:#64748b;margin-top:4px}}
.section{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;margin-bottom:16px}}
.section h2{{font-size:.85rem;font-weight:700;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse}}th{{text-align:left;padding:10px;font-size:.7rem;color:#64748b;border-bottom:1px solid #334155}}tr:hover{{background:#334155/30}}
.form-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
label{{display:block;font-size:.68rem;font-weight:600;color:#94a3b8;margin-bottom:4px}}
input,select,textarea{{width:100%;padding:9px 12px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#fff;font-size:.78rem;outline:none}}
.btn{{padding:10px 20px;border:none;border-radius:8px;font-weight:700;font-size:.78rem;cursor:pointer}}
.btn-primary{{background:linear-gradient(135deg,#00e5ff,#0ea5e9);color:#020817}}.btn-secondary{{background:#334155;color:#fff}}
</style></head><body>
<h1>Ad Manager</h1>
<p class="sub">Manage advertising across {len(campaigns)} campaign(s) on City Maps network</p>

<div class="stats">
<div class="stat-card"><div class="n">{len(campaigns)}</div><div class="l">Campaigns</div></div>
<div class="stat-card"><div class="n">{len([c for c in campaigns if c.get('active')])}</div><div class="l">Active</div></div>
<div class="stat-card"><div class="n">{total_impressions:,}</div><div class="l">Impressions</div></div>
<div class="stat-card"><div class="n">{total_clicks:,}</div><div class="l">Clicks</div></div>
</div>

<!-- Create Campaign -->
<div class="section">
<h2>Create Campaign</h2>
<form onsubmit="createCampaign(event)">
<div class="form-grid">
<div><label>Campaign Name</label><input id="cName" required placeholder="e.g., Summer Sale Ads"></div>
<div><label>Advertiser</label><input id="cAdvertiser" required placeholder="Business name"></div>
<div><label>Creative Image URL</label><input id="cCreative" required placeholder="https://..."></div>
<div><label>Destination URL (click target)</label><input id="cDest" required placeholder="https://..."></div>
<div><label>Ad Format</label><select id="cFormat"><option value="banner">Banner (top)</option><option value="sticky_footer">Sticky Footer</option><option value="in_content">In-Content</option></select></div>
<div><label>Targeting</label><select id="cTargetType" onchange="document.getElementById('cTargetVal').style.display=this.value==='all'?'none':'block'"><option value="all">All Sites</option><option value="area">By Area/City</option><option value="category">By Category</option><option value="website">Specific Website</option></select></div>
<div><label>Target Value</label><input id="cTargetVal" placeholder="City, category, or website ID" style="display:none"></div>
<div><label>Pricing</label><select id="cPricing"><option value="cpm">CPM (per 1000 views)</option><option value="cpc">CPC (per click)</option></select></div>
<div><label>Rate (Rs.)</label><input id="cRate" type="number" value="10" step="0.5" min="1"></div>
<div><label>Budget (Rs.)</label><input id="cBudget" type="number" value="1000" step="100" min="100"></div>
</div>
<div style="margin-top:12px;display:flex;gap:8px">
<button type="submit" class="btn btn-primary">Create Campaign</button>
</div>
</form>
</div>

<!-- Google AdSense -->
<div class="section">
<h2>Google AdSense</h2>
<p style="font-size:.75rem;color:#64748b;margin-bottom:10px">Enter your AdSense publisher ID to enable Google Ads across all sites.</p>
<div style="display:flex;gap:8px;margin-bottom:8px">
<input id="adsenseId" placeholder="ca-pub-XXXXXXXXXX" style="flex:1">
<button onclick="saveAdsense()" class="btn btn-secondary">Save</button>
</div>
<div style="display:flex;gap:8px">
<input id="adsenseSlot" placeholder="Ad Slot ID (optional)" style="flex:1">
<button onclick="saveAdsenseSlot()" class="btn btn-secondary">Save Slot</button>
</div>
</div>

<!-- Meta/Facebook Pixel -->
<div class="section">
<h2>Meta Pixel (Facebook Ads)</h2>
<p style="font-size:.75rem;color:#64748b;margin-bottom:10px">Enter your Meta Pixel ID to track conversions from Facebook/Instagram ads.</p>
<div style="display:flex;gap:8px">
<input id="metaPixel" placeholder="Pixel ID (e.g., 123456789012345)" style="flex:1">
<button onclick="saveMetaPixel()" class="btn btn-secondary">Save</button>
</div>
</div>

<!-- Campaigns Table -->
<div class="section">
<h2>Campaigns</h2>
<table>
<thead><tr><th>Name</th><th>Targeting</th><th>Format</th><th>Rate</th><th>Status</th><th>Action</th></tr></thead>
<tbody>{campaign_rows}</tbody>
</table>
{('<p style="text-align:center;padding:20px;font-size:.75rem;color:#475569">No campaigns yet</p>' if not campaigns else '')}
</div>

<script>
async function createCampaign(e) {{
    e.preventDefault();
    var data = {{
        name: document.getElementById('cName').value,
        advertiser_name: document.getElementById('cAdvertiser').value,
        creative_url: document.getElementById('cCreative').value,
        destination_url: document.getElementById('cDest').value,
        ad_format: document.getElementById('cFormat').value,
        targeting_type: document.getElementById('cTargetType').value,
        targeting_value: document.getElementById('cTargetVal').value,
        pricing_model: document.getElementById('cPricing').value,
        rate: parseFloat(document.getElementById('cRate').value),
        budget: parseFloat(document.getElementById('cBudget').value),
        active: false
    }};
    var r = await fetch('/api/ads/campaigns', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
    if (r.ok) location.reload();
    else alert('Failed');
}}
async function deleteCampaign(id) {{if(!confirm('Delete?'))return;await fetch('/api/ads/campaigns/'+id,{{method:'DELETE'}});location.reload();}}
async function toggleCampaign(id) {{
    await fetch('/api/ads/campaigns/'+id+'/toggle', {{method:'POST'}});
    location.reload();
}}
async function saveAdsenseSlot() {{
    var id = document.getElementById('adsenseSlot').value;
    await fetch('/api/ads/adsense', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{publisher_id:id}})}});
    alert('Ad Slot saved!');
}}
async function saveMetaPixel() {{
    var id = document.getElementById('metaPixel').value;
    await fetch('/api/ads/meta-pixel', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{pixel_id:id}})}});
    alert('Meta Pixel saved!');
}}
async function saveAdsense() {{
    var id = document.getElementById('adsenseId').value;
    await fetch('/api/ads/adsense', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{publisher_id:id}})}});
    alert('Saved!');
}}
</script>
</body></html>'''
    return HTMLResponse(content=html)


@router.post("/campaigns")
async def create_campaign(campaign: AdCampaign):
    """Create a new ad campaign."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    
    data = campaign.model_dump()
    data["created_at"] = datetime.utcnow().isoformat()
    data["spent"] = 0
    data["impressions"] = 0
    data["clicks"] = 0
    
    result = db.table("ad_campaigns").insert(data).execute()
    return {"status": "created", "campaign": result.data[0] if result.data else data}


@router.post("/campaigns/{campaign_id}/toggle")
async def toggle_campaign(campaign_id: str):
    """Toggle campaign active/paused."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    
    campaign = db.table("ad_campaigns").select("active").eq("id", campaign_id).limit(1).execute()
    if not campaign.data:
        return {"error": "Not found"}
    
    new_status = not campaign.data[0]["active"]
    db.table("ad_campaigns").update({"active": new_status}).eq("id", campaign_id).execute()
    return {"status": "toggled", "active": new_status}


@router.post("/adsense")
async def save_adsense(data: dict):
    """Save Google AdSense publisher ID."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    
    pub_id = data.get("publisher_id", "")
    # Store in a settings table or config
    try:
        existing = db.table("platform_settings").select("id").eq("key", "adsense_publisher_id").limit(1).execute()
        if existing.data:
            db.table("platform_settings").update({"value": pub_id}).eq("key", "adsense_publisher_id").execute()
        else:
            db.table("platform_settings").insert({"key": "adsense_publisher_id", "value": pub_id}).execute()
    except Exception:
        pass
    return {"status": "saved"}


@router.get("/serve")
async def serve_ad(website_id: str = "", category: str = "", area: str = ""):
    """Serve an ad for a website - called by business sites."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    
    try:
        # Get active campaigns that match targeting
        campaigns = db.table("ad_campaigns").select("*").eq("active", True).execute().data or []
        
        matched = []
        for c in campaigns:
            # Skip if budget exhausted
            if c.get("spent", 0) >= c.get("budget", 0):
                continue
            
            t_type = c.get("targeting_type", "all")
            t_value = c.get("targeting_value", "").lower()
            
            if t_type == "all":
                matched.append(c)
            elif t_type == "website" and t_value == website_id:
                matched.append(c)
            elif t_type == "area" and t_value and t_value in area.lower():
                matched.append(c)
            elif t_type == "category" and t_value and t_value in category.lower():
                matched.append(c)
        
        if not matched:
            return {"ad": None}
        
        # Pick highest rate campaign
        matched.sort(key=lambda x: x.get("rate", 0), reverse=True)
        winner = matched[0]
        
        return {
            "ad": {
                "id": winner["id"],
                "creative_url": winner.get("creative_url", ""),
                "destination_url": winner.get("destination_url", ""),
                "format": winner.get("ad_format", "banner"),
                "campaign_name": winner.get("name", ""),
            }
        }
    except Exception as e:
        return {"ad": None, "error": str(e)}


@router.post("/track")
async def track_ad_event(data: dict):
    """Track ad impression or click."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    
    campaign_id = data.get("campaign_id", "")
    event_type = data.get("event_type", "ad_impression")  # ad_impression or ad_click
    website_id = data.get("website_id", "")
    
    if not campaign_id:
        return {"error": "Missing campaign_id"}
    
    # Record event
    db.table("analytics_events").insert({
        "website_id": website_id,
        "event_type": event_type,
        "page": f"/ad/{campaign_id}",
        "referrer": data.get("referrer", ""),
        "created_at": datetime.utcnow().isoformat(),
    }).execute()
    
    # Update campaign stats
    try:
        campaign = db.table("ad_campaigns").select("impressions,clicks,spent,rate,pricing_model").eq("id", campaign_id).limit(1).execute()
        if campaign.data:
            c = campaign.data[0]
            updates = {}
            if event_type == "ad_impression":
                updates["impressions"] = c.get("impressions", 0) + 1
                if c.get("pricing_model") == "cpm":
                    updates["spent"] = round(c.get("spent", 0) + c.get("rate", 0) / 1000, 4)
            elif event_type == "ad_click":
                updates["clicks"] = c.get("clicks", 0) + 1
                if c.get("pricing_model") == "cpc":
                    updates["spent"] = round(c.get("spent", 0) + c.get("rate", 0), 4)
            
            if updates:
                db.table("ad_campaigns").update(updates).eq("id", campaign_id).execute()
    except Exception:
        pass
    
    return {"tracked": True}

@router.get("/adsense-config")
async def get_adsense_config():
    """Get AdSense configuration for ad injection."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        result = db.table("platform_settings").select("value").eq("key", "adsense_publisher_id").limit(1).execute()
        pub_id = result.data[0]["value"] if result.data else ""
        slot_result = db.table("platform_settings").select("value").eq("key", "adsense_ad_slot").limit(1).execute()
        slot_id = slot_result.data[0]["value"] if slot_result.data else ""
        return {"publisher_id": pub_id, "ad_slot_id": slot_id}
    except Exception:
        return {"publisher_id": "", "ad_slot_id": ""}


@router.get("/meta-config")
async def get_meta_config():
    """Get Meta/Facebook Pixel configuration."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        result = db.table("platform_settings").select("value").eq("key", "meta_pixel_id").limit(1).execute()
        pixel_id = result.data[0]["value"] if result.data else ""
        return {"pixel_id": pixel_id}
    except Exception:
        return {"pixel_id": ""}


@router.post("/meta-pixel")
async def save_meta_pixel(data: dict):
    """Save Meta/Facebook Pixel ID."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    pixel_id = data.get("pixel_id", "")
    try:
        existing = db.table("platform_settings").select("id").eq("key", "meta_pixel_id").limit(1).execute()
        if existing.data:
            db.table("platform_settings").update({"value": pixel_id}).eq("key", "meta_pixel_id").execute()
        else:
            db.table("platform_settings").insert({"key": "meta_pixel_id", "value": pixel_id}).execute()
    except Exception:
        pass
    return {"status": "saved"}

@router.get("/campaign/{campaign_id}", response_class=HTMLResponse)
def campaign_details(campaign_id: str):
    """Campaign performance details page - accessible by advertiser."""
    from app.core.supabase import get_supabase
    from datetime import datetime, timedelta
    db = get_supabase()
    
    try:
        campaign = db.table("ad_campaigns").select("*").eq("id", campaign_id).limit(1).execute()
        if not campaign.data:
            return HTMLResponse("<h1>Campaign not found</h1>", status_code=404)
        c = campaign.data[0]
    except Exception as e:
        return HTMLResponse(f"<h1>Error: {e}</h1>", status_code=500)
    
    # Calculate metrics
    impressions = c.get("impressions", 0)
    clicks = c.get("clicks", 0)
    spent = c.get("spent", 0)
    budget = c.get("budget", 0)
    rate = c.get("rate", 0)
    ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0
    remaining = round(budget - spent, 2)
    status = "Active" if c.get("active") else "Paused"
    status_color = "#22c55e" if c.get("active") else "#f59e0b"
    
    # Calculate duration
    created = c.get("created_at", "")
    days_active = "N/A"
    if created:
        try:
            from dateutil import parser
            start = parser.parse(created)
            days_active = (datetime.utcnow() - start.replace(tzinfo=None)).days
        except Exception:
            days_active = "N/A"

    html = f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Campaign: {c.get("name","")} - City Maps Ads</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Inter',sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:800px;margin:0 auto}}
h1{{font-size:1.3rem;font-weight:800;margin-bottom:4px}}
.sub{{font-size:.75rem;color:#64748b;margin-bottom:24px}}
.status{{display:inline-block;padding:4px 12px;border-radius:50px;font-size:.7rem;font-weight:600;color:#fff;background:{status_color};margin-bottom:16px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px}}
.stat{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;text-align:center}}
.stat .n{{font-size:1.5rem;font-weight:800;color:#00e5ff}}.stat .l{{font-size:.65rem;color:#64748b;margin-top:4px}}
.section{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;margin-bottom:16px}}
.section h2{{font-size:.85rem;font-weight:700;margin-bottom:12px}}
.row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #334155;font-size:.78rem}}
.row:last-child{{border:none}}
.row .label{{color:#64748b}}.row .value{{font-weight:600}}
.creative{{max-width:100%;border-radius:8px;margin-top:12px;border:1px solid #334155}}
.progress{{background:#334155;border-radius:8px;height:8px;overflow:hidden;margin-top:8px}}
.progress-bar{{height:100%;background:linear-gradient(90deg,#00e5ff,#7c3aed);border-radius:8px;transition:width .3s}}
</style></head><body>

<h1>{c.get("name","Campaign")}</h1>
<p class="sub">Advertiser: {c.get("advertiser_name","")}</p>
<div class="status">{status}</div>

<div class="stats">
<div class="stat"><div class="n">{impressions:,}</div><div class="l">Impressions</div></div>
<div class="stat"><div class="n">{clicks:,}</div><div class="l">Clicks</div></div>
<div class="stat"><div class="n">{ctr}%</div><div class="l">CTR</div></div>
</div>

<div class="stats">
<div class="stat"><div class="n">Rs.{spent:.2f}</div><div class="l">Spent</div></div>
<div class="stat"><div class="n">Rs.{remaining:.2f}</div><div class="l">Remaining</div></div>
<div class="stat"><div class="n">{days_active}</div><div class="l">Days Active</div></div>
</div>

<!-- Budget Progress -->
<div class="section">
<h2>Budget Usage</h2>
<div class="row"><span class="label">Total Budget</span><span class="value">Rs.{budget:.2f}</span></div>
<div class="row"><span class="label">Amount Spent</span><span class="value">Rs.{spent:.2f}</span></div>
<div class="row"><span class="label">Remaining</span><span class="value">Rs.{remaining:.2f}</span></div>
<div class="progress"><div class="progress-bar" style="width:{min(spent/budget*100,100) if budget > 0 else 0}%"></div></div>
</div>

<!-- Campaign Details -->
<div class="section">
<h2>Campaign Settings</h2>
<div class="row"><span class="label">Pricing Model</span><span class="value">{c.get("pricing_model","").upper()}</span></div>
<div class="row"><span class="label">Rate</span><span class="value">Rs.{rate} per {'1000 impressions' if c.get("pricing_model")=="cpm" else 'click'}</span></div>
<div class="row"><span class="label">Ad Format</span><span class="value">{c.get("ad_format","banner").replace("_"," ").title()}</span></div>
<div class="row"><span class="label">Targeting</span><span class="value">{c.get("targeting_type","all").title()}{": " + c.get("targeting_value","") if c.get("targeting_value") else ""}</span></div>
<div class="row"><span class="label">Created</span><span class="value">{created[:10] if created else "N/A"}</span></div>
</div>

<!-- Creative Preview -->
<div class="section">
<h2>Ad Creative</h2>
<div class="row"><span class="label">Destination URL</span><span class="value" style="word-break:break-all">{c.get("destination_url","")}</span></div>
<img src="{c.get("creative_url","")}" class="creative" alt="Ad creative">
</div>

<p style="text-align:center;margin-top:20px;font-size:.7rem;color:#475569">City Maps Ad Platform &bull; <a href="/api/ads/manage" style="color:#00e5ff">Back to Ad Manager</a></p>
</body></html>'''
    return HTMLResponse(content=html)


@router.get("/portal/{advertiser_name}", response_class=HTMLResponse)
def advertiser_portal(advertiser_name: str):
    """Advertiser portal - view all campaigns for an advertiser."""
    from app.core.supabase import get_supabase
    import urllib.parse
    db = get_supabase()
    
    decoded_name = urllib.parse.unquote(advertiser_name)
    
    try:
        campaigns = db.table("ad_campaigns").select("*").eq("advertiser_name", decoded_name).order("created_at", desc=True).execute().data or []
    except Exception:
        campaigns = []
    
    total_impressions = sum(c.get("impressions", 0) for c in campaigns)
    total_clicks = sum(c.get("clicks", 0) for c in campaigns)
    total_spent = sum(c.get("spent", 0) for c in campaigns)
    total_budget = sum(c.get("budget", 0) for c in campaigns)
    
    campaign_cards = ""
    for c in campaigns:
        ctr = round((c.get("clicks",0) / c.get("impressions",1) * 100), 2) if c.get("impressions",0) > 0 else 0
        status_color = "#22c55e" if c.get("active") else "#64748b"
        campaign_cards += f'''<a href="/api/ads/campaign/{c.get("id","")}" style="display:block;background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;text-decoration:none;color:#fff;transition:all .2s" onmouseover="this.style.borderColor='#00e5ff'" onmouseout="this.style.borderColor='#334155'">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><span style="font-weight:700;font-size:.85rem">{c.get("name","")}</span><span style="color:{status_color};font-size:.7rem;font-weight:600">{"Active" if c.get("active") else "Paused"}</span></div>
        <div style="display:flex;gap:16px;font-size:.72rem;color:#94a3b8"><span>{c.get("impressions",0):,} views</span><span>{c.get("clicks",0)} clicks</span><span>{ctr}% CTR</span><span>Rs.{c.get("spent",0):.2f} spent</span></div>
        </a>'''
    
    html = f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{decoded_name} - Advertiser Portal</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Inter',sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:800px;margin:0 auto}}
h1{{font-size:1.3rem;font-weight:800;margin-bottom:4px}}
.sub{{font-size:.75rem;color:#64748b;margin-bottom:24px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}}
.stat{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:14px;text-align:center}}
.stat .n{{font-size:1.3rem;font-weight:800;color:#00e5ff}}.stat .l{{font-size:.6rem;color:#64748b;margin-top:4px}}
.campaigns{{display:flex;flex-direction:column;gap:10px}}
</style></head><body>

<h1>Advertiser Portal</h1>
<p class="sub">{decoded_name} &bull; {len(campaigns)} campaign(s)</p>

<div class="stats">
<div class="stat"><div class="n">{total_impressions:,}</div><div class="l">Total Views</div></div>
<div class="stat"><div class="n">{total_clicks:,}</div><div class="l">Total Clicks</div></div>
<div class="stat"><div class="n">Rs.{total_spent:.2f}</div><div class="l">Total Spent</div></div>
<div class="stat"><div class="n">Rs.{total_budget:.2f}</div><div class="l">Total Budget</div></div>
</div>

<h2 style="font-size:.85rem;font-weight:700;margin-bottom:12px">Your Campaigns</h2>
<div class="campaigns">
{campaign_cards}
{('<p style="text-align:center;padding:20px;font-size:.75rem;color:#475569">No campaigns yet</p>' if not campaigns else '')}
</div>

<p style="text-align:center;margin-top:24px;font-size:.7rem;color:#475569">City Maps Ad Platform</p>
</body></html>'''
    return HTMLResponse(content=html)

@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    db.table("ad_campaigns").delete().eq("id", campaign_id).execute()
    return {"status": "deleted"}


@router.get("/analytics", response_class=HTMLResponse)
def ads_analytics(pwd: str = ""):
    """Analytics dashboard."""
    if pwd != "kalpdev2024":
        return HTMLResponse("<script>location.href='/api/ads/manage'</script>")
    from app.core.supabase import get_supabase
    db = get_supabase()
    campaigns = db.table("ad_campaigns").select("*").execute().data or []
    ti = sum(c.get("impressions", 0) for c in campaigns)
    tc = sum(c.get("clicks", 0) for c in campaigns)
    tr = sum(c.get("spent", 0) for c in campaigns)
    try:
        usage = db.table("usage_tracking").select("*").order("created_at", desc=True).limit(50).execute().data or []
    except Exception:
        usage = []
    rc = sum(1 for u in usage if "video" in u.get("service", "").lower())
    gc = sum(1 for u in usage if "gemini" in u.get("service", "").lower())
    html = f"<html><head><meta charset=UTF-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Analytics</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:700px;margin:0 auto}}.g{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0}}.c{{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px;text-align:center}}.n{{font-size:1.3rem;font-weight:800;color:#00e5ff}}.l{{font-size:.6rem;color:#64748b;margin-top:4px}}</style></head><body><h1 style='font-size:1.2rem;margin-bottom:16px'>Analytics</h1><div class=g><div class=c><div class=n>Rs.{tr:.2f}</div><div class=l>Ad Revenue</div></div><div class=c><div class=n>{ti:,}</div><div class=l>Impressions</div></div><div class=c><div class=n>{tc:,}</div><div class=l>Clicks</div></div></div><div class=g><div class=c><div class=n>${rc*0.5:.2f}</div><div class=l>Replicate Cost</div></div><div class=c><div class=n>{rc}</div><div class=l>Videos Made</div></div><div class=c><div class=n>{gc}</div><div class=l>Sites Generated</div></div></div><p style='margin-top:16px;font-size:.7rem;text-align:center'><a href='/api/ads/manage?pwd=kalpdev2024' style='color:#00e5ff'>Back to Ad Manager</a></p></body></html>"
    return HTMLResponse(content=html)