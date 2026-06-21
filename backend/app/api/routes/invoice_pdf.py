from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/org/{org_id}/billing", tags=["billing-pdf"])


@router.get("/invoices/{invoice_id}/pdf", response_class=HTMLResponse)
async def invoice_pdf_view(org_id: str, invoice_id: str):
    """Generate printable invoice HTML (user can print to PDF from browser)."""
    db = get_supabase()
    invoice = db.table("billing_invoices").select("*, crm_contacts(name, phone, email, company, address)").eq("id", invoice_id).eq("organization_id", org_id).single().execute()
    if not invoice.data:
        raise HTTPException(404, "Invoice not found")
    
    inv = invoice.data
    org = db.table("organizations").select("name, phone, email, address, city").eq("id", org_id).single().execute()
    org_data = org.data or {}
    
    # Build line items
    items = inv.get("items", [])
    rows = ""
    for i, item in enumerate(items):
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        total = qty * price
        rows += f'<tr><td>{i+1}</td><td>{item.get("name","")}</td><td>{qty}</td><td>Rs.{price:,.0f}</td><td>Rs.{total:,.0f}</td></tr>'
    
    inv_type = inv.get("type", "invoice").upper()
    customer = inv.get("crm_contacts") or {}
    
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{inv["invoice_number"]} - {org_data.get("name","")}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Arial,sans-serif;background:#fff;color:#333;padding:20px;max-width:800px;margin:0 auto}}
.header{{display:flex;justify-content:space-between;align-items:start;margin-bottom:30px;padding-bottom:15px;border-bottom:2px solid #6366f1}}
.company{{font-size:1.3rem;font-weight:700;color:#6366f1}}
.company-info{{font-size:.75rem;color:#666;margin-top:4px}}
.inv-title{{text-align:right}}
.inv-title h2{{font-size:1.1rem;color:#333}}
.inv-title .number{{font-size:.85rem;color:#6366f1;font-weight:700}}
.inv-title .date{{font-size:.7rem;color:#999;margin-top:4px}}
.parties{{display:grid;grid-template-columns:1fr 1fr;gap:30px;margin-bottom:24px}}
.party h4{{font-size:.7rem;color:#999;text-transform:uppercase;margin-bottom:6px}}
.party .name{{font-size:.9rem;font-weight:600}}
.party .info{{font-size:.75rem;color:#666;margin-top:2px}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px}}
th{{background:#f8fafc;padding:10px 12px;text-align:left;font-size:.7rem;text-transform:uppercase;color:#64748b;border-bottom:1px solid #e2e8f0}}
td{{padding:10px 12px;border-bottom:1px solid #f1f5f9;font-size:.82rem}}
.totals{{float:right;width:250px}}
.totals .row{{display:flex;justify-content:space-between;padding:6px 0;font-size:.82rem}}
.totals .total{{font-size:1.1rem;font-weight:700;border-top:2px solid #333;padding-top:8px;margin-top:4px}}
.footer{{margin-top:40px;padding-top:15px;border-top:1px solid #e2e8f0;font-size:.7rem;color:#94a3b8;text-align:center}}
.status{{display:inline-block;padding:4px 12px;border-radius:12px;font-size:.7rem;font-weight:600}}
.status-paid{{background:#dcfce7;color:#166534}}
.status-pending{{background:#fef3c7;color:#92400e}}
.status-draft{{background:#f1f5f9;color:#475569}}
@media print{{body{{padding:0}}}}
.print-btn{{position:fixed;bottom:20px;right:20px;padding:12px 20px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.85rem;box-shadow:0 2px 8px rgba(0,0,0,.15)}}
@media print{{.print-btn{{display:none}}}}
</style></head><body>

<div class="header">
<div>
<div class="company">{org_data.get("name", "Business")}</div>
<div class="company-info">{org_data.get("phone", "")} | {org_data.get("email", "")}<br>{org_data.get("address", "")} {org_data.get("city", "")}</div>
</div>
<div class="inv-title">
<h2>{inv_type}</h2>
<div class="number">{inv["invoice_number"]}</div>
<div class="date">Date: {inv.get("created_at","")[:10]}</div>
{f'<div class="date">Due: {inv["due_date"]}</div>' if inv.get("due_date") else ""}
<div style="margin-top:6px"><span class="status status-{inv["status"]}">{inv["status"].upper()}</span></div>
</div>
</div>

<div class="parties">
<div class="party"><h4>Bill To</h4><div class="name">{customer.get("name", "Customer")}</div><div class="info">{customer.get("phone", "")}</div><div class="info">{customer.get("email", "")}</div><div class="info">{customer.get("company", "")}</div></div>
<div class="party"><h4>From</h4><div class="name">{org_data.get("name", "")}</div><div class="info">{org_data.get("phone", "")}</div><div class="info">{org_data.get("email", "")}</div></div>
</div>

<table>
<thead><tr><th>#</th><th>Item</th><th>Qty</th><th>Price</th><th>Amount</th></tr></thead>
<tbody>{rows}</tbody>
</table>

<div class="totals">
<div class="row"><span>Subtotal</span><span>Rs.{float(inv.get("subtotal",0)):,.0f}</span></div>
{f'<div class="row"><span>Tax</span><span>Rs.{float(inv.get("tax_amount",0)):,.0f}</span></div>' if float(inv.get("tax_amount",0)) > 0 else ""}
{f'<div class="row"><span>Discount</span><span>-Rs.{float(inv.get("discount_amount",0)):,.0f}</span></div>' if float(inv.get("discount_amount",0)) > 0 else ""}
<div class="row total"><span>Total</span><span>Rs.{float(inv.get("total",0)):,.0f}</span></div>
{f'<div class="row"><span>Paid</span><span>Rs.{float(inv.get("paid_amount",0)):,.0f}</span></div>' if float(inv.get("paid_amount",0)) > 0 else ""}
</div>

<div style="clear:both"></div>

{f'<div style="margin-top:20px;padding:12px;background:#f8fafc;border-radius:8px;font-size:.8rem;color:#475569"><b>Notes:</b> {inv.get("notes","")}</div>' if inv.get("notes") else ""}

<div class="footer">Thank you for your business! | Generated by City Maps Platform</div>

<button class="print-btn" onclick="window.print()">&#128424; Print / Save PDF</button>
</body></html>'''
    return HTMLResponse(content=html)