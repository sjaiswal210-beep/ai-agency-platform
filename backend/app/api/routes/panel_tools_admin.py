from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/admin/panel-tools", tags=["admin-panel-tools"])


@router.get("/")
async def list_panel_tools():
    """List all available panel tools."""
    db = get_supabase()
    result = db.table("panel_tools").select("*").order("sort_order").execute()
    return {"tools": result.data}


@router.get("/website/{website_id}")
async def get_website_tools(website_id: str):
    """Get which tools are enabled/disabled for a specific website."""
    db = get_supabase()
    
    # Get all tools
    all_tools = db.table("panel_tools").select("*").order("sort_order").execute()
    
    # Get overrides for this website
    overrides = db.table("website_tool_config").select("tool_id, enabled").eq("website_id", website_id).execute()
    override_map = {o["tool_id"]: o["enabled"] for o in (overrides.data or [])}
    
    # Merge: tool is enabled if no override exists (uses default) or override says enabled
    tools = []
    for tool in all_tools.data:
        enabled = override_map.get(tool["id"], tool.get("is_default", True))
        tools.append({**tool, "enabled": enabled})
    
    return {"website_id": website_id, "tools": tools}


@router.put("/website/{website_id}")
async def update_website_tools(website_id: str, data: dict):
    """Bulk update tool visibility for a website. 
    Body: {"enabled_tools": ["products", "analytics", ...], "disabled_tools": ["video_creator", ...]}
    """
    db = get_supabase()
    enabled_tools = data.get("enabled_tools", [])
    disabled_tools = data.get("disabled_tools", [])
    
    for tool_id in enabled_tools:
        db.table("website_tool_config").upsert({
            "website_id": website_id,
            "tool_id": tool_id,
            "enabled": True
        }).execute()
    
    for tool_id in disabled_tools:
        db.table("website_tool_config").upsert({
            "website_id": website_id,
            "tool_id": tool_id,
            "enabled": False
        }).execute()
    
    return {"message": "Tools updated", "enabled": len(enabled_tools), "disabled": len(disabled_tools)}


@router.post("/website/{website_id}/toggle")
async def toggle_tool(website_id: str, data: dict):
    """Toggle a single tool on/off for a website.
    Body: {"tool_id": "assistant", "enabled": true}
    """
    db = get_supabase()
    tool_id = data["tool_id"]
    enabled = data["enabled"]
    
    db.table("website_tool_config").upsert({
        "website_id": website_id,
        "tool_id": tool_id,
        "enabled": enabled
    }).execute()
    
    return {"message": f"Tool '{tool_id}' {'enabled' if enabled else 'disabled'}", "tool_id": tool_id, "enabled": enabled}


@router.post("/bulk-update")
async def bulk_update_all_websites(data: dict, pwd: str = ""):
    """Enable/disable a tool for ALL websites at once.
    Body: {"tool_id": "video_creator", "enabled": false}
    """
    if pwd != "kalpdev2024":
        raise HTTPException(403, "Unauthorized")
    
    db = get_supabase()
    tool_id = data["tool_id"]
    enabled = data["enabled"]
    
    # Get all websites
    websites = db.table("websites").select("id").execute()
    count = 0
    for w in (websites.data or []):
        db.table("website_tool_config").upsert({
            "website_id": w["id"],
            "tool_id": tool_id,
            "enabled": enabled
        }).execute()
        count += 1
    
    return {"message": f"Tool '{tool_id}' {'enabled' if enabled else 'disabled'} for {count} websites"}
