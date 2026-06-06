from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.supabase import get_supabase
from datetime import datetime, timedelta

router = APIRouter(prefix="/owner-analytics", tags=["owner-analytics"])


@router.get("/{website_id}", response_class=HTMLResponse)
def owner_analytics_page(website_id: str):
    """Beautiful analytics dashboard for business owners."""
    service = WebsiteService()
    lead_service = LeadService()
    db = get_supabase()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    slug = website.get("slug", "")
    since_7d = (datetime.utcnow() - timedelta(days=7)).isoformat()
    since_30d = (datetime.utcnow() - timedelta(days=30)).isoformat()
    try:
        v7 = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "page_view").gte("created_at", since_7d).execute()).count or 0
        v30 = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "page_view").gte("created_at", since_30d).execute()).count or 0
        c30 = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "call_click").gte("created_at", since_30d).execute()).count or 0
        w30 = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "whatsapp_click").gte("created_at", since_30d).execute()).count or 0
        l30 = (db.table("analytics_events").select("*", count="exact").eq("website_id", website_id).eq("event_type", "lead_form").gte("created_at", since_30d).execute()).count or 0
    except Exception:
        v7 = v30 = c30 = w30 = l30 = 0
    daily = {}
    try:
        all_ev = db.table("analytics_events").select("created_at").eq("website_id", website_id).gte("created_at", since_7d).execute()
        for e in (all_ev.data or []):
            day = e.get("created_at", "")[:10]
            daily[day] = daily.get(day, 0) + 1
    except Exception:
        pass
    chart_labels = []
    chart_values = []
    for i in range(6, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        chart_labels.append((datetime.utcnow() - timedelta(days=i)).strftime("%b %d"))
        chart_values.append(daily.get(d, 0))
    site_url = f"https://city-maps.online/{slug}" if slug else ""
    max_val = max(max(chart_values), 1)
    bars = "".join(f'<div class="bw"><div class="bv">{chart_values[i]}</div><div class="bar" style="height:{max(4,int(chart_values[i]/max_val*140))}px"></div><div class="bl">{chart_labels[i]}</div></div>' for i in range(7))
    return HTMLResponse(content=_build_html(business_name, site_url, website_id, v7, v30, c30, w30, l30, bars))


def _build_html(name, url, wid, v7, v30, c30, w30, l30, bars):
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Analytics - {name}</title><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet"><style>*{{{{margin:0;padding:0;box-sizing:border-box}}}}body{{{{font-family:"Plus Jakarta Sans",sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}}}}.hdr{{{{background:linear-gradient(135deg,#1e1b4b,#312e81);padding:24px 28px;border-bottom:1px solid rgba(255,255,255,.06)}}}}.hdr h1{{{{font-size:1.3rem;font-weight:800}}}}.hdr p{{{{font-size:.82rem;color:#94a3b8;margin-top:4px}}}}.hdr a{{{{color:#a78bfa}}}}.wrap{{{{max-width:1100px;margin:0 auto;padding:24px}}}}.sg{{{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:28px}}}}.sc{{{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:20px;transition:transform .2s}}}}.sc:hover{{{{transform:translateY(-2px)}}}}.si{{{{font-size:1.5rem;margin-bottom:10px}}}}.sv{{{{font-size:1.7rem;font-weight:800}}}}.sl{{{{font-size:.75rem;color:#64748b;margin-top:2px}}}}.cc{{{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:22px;margin-bottom:22px}}}}.cc h3{{{{font-size:.95rem;font-weight:700;margin-bottom:14px}}}}.chart{{{{display:flex;align-items:end;gap:6px;height:160px}}}}.bw{{{{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px}}}}.bar{{{{width:100%;border-radius:5px 5px 0 0;background:linear-gradient(to top,#7c3aed,#a78bfa);min-height:4px}}}}.bl{{{{font-size:.6rem;color:#64748b}}}}.bv{{{{font-size:.65rem;color:#a78bfa;font-weight:700}}}}.acts{{{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:22px}}}}.ab{{{{display:flex;align-items:center;justify-content:center;gap:6px;padding:13px;border-radius:10px;font-weight:700;font-size:.85rem;text-decoration:none;transition:transform .2s}}}}.ab:hover{{{{transform:translateY(-2px)}}}}.bp{{{{background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff}}}}.bg{{{{background:linear-gradient(135deg,#059669,#10b981);color:#fff}}}}.bb{{{{background:linear-gradient(135deg,#2563eb,#3b82f6);color:#fff}}}}.ba{{{{background:linear-gradient(135deg,#d97706,#f59e0b);color:#fff}}}}.ad{{{{background:rgba(245,158,11,.08);border:1px dashed rgba(245,158,11,.25);border-radius:10px;padding:14px;text-align:center;margin-bottom:16px}}}}.ad p{{{{font-size:.78rem;color:#f59e0b;font-weight:600}}}}.tips{{{{background:rgba(124,58,237,.06);border:1px solid rgba(124,58,237,.15);border-radius:14px;padding:20px;margin-bottom:22px}}}}.tips h3{{{{font-size:.9rem;font-weight:700;color:#a78bfa;margin-bottom:10px}}}}.tips li{{{{font-size:.82rem;color:#94a3b8;margin-bottom:6px;list-style:none;padding-left:18px;position:relative}}}}.tips li::before{{{{content:"\2713";position:absolute;left:0;color:#a78bfa}}}}.ft{{{{text-align:center;padding:18px;font-size:.72rem;color:#475569;border-top:1px solid rgba(255,255,255,.05)}}}}@media(max-width:640px){{{{.sg{{{{grid-template-columns:repeat(2,1fr)}}}}.acts{{{{grid-template-columns:1fr}}}}}}}}</style></head><body><div class="hdr"><h1>\U0001f4ca {name}</h1><p>Website Analytics &bull; <a href="{url}" target="_blank">{url or "Preview"}</a></p></div><div class="wrap"><div class="sg"><div class="sc"><div class="si">\U0001f4c8</div><div class="sv">{v7}</div><div class="sl">Views (7d)</div></div><div class="sc"><div class="si">\U0001f4de</div><div class="sv">{c30}</div><div class="sl">Calls (30d)</div></div><div class="sc"><div class="si">\U0001f4ac</div><div class="sv">{w30}</div><div class="sl">WhatsApp (30d)</div></div><div class="sc"><div class="si">\U0001f4dd</div><div class="sv">{l30}</div><div class="sl">Leads (30d)</div></div><div class="sc"><div class="si">\U0001f30d</div><div class="sv">{v30}</div><div class="sl">Total (30d)</div></div></div><div class="cc"><h3>\U0001f4c5 Daily Visitors</h3><div class="chart">{bars}</div></div><div class="ad"><p>\U0001f4e2 Promote your business here</p></div><div class="acts"><a href="/api/daily/{wid}" class="ab bp">\U0001f4f1 Daily Content</a><a href="{url}" target="_blank" class="ab bg">\U0001f310 View Site</a><a href="/api/panel/{wid}" class="ab bb">\U0001f6e0 Manage</a><a href="/api/owner-analytics/{wid}" class="ab ba">\U0001f504 Refresh</a></div><div class="tips"><h3>\U0001f4a1 Growth Tips</h3><ul><li>Share your website on WhatsApp status daily</li><li>Ask happy customers to leave Google reviews</li><li>Post your work on Instagram with location tag</li><li>Update Google Business Profile with new photos</li><li>Reply to all Google reviews</li></ul></div><div class="ad"><p>\U0001f381 Upgrade to Premium for AI Ads & Social Calendar</p></div></div><div class="ft">Powered by <a href="https://city-maps.online" style="color:#a78bfa">City Maps</a> &bull; Made with \u2764\ufe0f by Kalpdev Digitals</div></body></html>'''
