from __future__ import annotations
import time
from app.core.supabase import get_supabase
from app.core.logging import get_logger

logger = get_logger(__name__)

# In-memory tracker (persists until server restart)
_usage = {
    "google_places_search": {"calls": 0, "cost_per_call": 0.032},
    "google_places_details": {"calls": 0, "cost_per_call": 0.017},
    "google_places_photos": {"calls": 0, "cost_per_call": 0.007},
    "gemini_analysis": {"calls": 0, "cost_per_call": 0.001},
    "gemini_website_gen": {"calls": 0, "cost_per_call": 0.003},
    "gemini_outreach": {"calls": 0, "cost_per_call": 0.001},
    "gemini_logo": {"calls": 0, "cost_per_call": 0.002},
    "gemini_social": {"calls": 0, "cost_per_call": 0.002},
    "gemini_editor": {"calls": 0, "cost_per_call": 0.002},
    "gemini_toolkit": {"calls": 0, "cost_per_call": 0.002},
}


def track_usage(action: str, calls: int = 1):
    """Track an API call."""
    if action in _usage:
        _usage[action]["calls"] += calls


def get_usage_stats() -> dict:
    """Get current usage statistics and costs."""
    items = []
    total_cost = 0.0
    total_google = 0.0
    total_gemini = 0.0

    for action, data in _usage.items():
        cost = data["calls"] * data["cost_per_call"]
        total_cost += cost
        if "google" in action:
            total_google += cost
        else:
            total_gemini += cost

        items.append({
            "action": action,
            "calls": data["calls"],
            "cost_per_call": data["cost_per_call"],
            "total_cost": round(cost, 4),
        })

    return {
        "items": items,
        "total_cost": round(total_cost, 4),
        "total_google_cost": round(total_google, 4),
        "total_gemini_cost": round(total_gemini, 4),
        "google_free_remaining": round(200.0 - total_google, 2),
        "gemini_free": total_gemini < 0.50,  # Effectively free under free tier
    }


def reset_usage():
    """Reset usage counters."""
    for key in _usage:
        _usage[key]["calls"] = 0
