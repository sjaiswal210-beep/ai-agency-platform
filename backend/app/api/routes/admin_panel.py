from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_USER = "shubham"
ADMIN_PASS = "Shubham@1994"


@router.post("/login")
def admin_login(username: str = "", password: str = ""):
    """Admin authentication."""
    if username == ADMIN_USER and password == ADMIN_PASS:
        return {"status": "authenticated", "token": "admin-session-active"}
    raise HTTPException(401, "Invalid credentials")


@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(auth: str = ""):
    """Full admin dashboard - overview of all businesses, websites, leads."""
    db = get_supabase()

    # Stats
    leads_r = db.table("leads").select("*", count="exact").execute()
    websites_r = db.table("websites").select("*", count="exact").execute()
    total_leads = leads_r.count or len(leads_r.data or [])
    total_websites = websites_r.count or len(websites_r.data or [])

    # Recent leads
    recent = db.table("leads").select("id, business_name, category, phone, rating, status, created_at").order("created_at", desc=True).limit(20).execute()

    # Recent websites
    recent_sites = db.table("websites").select("id, lead_id, slug, status, created_at").order("created_at", desc=True).limit(20).execute()

    # Status breakdown
    statuses = {}
    for l in (leads_r.data or []):
        s = l.get("status", "new")
        statuses[s] = statuses.get(s, 0) + 1

    # Categories breakdown
    categories = {}
    for l in (leads_r.data or []):
        cat = l.get("category", "other") or "other"
        categories[cat] = categories.get(cat, 0) + 1
    top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:8]

    # Build lead rows
    lead_rows = ""
    for l in (recent.data or []):
        lead_rows += f'<tr><td>{l.get("business_name","")}</td><td>{l.get("category","")}</td><td>{l.get("phone","")}</td><td>{l.get("rating","")}</td><td><span class="badge">{l.get("status","")}</span></td><td>{l.get("created_at","")[:10]}</td></tr>'

    # Build website rows
    site_rows = ""
    for s in (recent_sites.data or []):
        slug = s.get("slug", "")
        url = f"https://city-maps.online/{slug}" if slug else ""
        site_rows += f'<tr><td><a href="{url}" target="_blank">{slug or s["id"][:8]}</a></td><td>{s.get("status","")}</td><td>{s.get("created_at","")[:10]}</td></tr>'

    # Status bars
    status_bars = ""
    for status, count in statuses.items():
        pct = int(count / max(total_leads, 1) * 100)
        status_bars += f'<div class="sbar"><span class="slbl">{status}</span><div class="strack"><div class="sfill" style="width:{pct}%"></div></div><span class="snum">{count}</span></div>'

    # Category chips
    cat_chips = "".join(f'<span class="chip">{c}: {n}</span>' for c, n in top_cats)

    html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    html += '<title>Admin Panel - AI Agency Platform</title>'
    html += '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    html += '<style>'
    html += "*{margin:0;padding:0;box-sizing:border-box}"
    html += "body{font-family:'Plus Jakarta Sans',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}"
    html += ".top{background:linear-gradient(135deg,#1e1b4b,#312e81);padding:20px 24px;display:flex;justify-content:space-between;align-items:center}"
    html += ".top h1{font-size:1.2rem;font-weight:800}.top span{font-size:.75rem;color:#94a3b8}"
    html += ".wrap{max-width:1200px;margin:0 auto;padding:20px}"
    html += ".stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px}"
    html += ".sc{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:18px;text-align:center}"
    html += ".sc .num{font-size:1.6rem;font-weight:800}.sc .lbl{font-size:.72rem;color:#64748b;margin-top:4px}"
    html += ".card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:18px;margin-bottom:16px}"
    html += ".card h3{font-size:.9rem;font-weight:700;margin-bottom:12px;color:#a78bfa}"
    html += "table{width:100%;border-collapse:collapse;font-size:.8rem}"
    html += "th{text-align:left;padding:8px;color:#64748b;border-bottom:1px solid rgba(255,255,255,.08);font-size:.7rem;text-transform:uppercase}"
    html += "td{padding:8px;border-bottom:1px solid rgba(255,255,255,.04)}"
    html += "td a{color:#a78bfa}"
    html += ".badge{background:rgba(124,58,237,.2);color:#a78bfa;padding:2px 8px;border-radius:50px;font-size:.68rem;font-weight:600}"
    html += ".sbar{display:flex;align-items:center;gap:8px;margin-bottom:8px}"
    html += ".slbl{font-size:.75rem;width:90px;color:#94a3b8}"
    html += ".strack{flex:1;height:6px;background:rgba(255,255,255,.08);border-radius:3px;overflow:hidden}"
    html += ".sfill{height:100%;background:linear-gradient(90deg,#7c3aed,#a78bfa);border-radius:3px}"
    html += ".snum{font-size:.75rem;color:#64748b;width:30px;text-align:right}"
    html += ".chip{display:inline-block;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);padding:4px 10px;border-radius:50px;font-size:.7rem;margin:3px}"
    html += ".grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}"
    html += "@media(max-width:768px){.grid2{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}}"
    html += '</style></head><body>'
    html += f'<div class="top"><h1>\U0001f6e0 Admin Panel</h1><span>{total_leads} leads | {total_websites} websites</span></div>'
    html += '<div class="wrap">'
    html += '<div class="stats">'
    html += f'<div class="sc"><div class="num">{total_leads}</div><div class="lbl">Total Leads</div></div>'
    html += f'<div class="sc"><div class="num">{total_websites}</div><div class="lbl">Websites</div></div>'
    html += f'<div class="sc"><div class="num">{statuses.get("converted", 0)}</div><div class="lbl">Converted</div></div>'
    html += f'<div class="sc"><div class="num">{len(categories)}</div><div class="lbl">Categories</div></div>'
    html += '</div>'
    html += '<div class="grid2">'
    html += f'<div class="card"><h3>Pipeline Status</h3>{status_bars}</div>'
    html += f'<div class="card"><h3>Top Categories</h3>{cat_chips}</div>'
    html += '</div>'
    html += f'<div class="card"><h3>Recent Leads (20)</h3><table><thead><tr><th>Business</th><th>Category</th><th>Phone</th><th>Rating</th><th>Status</th><th>Date</th></tr></thead><tbody>{lead_rows}</tbody></table></div>'
    html += f'<div class="card"><h3>Recent Websites (20)</h3><table><thead><tr><th>Slug/URL</th><th>Status</th><th>Date</th></tr></thead><tbody>{site_rows}</tbody></table></div>'
    html += '<div class="card"><h3>Quick Notes</h3><textarea id="noteText" rows="2" placeholder="Write a note..." style="width:100%;padding:8px;border:1px solid rgba(255,255,255,.08);border-radius:8px;background:rgba(255,255,255,.04);color:#e2e8f0;font-size:.8rem;margin-bottom:8px;resize:none"></textarea><button onclick="saveNote()" style="background:#7c3aed;color:#fff;border:none;padding:6px 12px;border-radius:6px;font-size:.75rem;font-weight:600;cursor:pointer">Save Note</button><div id="notesList" style="margin-top:10px;font-size:.75rem;color:#94a3b8"></div></div>'
    html += '<script>async function saveNote(){var t=document.getElementById("noteText").value;if(!t)return;await fetch("/api/admin/notes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:t})});document.getElementById("noteText").value="";loadNotes();}async function loadNotes(){var r=await fetch("/api/admin/notes");var d=await r.json();var h="";d.forEach(function(n){h+="<div style=padding:6px;border-bottom:1px_solid_rgba(255,255,255,.04)>"+n.note+"</div>";});document.getElementById("notesList").innerHTML=h;}loadNotes();</script>'
    html += '</div></body></html>'
    return HTMLResponse(content=html)


@router.get("/leads")
def admin_list_leads(status: str = "", category: str = "", limit: int = 50):
    """List all leads with filters."""
    db = get_supabase()
    query = db.table("leads").select("*").order("created_at", desc=True).limit(limit)
    if status:
        query = query.eq("status", status)
    if category:
        query = query.ilike("category", f"%{category}%")
    result = query.execute()
    return result.data or []


@router.get("/websites")
def admin_list_websites(limit: int = 50):
    """List all websites with slugs."""
    db = get_supabase()
    result = db.table("websites").select("id, lead_id, slug, status, created_at").order("created_at", desc=True).limit(limit).execute()
    return result.data or []


@router.delete("/lead/{lead_id}")
def admin_delete_lead(lead_id: str):
    """Delete a lead and all associated data."""
    db = get_supabase()
    db.table("websites").delete().eq("lead_id", lead_id).execute()
    db.table("outreach_messages").delete().eq("lead_id", lead_id).execute()
    db.table("leads").delete().eq("id", lead_id).execute()
    return {"deleted": True, "lead_id": lead_id}


@router.delete("/website/{website_id}")
def admin_delete_website(website_id: str):
    """Delete a website."""
    db = get_supabase()
    db.table("websites").delete().eq("id", website_id).execute()
    return {"deleted": True, "website_id": website_id}


@router.post("/bulk-delete-leads")
def admin_bulk_delete(status: str = ""):
    """Delete all leads with a given status."""
    if not status:
        raise HTTPException(400, "status parameter required")
    db = get_supabase()
    leads = db.table("leads").select("id").eq("status", status).execute()
    ids = [l["id"] for l in (leads.data or [])]
    for lid in ids:
        db.table("websites").delete().eq("lead_id", lid).execute()
        db.table("leads").delete().eq("id", lid).execute()
    return {"deleted": len(ids), "status": status}


@router.get("/stats")
def admin_stats():
    """Platform-wide statistics."""
    db = get_supabase()
    leads = db.table("leads").select("status, category, rating", count="exact").execute()
    websites = db.table("websites").select("status", count="exact").execute()

    statuses = {}
    categories = {}
    avg_rating = 0
    rated_count = 0
    for l in (leads.data or []):
        s = l.get("status", "new")
        statuses[s] = statuses.get(s, 0) + 1
        cat = l.get("category", "other") or "other"
        categories[cat] = categories.get(cat, 0) + 1
        if l.get("rating"):
            avg_rating += float(l["rating"])
            rated_count += 1

    return {
        "total_leads": leads.count or 0,
        "total_websites": websites.count or 0,
        "leads_by_status": statuses,
        "leads_by_category": categories,
        "avg_rating": round(avg_rating / max(rated_count, 1), 2),
    }


@router.get("/notes")
def get_notes():
    """Get saved admin notes."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    try:
        result = db.table("agent_logs").select("*").eq("agent_name", "admin_notes").order("created_at", desc=True).limit(20).execute()
        return [{"id": r["id"], "note": r.get("action", ""), "created_at": r.get("created_at", "")} for r in (result.data or [])]
    except Exception:
        return []


@router.post("/notes")
def save_note(note: dict):
    """Save an admin note."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    text = note.get("text", "")
    if not text:
        raise HTTPException(400, "Note text required")
    db.table("agent_logs").insert({"agent_name": "admin_notes", "action": text, "details": {"type": "note"}}).execute()
    return {"saved": True}




@router.put("/notes/{note_id}")
def update_note(note_id: str, data: dict):
    """Update an admin note (edit text, mark done, add reply)."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    new_text = data.get("note", "")
    if not new_text:
        raise HTTPException(400, "Note text required")
    try:
        db.table("agent_logs").update({"action": new_text}).eq("id", note_id).eq("agent_name", "admin_notes").execute()
        return {"updated": True}
    except Exception as e:
        raise HTTPException(500, str(e)[:100])

@router.delete("/notes/{note_id}")
def delete_note(note_id: str):
    """Delete an admin note."""
    from app.core.supabase import get_supabase
    db = get_supabase()
    db.table("agent_logs").delete().eq("id", note_id).eq("agent_name", "admin_notes").execute()
    return {"deleted": True}
