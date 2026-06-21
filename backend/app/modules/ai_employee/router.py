from fastapi import APIRouter, HTTPException
from app.core.supabase import get_supabase
from app.core.llm import chat_completion
import json

router = APIRouter(prefix="/api/org/{org_id}/ai", tags=["ai-employee"])

async def check_access(org_id: str):
    db = get_supabase()
    r = db.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "ai_employee").single().execute()
    if not r.data or not r.data.get("enabled"): raise HTTPException(403, "AI Employee not enabled")


@router.post("/ask")
async def ai_ask(org_id: str, data: dict):
    """AI Employee - understands natural language commands and executes actions."""
    await check_access(org_id)
    db = get_supabase()
    
    question = data.get("question", "")
    if not question:
        raise HTTPException(400, "Question required")
    
    # Get org context
    org = db.table("organizations").select("name, slug").eq("id", org_id).single().execute()
    org_name = org.data["name"] if org.data else "Business"
    
    # Get enabled modules for context
    mods = db.table("organization_modules").select("module_id").eq("organization_id", org_id).eq("enabled", True).execute()
    enabled = [m["module_id"] for m in (mods.data or [])]
    
    # Build system prompt
    system = f"""You are an AI business assistant for "{org_name}". 
You can help with these modules: {", ".join(enabled)}.

When the user asks to DO something (create invoice, add contact, book appointment), respond with a JSON action:
{{"action": "create", "module": "crm", "data": {{"name": "...", "phone": "..."}}}}

When the user asks a QUESTION, respond with plain text answer.

Available actions:
- create contact: {{"action":"create","module":"crm","endpoint":"/contacts","data":{{"name":"...","phone":"...","type":"lead"}}}}
- create invoice: {{"action":"create","module":"billing","endpoint":"/invoices","data":{{"type":"invoice","items":[{{"name":"...","quantity":1,"price":0}}]}}}}
- create appointment: {{"action":"create","module":"booking","endpoint":"/appointments","data":{{"customer_name":"...","date":"...","start_time":"...","end_time":"..."}}}}
- add subscriber: {{"action":"create","module":"subscriptions","endpoint":"","data":{{"customer_name":"...","customer_phone":"...","product_name":"...","price_per_unit":0}}}}
- create job card: {{"action":"create","module":"job_cards","endpoint":"","data":{{"customer_name":"...","problem_description":"..."}}}}

If you're not sure what to do, ask a clarifying question.
Keep responses short and helpful. Use emojis."""

    try:
        response = await chat_completion([
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ])
        
        # Check if response is an action (JSON)
        cleaned = response.strip()
        if cleaned.startswith("{"):
            try:
                action = json.loads(cleaned)
                if action.get("action") == "create":
                    # Execute the action
                    module = action.get("module", "")
                    endpoint = action.get("endpoint", "")
                    action_data = action.get("data", {})
                    
                    # Map module to API path
                    module_paths = {
                        "crm": f"/api/org/{org_id}/crm/contacts",
                        "billing": f"/api/org/{org_id}/billing/invoices",
                        "booking": f"/api/org/{org_id}/booking/appointments",
                        "subscriptions": f"/api/org/{org_id}/subscriptions",
                        "job_cards": f"/api/org/{org_id}/job-cards",
                    }
                    
                    api_path = module_paths.get(module, "")
                    if api_path and action_data:
                        # Execute via internal API call
                        # For now, directly insert into DB
                        if module == "crm":
                            action_data["organization_id"] = org_id
                            if "type" not in action_data: action_data["type"] = "lead"
                            db.table("crm_contacts").insert(action_data).execute()
                            return {"answer": f"Done! Created contact: {action_data.get('name', '')}", "action_taken": True, "module": module}
                        elif module == "billing":
                            action_data["organization_id"] = org_id
                            action_data["invoice_number"] = "AI-" + str(hash(question))[-4:]
                            if "status" not in action_data: action_data["status"] = "draft"
                            db.table("billing_invoices").insert(action_data).execute()
                            return {"answer": f"Done! Invoice created.", "action_taken": True, "module": module}
                    
                    return {"answer": f"I understood you want to create something in {module}, but I need more details. Can you specify?", "action_taken": False}
            except json.JSONDecodeError:
                pass
        
        return {"answer": response, "action_taken": False}
    
    except Exception as e:
        return {"answer": f"Sorry, I could not process that. Error: {str(e)[:50]}", "action_taken": False}


@router.get("/suggestions")
async def ai_suggestions(org_id: str):
    """Get AI-powered suggestions based on business data."""
    await check_access(org_id)
    db = get_supabase()
    
    org = db.table("organizations").select("name").eq("id", org_id).single().execute()
    org_name = org.data["name"] if org.data else "Business"
    
    # Get some business stats for context
    contacts = db.table("crm_contacts").select("id", count="exact").eq("organization_id", org_id).execute()
    
    suggestions = [
        "Show me today's pending tasks",
        "Create an invoice for last service",
        "Add a new customer lead",
        "What's my revenue this month?",
        "Send payment reminder to overdue customers",
        "Generate a social media post",
        "Book an appointment for tomorrow",
    ]
    
    return {"suggestions": suggestions, "business": org_name, "total_contacts": contacts.count}


@router.get("/dashboard")
async def ai_dashboard(org_id: str):
    await check_access(org_id)
    return {"status": "active", "queries_today": 0, "actions_executed": 0, "model": "AI Employee v1"}