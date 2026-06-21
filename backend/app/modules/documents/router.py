from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date

router = APIRouter(prefix="/api/org/{org_id}/documents", tags=["documents"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "documents").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "Documents module not enabled")

@router.get("/")
async def list_documents(org_id: str, folder: Optional[str] = None, search: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("documents").select("*").eq("organization_id", org_id)
    if folder: query = query.eq("folder", folder)
    if search: query = query.ilike("title", f"%{search}%")
    return {"documents": query.order("created_at", desc=True).execute().data}

@router.post("/")
async def create_document(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("documents").insert({
        "organization_id": org_id, "title": data["title"],
        "type": data.get("type", "file"), "folder": data.get("folder", "general"),
        "file_url": data.get("file_url"), "description": data.get("description"),
        "tags": data.get("tags", []), "linked_to": data.get("linked_to"),
    }).execute()
    return {"document": result.data[0], "message": "Document added"}

@router.get("/folders")
async def list_folders(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("documents").select("folder").eq("organization_id", org_id).execute()
    folders = list(set(d.get("folder", "general") for d in result.data))
    return {"folders": sorted(folders)}

@router.delete("/{doc_id}")
async def delete_document(org_id: str, doc_id: str):
    await check_access(org_id)
    db = get_supabase()
    db.table("documents").delete().eq("id", doc_id).eq("organization_id", org_id).execute()
    return {"message": "Document deleted"}

@router.get("/dashboard")
async def documents_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    docs = db.table("documents").select("type, folder").eq("organization_id", org_id).execute()
    total = len(docs.data)
    by_folder = {}
    for d in docs.data:
        f = d.get("folder", "general")
        by_folder[f] = by_folder.get(f, 0) + 1
    return {"total_documents": total, "by_folder": by_folder}