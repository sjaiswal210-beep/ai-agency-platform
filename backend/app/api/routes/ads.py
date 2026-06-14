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
def ad_manager_page():
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
        <td style="padding:10px"><button onclick="toggleCampaign('{c.get('id','')}')" style="font-size:.7rem;padding:4px 10px;border-radius:6px;border:1px solid #334155;background:#1e293b;color:#fff;cursor:pointer">{'Pause' if c.get('active') else 'Activate'}</button></td>
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
<div style="display:flex;gap:8px">
<input id="adsenseId" placeholder="ca-pub-XXXXXXXXXX" style="flex:1">
<button onclick="saveAdsense()" class="btn btn-secondary">Save</button>
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
async function toggleCampaign(id) {{
    await fetch('/api/ads/campaigns/'+id+'/toggle', {{method:'POST'}});
    location.reload();
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