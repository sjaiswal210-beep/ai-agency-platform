from __future__ import annotations
from fastapi import APIRouter, Request
from app.core.supabase import get_supabase
import hashlib
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/track")
async def track_event(request: Request):
    """Track a page view or event for a website."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    website_id = body.get("website_id", "")
    event_type = body.get("event_type", "page_view")
    page = body.get("page", "/")
    referrer = body.get("referrer", "")

    # Get IP and hash it for privacy
    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]

    user_agent = request.headers.get("user-agent", "")[:200]

    if not website_id:
        return {"status": "skipped", "reason": "no website_id"}

    db = get_supabase()
    db.table("analytics_events").insert({
        "website_id": website_id,
        "event_type": event_type,
        "page": page,
        "referrer": referrer,
        "user_agent": user_agent,
        "ip_hash": ip_hash,
    }).execute()

    return {"status": "tracked"}


@router.get("/website/{website_id}")
def get_website_analytics(website_id: str, days: int = 30):
    """Get analytics for a specific website."""
    db = get_supabase()

    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    # Total views
    events = (
        db.table("analytics_events")
        .select("*", count="exact")
        .eq("website_id", website_id)
        .gte("created_at", since)
        .execute()
    )

    total_views = events.count or len(events.data or [])

    # Unique visitors (by ip_hash)
    unique_ips = set()
    event_types = {}
    daily_views = {}

    for e in (events.data or []):
        unique_ips.add(e.get("ip_hash", ""))
        et = e.get("event_type", "page_view")
        event_types[et] = event_types.get(et, 0) + 1
        day = e.get("created_at", "")[:10]
        daily_views[day] = daily_views.get(day, 0) + 1

    # Top referrers
    referrers = {}
    for e in (events.data or []):
        ref = e.get("referrer", "") or "direct"
        if ref:
            referrers[ref] = referrers.get(ref, 0) + 1

    top_referrers = sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "website_id": website_id,
        "period_days": days,
        "total_views": total_views,
        "unique_visitors": len(unique_ips),
        "events_by_type": event_types,
        "daily_views": daily_views,
        "top_referrers": [{"source": r[0], "count": r[1]} for r in top_referrers],
    }


@router.get("/website/{website_id}/summary")
def get_analytics_summary(website_id: str):
    """Quick summary for owner dashboard."""
    db = get_supabase()

    # Last 7 days
    since_7d = (datetime.utcnow() - timedelta(days=7)).isoformat()
    since_30d = (datetime.utcnow() - timedelta(days=30)).isoformat()

    views_7d = (
        db.table("analytics_events")
        .select("*", count="exact")
        .eq("website_id", website_id)
        .eq("event_type", "page_view")
        .gte("created_at", since_7d)
        .execute()
    )

    views_30d = (
        db.table("analytics_events")
        .select("*", count="exact")
        .eq("website_id", website_id)
        .eq("event_type", "page_view")
        .gte("created_at", since_30d)
        .execute()
    )

    leads_30d = (
        db.table("analytics_events")
        .select("*", count="exact")
        .eq("website_id", website_id)
        .eq("event_type", "lead_form")
        .gte("created_at", since_30d)
        .execute()
    )

    calls_30d = (
        db.table("analytics_events")
        .select("*", count="exact")
        .eq("website_id", website_id)
        .eq("event_type", "call_click")
        .gte("created_at", since_30d)
        .execute()
    )

    wa_30d = (
        db.table("analytics_events")
        .select("*", count="exact")
        .eq("website_id", website_id)
        .eq("event_type", "whatsapp_click")
        .gte("created_at", since_30d)
        .execute()
    )

    return {
        "views_7d": views_7d.count or 0,
        "views_30d": views_30d.count or 0,
        "leads_30d": leads_30d.count or 0,
        "calls_30d": calls_30d.count or 0,
        "whatsapp_30d": wa_30d.count or 0,
    }
