from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.core.supabase import get_supabase
from app.services.lead_service import LeadService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("/group")
def create_location_group(brand_name: str, lead_ids: list[str]):
    """Group multiple leads (branches) under one brand name."""
    db = get_supabase()

    if not brand_name or not lead_ids:
        raise HTTPException(400, "brand_name and lead_ids are required")

    # Verify leads exist
    lead_service = LeadService()
    valid_ids = []
    for lid in lead_ids:
        lead = lead_service.get(lid)
        if lead:
            valid_ids.append(lid)

    if not valid_ids:
        raise HTTPException(404, "No valid leads found")

    # Store group in leads table using notes field (simple approach without new table)
    group_tag = f"[BRAND:{brand_name}]"
    for lid in valid_ids:
        lead = lead_service.get(lid)
        current_notes = lead.get("notes") or ""
        if group_tag not in current_notes:
            new_notes = f"{current_notes} {group_tag}".strip()
            db.table("leads").update({"notes": new_notes}).eq("id", lid).execute()

    return {"brand": brand_name, "locations": len(valid_ids), "lead_ids": valid_ids}


@router.get("/group/{brand_name}")
def get_location_group(brand_name: str):
    """Get all locations/branches for a brand."""
    db = get_supabase()

    # Search leads with brand tag
    tag = f"[BRAND:{brand_name}]"
    result = db.table("leads").select("*").ilike("notes", f"%{tag}%").execute()

    locations = []
    for lead in (result.data or []):
        # Get associated website
        website = db.table("websites").select("id, slug, status").eq("lead_id", lead["id"]).limit(1).execute()
        ws = website.data[0] if website.data else None

        locations.append({
            "lead_id": lead["id"],
            "business_name": lead.get("business_name"),
            "address": lead.get("address"),
            "phone": lead.get("phone"),
            "rating": lead.get("rating"),
            "category": lead.get("category"),
            "website_slug": ws.get("slug") if ws else None,
            "website_url": f"https://city-maps.online/{ws['slug']}" if ws and ws.get("slug") else None,
        })

    return {"brand": brand_name, "location_count": len(locations), "locations": locations}


@router.get("/brands")
def list_brands():
    """List all brand groups."""
    db = get_supabase()
    result = db.table("leads").select("notes").ilike("notes", "%[BRAND:%").execute()

    brands = set()
    for lead in (result.data or []):
        notes = lead.get("notes", "")
        import re
        matches = re.findall(r'\[BRAND:([^\]]+)\]', notes)
        for m in matches:
            brands.add(m)

    return {"brands": sorted(list(brands)), "count": len(brands)}


@router.delete("/group/{brand_name}")
def delete_location_group(brand_name: str):
    """Remove brand grouping (doesn't delete leads, just removes the tag)."""
    db = get_supabase()
    tag = f"[BRAND:{brand_name}]"

    result = db.table("leads").select("id, notes").ilike("notes", f"%{tag}%").execute()
    updated = 0
    for lead in (result.data or []):
        new_notes = (lead.get("notes") or "").replace(tag, "").strip()
        db.table("leads").update({"notes": new_notes}).eq("id", lead["id"]).execute()
        updated += 1

    return {"brand": brand_name, "ungrouped": updated}


@router.get("/nearby/{lead_id}")
def find_nearby_branches(lead_id: str):
    """Find potential branches of the same business nearby."""
    lead_service = LeadService()
    db = get_supabase()

    lead = lead_service.get(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    name = lead.get("business_name", "")
    category = lead.get("category", "")

    # Search for similar business names
    if not name:
        return {"matches": []}

    # Get first word(s) of business name for fuzzy matching
    name_parts = name.split()[:2]
    search_term = name_parts[0] if name_parts else ""

    if len(search_term) < 3:
        return {"matches": []}

    result = db.table("leads").select("id, business_name, address, phone, rating").ilike("business_name", f"%{search_term}%").neq("id", lead_id).limit(10).execute()

    matches = [
        {
            "lead_id": m["id"],
            "business_name": m.get("business_name"),
            "address": m.get("address"),
            "phone": m.get("phone"),
            "similarity": "high" if name.lower() in m.get("business_name", "").lower() or m.get("business_name", "").lower() in name.lower() else "partial",
        }
        for m in (result.data or [])
    ]

    return {"business": name, "potential_branches": matches}
