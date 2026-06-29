"""Shared business credits helper (owner_credits table, keyed by website_id)."""
from __future__ import annotations
from app.core.supabase import get_supabase


def get_credits(website_id: str) -> float:
    try:
        r = get_supabase().table("owner_credits").select("balance").eq("website_id", website_id).limit(1).execute()
        return float(r.data[0]["balance"]) if r.data else 0.0
    except Exception:
        return 0.0


def deduct_credit(website_id: str, amount: float) -> float:
    db = get_supabase()
    bal = get_credits(website_id)
    new_bal = max(0, bal - amount)
    try:
        existing = db.table("owner_credits").select("id").eq("website_id", website_id).limit(1).execute()
        if existing.data:
            db.table("owner_credits").update({"balance": new_bal}).eq("website_id", website_id).execute()
        else:
            db.table("owner_credits").insert({"website_id": website_id, "balance": new_bal}).execute()
    except Exception:
        pass
    return new_bal