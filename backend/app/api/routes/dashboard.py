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

@router.get("/replicate-usage")
async def replicate_usage():
    """Get real Replicate API usage and costs from their API."""
    import os
    import httpx
    token = os.environ.get("REPLICATE_TOKEN", "")
    if not token:
        return {"predictions": 0, "total_cost": 0, "items": []}
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.replicate.com/v1/predictions",
                headers={"Authorization": f"Token {token}"},
                params={"limit": 50}
            )
            if resp.status_code != 200:
                return {"predictions": 0, "total_cost": 0, "error": "API error"}
            
            data = resp.json()
            preds = data.get("results", [])
            
            total_cost = 0
            items = []
            for p in preds:
                metrics = p.get("metrics", {}) or {}
                predict_time = metrics.get("predict_time", 0) or 0
                # LTX-2 distilled runs on Nvidia A40 at $0.000725/sec
                cost = round(predict_time * 0.000725, 4)
                total_cost += cost
                items.append({
                    "id": p.get("id", "")[:8],
                    "model": (p.get("model", "") or "").split("/")[-1][:25],
                    "status": p.get("status", ""),
                    "time": round(predict_time, 1),
                    "cost": cost,
                    "created": (p.get("created_at", "") or "")[:10],
                })
            
            return {
                "predictions": len(preds),
                "total_cost": round(total_cost, 4),
                "items": items[:20],
            }
    except Exception as e:
        return {"predictions": 0, "total_cost": 0, "error": str(e)[:50]}
