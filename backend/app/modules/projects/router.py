from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date

router = APIRouter(prefix="/api/org/{org_id}/projects", tags=["projects"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "projects").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "Projects module not enabled")

@router.get("/")
async def list_projects(org_id: str, status: Optional[str] = None):
    await check_access(org_id)
    db = get_supabase()
    query = db.table("projects").select("*").eq("organization_id", org_id)
    if status: query = query.eq("status", status)
    return {"projects": query.order("created_at", desc=True).execute().data}

@router.post("/")
async def create_project(org_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("projects").insert({
        "organization_id": org_id, "name": data["name"],
        "client_name": data.get("client_name"), "client_phone": data.get("client_phone"),
        "description": data.get("description"),
        "budget_estimated": data.get("budget_estimated", 0),
        "start_date": data.get("start_date"), "end_date": data.get("end_date"),
        "status": data.get("status", "active"),
    }).execute()
    return {"project": result.data[0], "message": "Project created"}

@router.get("/{project_id}")
async def get_project(org_id: str, project_id: str):
    await check_access(org_id)
    db = get_supabase()
    project = db.table("projects").select("*").eq("id", project_id).single().execute()
    milestones = db.table("project_milestones").select("*").eq("project_id", project_id).order("sort_order").execute()
    tasks = db.table("project_tasks").select("*").eq("project_id", project_id).execute()
    expenses = db.table("project_expenses").select("*").eq("project_id", project_id).execute()
    return {"project": project.data, "milestones": milestones.data, "tasks": tasks.data, "expenses": expenses.data}

@router.post("/{project_id}/milestones")
async def add_milestone(org_id: str, project_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("project_milestones").insert({
        "project_id": project_id, "name": data["name"],
        "description": data.get("description"), "deadline": data.get("deadline"),
        "payment_amount": data.get("payment_amount", 0),
    }).execute()
    return {"milestone": result.data[0], "message": "Milestone added"}

@router.post("/{project_id}/tasks")
async def add_task(org_id: str, project_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("project_tasks").insert({
        "project_id": project_id, "milestone_id": data.get("milestone_id"),
        "title": data["title"], "assigned_to": data.get("assigned_to"),
        "status": data.get("status", "todo"), "due_date": data.get("due_date"),
    }).execute()
    return {"task": result.data[0], "message": "Task added"}

@router.post("/{project_id}/expenses")
async def add_expense(org_id: str, project_id: str, data: dict):
    await check_access(org_id)
    db = get_supabase()
    result = db.table("project_expenses").insert({
        "project_id": project_id, "category": data.get("category"),
        "description": data["description"], "amount": data["amount"],
        "vendor": data.get("vendor"), "date": data.get("date", str(date.today())),
    }).execute()
    return {"expense": result.data[0], "message": "Expense added"}

@router.get("/dashboard")
async def projects_dashboard(org_id: str):
    await check_access(org_id)
    db = get_supabase()
    projects = db.table("projects").select("status, budget_estimated").eq("organization_id", org_id).execute()
    total = len(projects.data)
    active = sum(1 for p in projects.data if p["status"] == "active")
    total_budget = sum(float(p.get("budget_estimated", 0) or 0) for p in projects.data)
    return {"total_projects": total, "active_projects": active, "total_budget": total_budget}