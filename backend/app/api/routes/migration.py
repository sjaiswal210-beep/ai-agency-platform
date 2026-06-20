from fastapi import APIRouter, HTTPException
from app.core.supabase import get_supabase
import re

router = APIRouter(prefix="/api/admin/migrate", tags=["admin-migration"])


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:30].strip('-')


@router.post("/clients-to-orgs")
async def migrate_clients_to_orgs(pwd: str = ""):
    """Migrate existing clients to organizations. One-time operation."""
    if pwd != "kalpdev2024":
        raise HTTPException(403, "Unauthorized")
    
    db = get_supabase()
    
    # Get all clients
    clients = db.table("clients").select("*").execute()
    if not clients.data:
        return {"message": "No clients found", "migrated": 0}
    
    # Get existing org slugs
    existing = db.table("organizations").select("slug").execute()
    existing_slugs = set(o["slug"] for o in (existing.data or []))
    
    migrated = 0
    errors = []
    
    for client in clients.data:
        try:
            # Get linked lead
            lead = None
            if client.get("lead_id"):
                lead_result = db.table("leads").select("*").eq("id", client["lead_id"]).limit(1).execute()
                lead = lead_result.data[0] if lead_result.data else None
            
            name = client.get("name") or (lead.get("business_name") if lead else None) or f"Business-{client['id'][:8]}"
            slug = slugify(name)
            
            # Ensure unique slug
            base_slug = slug
            counter = 1
            while slug in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            if not slug:
                slug = f"biz-{client['id'][:8]}"
            
            # Create organization
            org_data = {
                "name": name,
                "slug": slug,
                "subdomain": slug,
                "plan": client.get("plan", "starter"),
                "phone": client.get("phone"),
                "status": "active" if client.get("status") == "active" else "suspended",
            }
            
            if lead:
                org_data["email"] = lead.get("email")
                addr = lead.get("address", "")
                parts = [p.strip() for p in addr.split(",") if p.strip()]
                if len(parts) >= 2:
                    org_data["city"] = parts[-2].strip()
            
            result = db.table("organizations").insert(org_data).execute()
            if result.data:
                org_id = result.data[0]["id"]
                existing_slugs.add(slug)
                
                # Enable core modules
                for mod_id in ["crm", "billing", "website", "analytics"]:
                    db.table("organization_modules").upsert({
                        "organization_id": org_id,
                        "module_id": mod_id,
                        "enabled": True
                    }).execute()
                
                migrated += 1
        except Exception as e:
            errors.append(f"{client.get('name', 'unknown')}: {str(e)[:50]}")
    
    return {"message": f"Migration complete", "migrated": migrated, "total_clients": len(clients.data), "errors": errors[:10]}


@router.post("/websites-to-orgs")
async def link_websites_to_orgs(pwd: str = ""):
    """Create orgs from websites that don't have clients. One-time operation."""
    if pwd != "kalpdev2024":
        raise HTTPException(403, "Unauthorized")
    
    db = get_supabase()
    
    # Get websites with slugs
    websites = db.table("websites").select("id, slug, lead_id, template").not_.is_("slug", "null").execute()
    
    # Get existing org slugs
    existing = db.table("organizations").select("slug").execute()
    existing_slugs = set(o["slug"] for o in (existing.data or []))
    
    migrated = 0
    skipped = 0
    
    for website in (websites.data or []):
        slug = website.get("slug", "")
        if not slug or slug in existing_slugs:
            skipped += 1
            continue
        
        # Get lead info
        lead = None
        if website.get("lead_id"):
            lead_result = db.table("leads").select("business_name, phone, email, address, category").eq("id", website["lead_id"]).limit(1).execute()
            lead = lead_result.data[0] if lead_result.data else None
        
        name = lead.get("business_name") if lead else slug.replace("-", " ").title()
        
        org_data = {
            "name": name,
            "slug": slug,
            "subdomain": slug,
            "plan": "starter",
            "phone": lead.get("phone") if lead else None,
            "email": lead.get("email") if lead else None,
            "status": "active",
        }
        
        if lead and lead.get("address"):
            parts = [p.strip() for p in lead["address"].split(",") if p.strip()]
            if len(parts) >= 2:
                org_data["city"] = parts[-2].strip()
        
        try:
            result = db.table("organizations").insert(org_data).execute()
            if result.data:
                org_id = result.data[0]["id"]
                existing_slugs.add(slug)
                
                # Enable core modules
                for mod_id in ["crm", "billing", "website", "analytics"]:
                    db.table("organization_modules").upsert({
                        "organization_id": org_id,
                        "module_id": mod_id,
                        "enabled": True
                    }).execute()
                
                migrated += 1
        except Exception:
            skipped += 1
    
    return {"message": "Website migration complete", "migrated": migrated, "skipped": skipped, "total_websites": len(websites.data or [])}
