"""QA Review API routes."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/qa", tags=["qa-review"])


@router.post("/review/{website_id}")
async def trigger_review(website_id: str):
    """Trigger QA review for a specific website."""
    from app.agents.qa_review.agent import review_website
    result = await review_website(website_id)
    return result


@router.get("/review/{website_id}")
async def get_review(website_id: str):
    """Get QA review results for a website."""
    from app.core.supabase import get_supabase
    from app.services.website_service import WebsiteService
    
    db = get_supabase()
    
    # Try qa_reviews table first
    try:
        result = db.table("qa_reviews").select("*").eq("website_id", website_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    
    # Fallback to content._qa_review
    ws = WebsiteService()
    website = ws.get(website_id)
    if website and isinstance(website.get("content"), dict):
        review = website["content"].get("_qa_review")
        if review:
            return review
    
    return {"error": "No review found", "website_id": website_id}


@router.get("/review-all")
async def review_all(limit: int = 5):
    """Review recent websites that haven't been reviewed."""
    from app.agents.qa_review.agent import review_all_recent
    results = await review_all_recent(limit)
    return {"reviewed": len(results), "results": results}


@router.get("/lead/{lead_id}")
async def get_review_for_lead(lead_id: str):
    """Get QA review for a lead's website."""
    from app.core.supabase import get_supabase
    from app.services.website_service import WebsiteService
    
    db = get_supabase()
    ws = WebsiteService()
    
    websites = ws.get_by_lead(lead_id)
    if not websites:
        return {"error": "No website found for this lead"}
    
    website_id = websites[0]["id"]
    
    # Try qa_reviews table
    try:
        result = db.table("qa_reviews").select("*").eq("website_id", website_id).limit(1).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    
    # Check content
    website = ws.get(website_id)
    if website and isinstance(website.get("content"), dict):
        review = website["content"].get("_qa_review")
        if review:
            return review
    
    # No review yet - trigger one
    from app.agents.qa_review.agent import review_website
    result = await review_website(website_id)
    return result

@router.get("/dashboard", response_class=HTMLResponse)
async def qa_dashboard():
    """QA Dashboard with summary, scores, and auto-fix."""
    from app.core.supabase import get_supabase
    from app.services.lead_service import LeadService
    db = get_supabase()
    ls = LeadService()

    sites = db.table("websites").select("id,slug,lead_id,content").not_.is_("slug", "null").order("created_at", desc=True).limit(50).execute().data or []
    
    total_score = 0
    reviewed_count = 0
    issues_count = 0
    rows = ""
    
    for site in sites:
        content = site.get("content", {}) or {}
        review = content.get("_qa_review", {}) if isinstance(content, dict) else {}
        lead = ls.get(site["lead_id"]) if site.get("lead_id") else None
        name = lead.get("business_name", "Unknown")[:25] if lead else "Unknown"
        slug = site.get("slug", "")
        score = review.get("overall_score", 0) if review else 0
        issues = review.get("issues", []) if review else []
        top_issue = issues[0].get("detail", "")[:50] if issues else "No issues"
        
        if score > 0:
            total_score += score
            reviewed_count += 1
            issues_count += len(issues)
        
        color = "#22c55e" if score >= 8 else "#f59e0b" if score >= 5 else "#ef4444" if score > 0 else "#475569"
        status = "\u2705" if score >= 8 else "\u26a0\ufe0f" if score >= 5 else "\u274c" if score > 0 else "\u23f3"
        
        rows += f'<tr style="border-bottom:1px solid #334155"><td style="padding:8px;font-size:.75rem;font-weight:600;color:#e2e8f0">{name}</td><td style="padding:8px;font-size:.7rem;color:#64748b">{slug}</td><td style="padding:8px;text-align:center;color:{color};font-weight:700">{score or "-"}</td><td style="padding:8px;font-size:.65rem;color:#94a3b8">{top_issue}</td><td style="padding:8px;text-align:center">{status}</td><td style="padding:8px"><button onclick="reviewSite(\'{site["id"]}\')" style="font-size:.6rem;padding:3px 8px;background:#6366f1;color:#fff;border:none;border-radius:4px;cursor:pointer">Review</button></td></tr>'
    
    avg_score = round(total_score / reviewed_count, 1) if reviewed_count > 0 else 0
    needs_fix = sum(1 for s in sites if isinstance((s.get("content") or {}).get("_qa_review", {}).get("overall_score", 10), (int, float)) and (s.get("content") or {}).get("_qa_review", {}).get("overall_score", 10) < 8 and (s.get("content") or {}).get("_qa_review", {}).get("overall_score", 0) > 0)

    html = f'''<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>QA Dashboard</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:900px;margin:0 auto}}input,select,textarea{{font-size:16px!important}}h1{{font-size:1.2rem;font-weight:800;margin-bottom:4px}}.sub{{font-size:.72rem;color:#64748b;margin-bottom:16px}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}}.stat{{background:rgba(255,255,255,.03);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:12px;text-align:center}}.stat .n{{font-size:1.2rem;font-weight:800;color:#00e5ff}}.stat .l{{font-size:.58rem;color:#64748b;margin-top:2px}}.actions{{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}}.btn{{padding:8px 14px;border:none;border-radius:8px;font-size:.72rem;font-weight:600;cursor:pointer}}.btn-p{{background:#6366f1;color:#fff}}.btn-g{{background:#22c55e;color:#fff}}.btn-a{{background:#f59e0b;color:#000}}table{{width:100%;border-collapse:collapse;background:rgba(255,255,255,.02);border-radius:10px;overflow:hidden}}th{{text-align:left;padding:8px;font-size:.62rem;color:#64748b;background:rgba(255,255,255,.03)}}#prog{{display:none;text-align:center;padding:10px;font-size:.78rem;color:#94a3b8;margin-bottom:10px}}</style></head><body>
<h1>QA Dashboard</h1>
<p class="sub">Quality analysis &bull; Auto-fix suggestions</p>
<div class="stats">
<div class="stat"><div class="n">{len(sites)}</div><div class="l">Total Sites</div></div>
<div class="stat"><div class="n">{reviewed_count}</div><div class="l">Reviewed</div></div>
<div class="stat"><div class="n">{avg_score}/10</div><div class="l">Avg Score</div></div>
<div class="stat"><div class="n">{needs_fix}</div><div class="l">Need Fix</div></div>
</div>
<div class="actions">
<button class="btn btn-p" onclick="reviewAll()">Review Unreviewed</button>
<button class="btn btn-g" onclick="fixAll()">Auto-Fix Low Scores</button>
<button class="btn btn-a" onclick="location.reload()">Refresh</button>
</div>
<div id="prog"></div>
<table><thead><tr><th>Business</th><th>Site</th><th>Score</th><th>Issue</th><th>Status</th><th>Action</th></tr></thead><tbody>{rows}</tbody></table>
<script>
async function reviewSite(id){{var p=document.getElementById("prog");p.style.display="block";p.textContent="Reviewing...";try{{var r=await fetch("/api/qa/review/"+id,{{method:"POST"}});var d=await r.json();p.textContent="Score: "+(d.overall_score||"?")+"/10";setTimeout(function(){{location.reload()}},2000)}}catch(e){{p.textContent="Error"}}}}
async function reviewAll(){{var p=document.getElementById("prog");p.style.display="block";p.textContent="Reviewing all (1-2 min)...";try{{var r=await fetch("/api/qa/review-all?limit=10");var d=await r.json();p.textContent="Reviewed "+d.reviewed+" sites";setTimeout(function(){{location.reload()}},2000)}}catch(e){{p.textContent="Error"}}}}
async function fixAll(){{var p=document.getElementById("prog");p.style.display="block";p.textContent="Auto-fixing...";try{{var r=await fetch("/api/qa/fix-all",{{method:"POST"}});var d=await r.json();p.textContent="Fixed "+(d.fixed||0)+" sites";setTimeout(function(){{location.reload()}},2000)}}catch(e){{p.textContent="Error"}}}}
</script></body></html>'''
    return HTMLResponse(content=html)


@router.post("/fix-all")
async def fix_all_low_scores():
    """Auto-fix all websites scoring below 8."""
    from app.core.supabase import get_supabase
    from app.services.website_service import WebsiteService
    from app.services.lead_service import LeadService
    from app.agents.qa_review.agent import auto_fix_website
    db = get_supabase()
    sites = db.table("websites").select("id,slug,lead_id,content").not_.is_("slug", "null").limit(50).execute().data or []
    fixed = 0
    for site in sites:
        content = site.get("content", {}) or {}
        if not isinstance(content, dict):
            continue
        review = content.get("_qa_review", {})
        if not review or review.get("overall_score", 10) >= 8:
            continue
        try:
            ls = LeadService()
            lead = ls.get(site["lead_id"]) if site.get("lead_id") else None
            await auto_fix_website(site["id"], review, content, lead)
            fixed += 1
        except Exception:
            continue
    return {"fixed": fixed, "total_checked": len(sites)}
