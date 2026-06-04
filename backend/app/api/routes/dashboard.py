from fastapi import APIRouter
from app.core.supabase import get_supabase

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats():
    """Get platform-wide dashboard statistics."""
    db = get_supabase()

    leads = db.table("leads").select("*", count="exact").execute()
    websites = db.table("websites").select("*", count="exact").execute()
    outreach = db.table("outreach_messages").select("*", count="exact").execute()

    # Count leads by status
    lead_statuses = {}
    for lead in leads.data:
        s = lead.get("status", "new")
        lead_statuses[s] = lead_statuses.get(s, 0) + 1

    total = leads.count or len(leads.data)
    converted = lead_statuses.get("converted", 0)

    return {
        "total_leads": total,
        "total_websites": websites.count or len(websites.data),
        "total_outreach": outreach.count or len(outreach.data),
        "leads_by_status": lead_statuses,
        "conversion_rate": round((converted / max(total, 1)) * 100, 1),
    }


@router.get("/activity")
def get_activity(limit: int = 20):
    """Get recent agent activity logs."""
    db = get_supabase()
    logs = (
        db.table("agent_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return logs.data


@router.get("/usage")
def get_usage():
    """Get API usage statistics and cost estimates."""
    from app.services.usage_tracker import get_usage_stats
    return get_usage_stats()


@router.post("/usage/reset")
def reset_usage_stats():
    """Reset usage counters."""
    from app.services.usage_tracker import reset_usage
    reset_usage()
    return {"status": "reset"}