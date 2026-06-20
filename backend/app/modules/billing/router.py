from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.supabase import get_supabase
from datetime import date

router = APIRouter(prefix="/api/org/{org_id}/billing", tags=["billing"])


async def check_billing_access(org_id: str):
    supabase = get_supabase()
    result = supabase.table("organization_modules").select("enabled").eq("organization_id", org_id).eq("module_id", "billing").single().execute()
    if not result.data or not result.data.get("enabled"):
        raise HTTPException(403, "Billing module not enabled for this organization")


@router.get("/invoices")
async def list_invoices(
    org_id: str,
    status: Optional[str] = None,
    type: Optional[str] = None,
    contact_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0
):
    await check_billing_access(org_id)
    supabase = get_supabase()
    query = supabase.table("billing_invoices").select("*, crm_contacts(name, phone, email)").eq("organization_id", org_id)
    
    if status:
        query = query.eq("status", status)
    if type:
        query = query.eq("type", type)
    if contact_id:
        query = query.eq("contact_id", contact_id)
    
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"invoices": result.data, "count": len(result.data)}


@router.post("/invoices")
async def create_invoice(org_id: str, data: dict):
    await check_billing_access(org_id)
    supabase = get_supabase()
    
    # Auto-generate invoice number
    count = supabase.table("billing_invoices").select("id", count="exact").eq("organization_id", org_id).execute()
    inv_type = data.get("type", "invoice")
    prefix = "INV" if inv_type == "invoice" else "QOT" if inv_type == "quotation" else "RCT"
    number = f"{prefix}-{(count.count or 0) + 1:04d}"
    
    # Calculate totals
    items = data.get("items", [])
    subtotal = sum(item.get("quantity", 1) * item.get("price", 0) for item in items)
    tax_amount = data.get("tax_amount", 0)
    discount_amount = data.get("discount_amount", 0)
    total = subtotal + tax_amount - discount_amount
    
    invoice_data = {
        "organization_id": org_id,
        "invoice_number": number,
        "contact_id": data.get("contact_id"),
        "type": inv_type,
        "status": data.get("status", "draft"),
        "items": items,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "discount_amount": discount_amount,
        "total": total,
        "currency": data.get("currency", "INR"),
        "tax_config": data.get("tax_config", {}),
        "notes": data.get("notes"),
        "terms": data.get("terms"),
        "due_date": data.get("due_date"),
    }
    
    result = supabase.table("billing_invoices").insert(invoice_data).execute()
    return {"invoice": result.data[0], "message": f"{inv_type.title()} created"}


@router.get("/invoices/{invoice_id}")
async def get_invoice(org_id: str, invoice_id: str):
    await check_billing_access(org_id)
    supabase = get_supabase()
    result = supabase.table("billing_invoices").select("*, crm_contacts(name, phone, email, company, address)").eq("id", invoice_id).eq("organization_id", org_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Invoice not found")
    return result.data


@router.put("/invoices/{invoice_id}")
async def update_invoice(org_id: str, invoice_id: str, data: dict):
    await check_billing_access(org_id)
    supabase = get_supabase()
    allowed = ["status", "items", "subtotal", "tax_amount", "discount_amount", "total", "notes", "terms", "due_date", "paid_at", "paid_amount"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    
    # Recalculate if items changed
    if "items" in update_data:
        items = update_data["items"]
        update_data["subtotal"] = sum(item.get("quantity", 1) * item.get("price", 0) for item in items)
        update_data["total"] = update_data["subtotal"] + update_data.get("tax_amount", 0) - update_data.get("discount_amount", 0)
    
    result = supabase.table("billing_invoices").update(update_data).eq("id", invoice_id).eq("organization_id", org_id).execute()
    if not result.data:
        raise HTTPException(404, "Invoice not found")
    return {"invoice": result.data[0], "message": "Updated"}


@router.post("/payments")
async def record_payment(org_id: str, data: dict):
    await check_billing_access(org_id)
    supabase = get_supabase()
    
    payment_data = {
        "organization_id": org_id,
        "invoice_id": data.get("invoice_id"),
        "contact_id": data.get("contact_id"),
        "amount": data["amount"],
        "currency": data.get("currency", "INR"),
        "method": data.get("method"),
        "reference": data.get("reference"),
        "notes": data.get("notes"),
        "payment_date": data.get("payment_date", str(date.today())),
    }
    
    result = supabase.table("billing_payments").insert(payment_data).execute()
    
    # Update invoice paid_amount if linked
    if data.get("invoice_id"):
        invoice = supabase.table("billing_invoices").select("paid_amount, total").eq("id", data["invoice_id"]).single().execute()
        if invoice.data:
            new_paid = float(invoice.data["paid_amount"] or 0) + float(data["amount"])
            status = "paid" if new_paid >= float(invoice.data["total"]) else "partially_paid"
            supabase.table("billing_invoices").update({"paid_amount": new_paid, "status": status}).eq("id", data["invoice_id"]).execute()
    
    return {"payment": result.data[0], "message": "Payment recorded"}


@router.get("/payments")
async def list_payments(org_id: str, limit: int = Query(default=50, le=200)):
    await check_billing_access(org_id)
    supabase = get_supabase()
    result = supabase.table("billing_payments").select("*, billing_invoices(invoice_number), crm_contacts(name)").eq("organization_id", org_id).order("created_at", desc=True).limit(limit).execute()
    return {"payments": result.data}


@router.get("/expenses")
async def list_expenses(org_id: str, category: Optional[str] = None, limit: int = Query(default=50, le=200)):
    await check_billing_access(org_id)
    supabase = get_supabase()
    query = supabase.table("billing_expenses").select("*").eq("organization_id", org_id)
    if category:
        query = query.eq("category", category)
    result = query.order("expense_date", desc=True).limit(limit).execute()
    return {"expenses": result.data}


@router.post("/expenses")
async def add_expense(org_id: str, data: dict):
    await check_billing_access(org_id)
    supabase = get_supabase()
    
    expense_data = {
        "organization_id": org_id,
        "category": data.get("category"),
        "description": data["description"],
        "amount": data["amount"],
        "currency": data.get("currency", "INR"),
        "vendor": data.get("vendor"),
        "receipt_url": data.get("receipt_url"),
        "expense_date": data.get("expense_date", str(date.today())),
    }
    
    result = supabase.table("billing_expenses").insert(expense_data).execute()
    return {"expense": result.data[0], "message": "Expense added"}


@router.get("/dashboard")
async def billing_dashboard(org_id: str):
    await check_billing_access(org_id)
    supabase = get_supabase()
    
    invoices = supabase.table("billing_invoices").select("status, total, paid_amount, type").eq("organization_id", org_id).execute()
    payments = supabase.table("billing_payments").select("amount").eq("organization_id", org_id).execute()
    expenses = supabase.table("billing_expenses").select("amount").eq("organization_id", org_id).execute()
    
    total_revenue = sum(float(p["amount"]) for p in payments.data)
    total_expenses = sum(float(e["amount"]) for e in expenses.data)
    total_pending = sum(float(i["total"]) - float(i["paid_amount"] or 0) for i in invoices.data if i["status"] in ("sent", "overdue", "partially_paid"))
    
    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_income": total_revenue - total_expenses,
        "total_pending": total_pending,
        "invoice_count": len([i for i in invoices.data if i["type"] == "invoice"]),
        "quotation_count": len([i for i in invoices.data if i["type"] == "quotation"]),
    }
