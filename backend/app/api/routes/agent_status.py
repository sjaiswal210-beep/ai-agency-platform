from __future__ import annotations
from fastapi import APIRouter
from app.core.supabase import get_supabase
from datetime import datetime, timedelta

router = APIRouter(prefix="/agent-status", tags=["agent-status"])

# In-memory status tracker
_agent_status = {}


def set_agent_status(agent_name: str, status: str, detail: str = ""):
    """Update agent status (call from any agent)."""
    _agent_status[agent_name] = {
        "status": status,
        "detail": detail,
        "updated_at": datetime.utcnow().isoformat(),
    }


def clear_agent_status(agent_name: str):
    """Clear agent status when done."""
    _agent_status[agent_name] = {
        "status": "idle",
        "detail": "",
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.get("/")
def get_all_agent_status():
    """Get current status of all agents."""
    db = get_supabase()
    
    # Get recent activity from logs
    since = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
    try:
        recent = db.table("agent_logs").select("agent_name, action, created_at").gte("created_at", since).order("created_at", desc=True).limit(10).execute()
        recent_activity = recent.data or []
    except Exception:
        recent_activity = []
    
    agents = {
        "lead_discovery": {"name": "Lead Discovery", "icon": "\U0001f50d", "status": "idle"},
        "website_generation": {"name": "Website Generator", "icon": "\U0001f310", "status": "idle"},
        "outreach": {"name": "Outreach Agent", "icon": "\U0001f4e8", "status": "idle"},
        "analysis": {"name": "Business Analyzer", "icon": "\U0001f4ca", "status": "idle"},
        "followup": {"name": "Follow-up Agent", "icon": "\U0001f501", "status": "idle"},
        "seo": {"name": "SEO Engine", "icon": "\U0001f680", "status": "idle"},
    }
    
    # Update from in-memory status
    for key, val in _agent_status.items():
        if key in agents:
            agents[key].update(val)
    
    # Update from recent logs
    for log in recent_activity:
        agent = log.get("agent_name", "")
        if agent in agents:
            agents[agent]["status"] = "active"
            agents[agent]["last_action"] = log.get("action", "")
            agents[agent]["last_active"] = log.get("created_at", "")
    
    return {"agents": agents, "recent_activity": recent_activity[:5]}


@router.get("/recent")
def get_recent_activity(limit: int = 20):
    """Get recent agent activity log."""
    db = get_supabase()
    try:
        result = db.table("agent_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    except Exception:
        return []
