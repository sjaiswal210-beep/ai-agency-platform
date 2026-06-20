"""
Migration Script: Convert existing clients + websites into Organizations
Run this once after deploying the Business OS schema.

Usage: python migrate_to_orgs.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
import re

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "") or os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Try loading from .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
        SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "") or os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_KEY environment variables")
    sys.exit(1)

db = create_client(SUPABASE_URL, SUPABASE_KEY)


def slugify(text):
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:30].strip('-')


def migrate_clients_to_organizations():
    """Convert clients table entries to organizations."""
    print("\n=== Migrating Clients to Organizations ===\n")
    
    # Get all clients
    clients = db.table("clients").select("*").execute()
    if not clients.data:
        print("No clients found. Skipping.")
        return
    
    print(f"Found {len(clients.data)} clients to migrate.")
    
    # Get existing org slugs to avoid duplicates
    existing = db.table("organizations").select("slug").execute()
    existing_slugs = set(o["slug"] for o in (existing.data or []))
    
    migrated = 0
    skipped = 0
    
    for client in clients.data:
        # Get linked lead for business name
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
        
        # Determine plan
        plan_map = {"starter": "starter", "pro": "pro", "enterprise": "enterprise"}
        plan = plan_map.get(client.get("plan", "starter"), "starter")
        
        # Create organization
        org_data = {
            "name": name,
            "slug": slug,
            "subdomain": slug,
            "plan": plan,
            "phone": client.get("phone"),
            "email": lead.get("email") if lead else None,
            "city": lead.get("address", "").split(",")[-2].strip() if lead and lead.get("address") and len(lead.get("address", "").split(",")) >= 2 else None,
            "status": "active" if client.get("status") == "active" else "suspended",
        }
        
        try:
            result = db.table("organizations").insert(org_data).execute()
            if result.data:
                org_id = result.data[0]["id"]
                existing_slugs.add(slug)
                
                # Enable default modules (core: crm, billing, website, analytics)
                core_modules = ["crm", "billing", "website", "analytics"]
                for mod_id in core_modules:
                    db.table("organization_modules").upsert({
                        "organization_id": org_id,
                        "module_id": mod_id,
                        "enabled": True
                    }).execute()
                
                # Link website to org (store org_id in website metadata)
                if client.get("lead_id"):
                    websites = db.table("websites").select("id").eq("lead_id", client["lead_id"]).execute()
                    for w in (websites.data or []):
                        # Add org_id to website content as metadata
                        db.table("websites").update({
                            "content": db.table("websites").select("content").eq("id", w["id"]).single().execute().data.get("content", {}) | {"organization_id": org_id}
                        }).eq("id", w["id"]).execute()
                
                migrated += 1
                print(f"  ✓ {name} -> {slug}.city-maps.online (plan: {plan})")
            else:
                skipped += 1
                print(f"  ✗ Failed: {name}")
        except Exception as e:
            skipped += 1
            print(f"  ✗ Error for {name}: {str(e)[:50]}")
    
    print(f"\nDone! Migrated: {migrated}, Skipped: {skipped}")


def migrate_bookings():
    """Migrate existing bookings table to booking_appointments."""
    print("\n=== Migrating Bookings ===\n")
    
    bookings = db.table("bookings").select("*").execute()
    if not bookings.data:
        print("No bookings found. Skipping.")
        return
    
    print(f"Found {len(bookings.data)} bookings to migrate.")
    
    # We need to map lead_id -> organization_id
    orgs = db.table("organizations").select("id, slug").execute()
    # Get websites to map lead_id to org
    websites = db.table("websites").select("lead_id, content").execute()
    lead_to_org = {}
    for w in (websites.data or []):
        content = w.get("content", {})
        if isinstance(content, dict) and content.get("organization_id"):
            lead_to_org[w["lead_id"]] = content["organization_id"]
    
    migrated = 0
    for booking in bookings.data:
        org_id = lead_to_org.get(booking.get("lead_id"))
        if not org_id:
            continue
        
        appt_data = {
            "organization_id": org_id,
            "customer_name": booking.get("customer_name", "Unknown"),
            "customer_phone": booking.get("customer_phone"),
            "date": booking.get("date", "2025-01-01"),
            "start_time": booking.get("time", "10:00"),
            "end_time": booking.get("time", "11:00"),  # Default 1 hour
            "status": booking.get("status", "pending"),
            "notes": booking.get("notes"),
            "source": "manual",
        }
        
        try:
            db.table("booking_appointments").insert(appt_data).execute()
            migrated += 1
        except Exception as e:
            print(f"  ✗ Booking error: {str(e)[:50]}")
    
    print(f"Done! Migrated {migrated} bookings.")


def print_summary():
    """Print current state."""
    print("\n=== Current State ===\n")
    orgs = db.table("organizations").select("id", count="exact").execute()
    modules = db.table("modules").select("id", count="exact").execute()
    org_mods = db.table("organization_modules").select("id", count="exact").execute()
    templates = db.table("industry_templates").select("id", count="exact").execute()
    
    print(f"  Organizations: {orgs.count}")
    print(f"  Modules registered: {modules.count}")
    print(f"  Module assignments: {org_mods.count}")
    print(f"  Industry templates: {templates.count}")
    
    # List orgs
    orgs_data = db.table("organizations").select("name, slug, plan").limit(20).execute()
    if orgs_data.data:
        print(f"\n  Organizations:")
        for o in orgs_data.data:
            print(f"    - {o['name']} ({o['slug']}.city-maps.online) [{o['plan']}]")


if __name__ == "__main__":
    print("=" * 50)
    print("  Business OS - Migration Script")
    print("=" * 50)
    
    migrate_clients_to_organizations()
    migrate_bookings()
    print_summary()
    
    print("\n✅ Migration complete!")
    print("Next steps:")
    print("  1. Go to /admin to see migrated organizations")
    print("  2. Assign templates/modules to each org")
    print("  3. Business owners can access /dashboard/{slug}")
