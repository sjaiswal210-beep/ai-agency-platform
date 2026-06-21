from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/biz", tags=["business-ui"])


def get_org_from_slug(slug_or_id: str):
    db = get_supabase()
    org = db.table("organizations").select("id, name, slug, brand_color, phone").eq("slug", slug_or_id).limit(1).execute()
    if not org.data:
        org = db.table("organizations").select("id, name, slug, brand_color, phone").eq("id", slug_or_id).limit(1).execute()
    return org.data[0] if org.data else None


def base_css():
    return """*{margin:0;padding:0;box-sizing:border-box}body{font-family:Inter,-apple-system,sans-serif;background:#f8fafc;color:#1e293b;min-height:100vh;padding-bottom:70px}.hd{background:#fff;border-bottom:1px solid #e2e8f0;padding:12px 16px;position:sticky;top:0;z-index:50}.hd-in{max-width:640px;margin:0 auto;display:flex;align-items:center;justify-content:space-between}.hd h1{font-size:.95rem;font-weight:700}.mn{max-width:640px;margin:0 auto;padding:12px 16px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px}.st{background:#fff;border:1px solid #f1f5f9;border-radius:10px;padding:12px;text-align:center}.st .n{font-size:1.2rem;font-weight:800;color:#6366f1}.st .l{font-size:.6rem;color:#94a3b8;margin-top:2px}.card{background:#fff;border:1px solid #f1f5f9;border-radius:10px;margin-bottom:8px}.btn{padding:9px 16px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:600;font-size:.8rem;cursor:pointer}.btn:hover{opacity:.9}.btn-sm{padding:5px 10px;font-size:.7rem;border-radius:6px}.list-item{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid #f8fafc}.list-item:hover{background:#f8fafc}.li-name{font-size:.82rem;font-weight:600}.li-meta{font-size:.65rem;color:#94a3b8;margin-top:1px}.badge{font-size:.6rem;padding:2px 8px;border-radius:10px;font-weight:600;background:#eff6ff;color:#3b82f6}.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;align-items:center;justify-content:center;padding:16px}.modal.show{display:flex}.modal-box{background:#fff;border-radius:14px;padding:20px;width:100%;max-width:440px;max-height:85vh;overflow-y:auto}.field{margin-bottom:10px}.field label{display:block;font-size:.7rem;font-weight:600;color:#64748b;margin-bottom:3px}.field input,.field select,.field textarea{width:100%;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;outline:none;font-family:inherit}.field textarea{resize:vertical;min-height:60px}.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.empty{text-align:center;padding:40px 16px;color:#94a3b8;font-size:.8rem}"""


def build_generic_page(org_id, org_name, module_id, module_name, emoji, api_path, list_key, fields):
    """Build a complete interactive module page without f-string issues."""
    
    # Build form fields HTML
    fields_html = ""
    field_ids = []
    required_ids = []
    for (fid, label, ftype, required) in fields:
        field_ids.append(fid)
        if required:
            required_ids.append(fid)
        req_mark = " *" if required else ""
        if ftype.startswith("select:"):
            options = ftype.split(":")[1].split(",")
            opts_html = "".join(['<option value="' + o + '">' + o.replace("_", " ").title() + '</option>' for o in options])
            fields_html += '<div class="field"><label>' + label + req_mark + '</label><select id="f_' + fid + '">' + opts_html + '</select></div>'
        elif ftype == "textarea":
            fields_html += '<div class="field"><label>' + label + req_mark + '</label><textarea id="f_' + fid + '" placeholder="' + label + '"></textarea></div>'
        else:
            fields_html += '<div class="field"><label>' + label + req_mark + '</label><input id="f_' + fid + '" type="' + ftype + '" placeholder="' + label + '"></div>'
    
    # JS to collect form data
    collect_js = "{" + ",".join(['"' + fid + '":document.getElementById("f_' + fid + '").value' for fid in field_ids]) + "}"
    required_check = "||".join(['!document.getElementById("f_' + fid + '").value.trim()' for fid in required_ids]) if required_ids else "false"
    
    page = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>""" + module_name + " - " + org_name + """</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>""" + base_css() + """</style></head><body>
<div class="hd"><div class="hd-in"><h1>""" + emoji + " " + module_name + """</h1><a href="#" style="color:#64748b;text-decoration:none;font-size:1.4rem" onclick="history.back();return false">&times;</a></div></div>
<div class="mn">
<div class="stats" id="stats"><div class="st"><div class="n">-</div><div class="l">Loading...</div></div></div>
<div style="display:flex;justify-content:flex-end;margin-bottom:10px"><button class="btn btn-sm" onclick="document.getElementById('addModal').classList.add('show')">+ Add New</button></div>
<div class="card" id="mainList"><div class="empty">Loading...</div></div>
</div>
<div class="modal" id="addModal"><div class="modal-box"><h2>Add """ + module_name + """</h2>
""" + fields_html + """
<div style="display:flex;gap:8px;margin-top:14px"><button class="btn" onclick="saveItem()" style="flex:1">Save</button><button class="btn" style="flex:.4;background:#e2e8f0;color:#475569" onclick="document.getElementById('addModal').classList.remove('show')">Cancel</button></div>
</div></div>
<script>
var API=\"""" + api_path + """\";var LIST_KEY=\"""" + list_key + """\";
async function loadDash(){try{var r=await fetch(API+"/dashboard");var d=await r.json();var h="";Object.entries(d).slice(0,4).forEach(function(e){var l=e[0].replace(/_/g," ");var v=typeof e[1]==="number"?(e[1]>999?"\\u20B9"+e[1].toLocaleString():e[1]):e[1];h+='<div class="st"><div class="n">'+v+'</div><div class="l">'+l+'</div></div>';});document.getElementById("stats").innerHTML=h;}catch(e){}}
async function loadList(){try{var r=await fetch(API+"?limit=50");var d=await r.json();var items=d[LIST_KEY]||d.items||[];if(!Array.isArray(items)){var k=Object.keys(d);for(var i=0;i<k.length;i++){if(Array.isArray(d[k[i]])){items=d[k[i]];break;}}}if(!items||items.length===0){document.getElementById("mainList").innerHTML='<div class="empty">No records yet. Add your first one!</div>';return;}document.getElementById("mainList").innerHTML=items.map(function(item){var name=item.customer_name||item.name||item.client_name||item.vehicle_number||item.title||"Record";var meta=item.phone||item.customer_phone||item.client_phone||item.status||item.type||item.due_date||"";var badge=item.status?'<span class="badge">'+item.status+'</span>':"";return '<div class="list-item"><div><div class="li-name">'+name+'</div><div class="li-meta">'+meta+'</div></div>'+badge+'</div>';}).join("");}catch(e){document.getElementById("mainList").innerHTML='<div class="empty">Error loading</div>';}}
async function saveItem(){if(""" + required_check + """){alert("Fill required fields");return;}var body=""" + collect_js + """;Object.keys(body).forEach(function(k){if(body[k]&&!isNaN(body[k])&&k.indexOf("phone")<0&&k!=="vehicle_number")body[k]=Number(body[k]);});await fetch(API,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});document.getElementById("addModal").classList.remove("show");document.querySelectorAll("#addModal input,#addModal textarea,#addModal select").forEach(function(el){el.value="";});loadList();loadDash();}
loadDash();loadList();
</script></body></html>"""
    return page


# Module configurations
MODULES = {
    "booking": ("Booking", "&#128197;", "/booking/appointments", "appointments", [("customer_name","Customer Name","text",True),("customer_phone","Phone","tel",False),("date","Date","date",True),("start_time","Time","time",True),("notes","Notes","text",False)]),
    "subscriptions": ("Subscriptions", "&#128257;", "/subscriptions", "subscriptions", [("customer_name","Customer","text",True),("customer_phone","Phone","tel",True),("address","Address","text",False),("product_name","Product","text",True),("quantity","Qty","number",False),("price_per_unit","Price/Unit","number",True),("frequency","Frequency","select:daily,alternate,weekdays,weekly",False)]),
    "job_cards": ("Job Cards", "&#128295;", "/job-cards", "job_cards", [("customer_name","Customer","text",True),("customer_phone","Phone","tel",False),("device_type","Type","select:vehicle_2w,vehicle_4w,mobile,laptop,appliance,electrical,plumbing,other",False),("device_brand","Brand","text",False),("problem_description","Problem","textarea",True),("estimated_cost","Est. Cost","number",False)]),
    "custom_orders": ("Custom Orders", "&#128203;", "/custom-orders", "orders", [("customer_name","Customer","text",True),("customer_phone","Phone","tel",False),("item_description","Item","textarea",True),("material","Material","text",False),("material_cost","Material Cost","number",False),("making_charges","Making Charges","number",False),("promised_date","Delivery Date","date",False)]),
    "clinic": ("Clinic", "&#129657;", "/clinic/patients", "patients", [("name","Patient Name","text",True),("phone","Phone","tel",False),("age","Age","number",False),("gender","Gender","select:male,female,other",False),("blood_group","Blood Group","text",False),("medical_history","History","textarea",False)]),
    "students": ("Students", "&#127891;", "/students", "students", [("name","Student Name","text",True),("phone","Phone","tel",False),("parent_phone","Parent Phone","tel",False),("email","Email","email",False)]),
    "events": ("Events", "&#127881;", "/events/bookings", "bookings", [("client_name","Client","text",True),("client_phone","Phone","tel",False),("event_type","Type","select:wedding,reception,birthday,corporate,other",False),("event_date","Date","date",True),("guest_count","Guests","number",False),("total_amount","Amount","number",False)]),
    "fleet": ("Fleet", "&#128663;", "/fleet/vehicles", "vehicles", [("vehicle_number","Vehicle No.","text",True),("type","Type","select:car,bike,auto,truck,van,bus",False),("make","Make","text",False),("model","Model","text",False)]),
    "reminders": ("Reminders", "&#128276;", "/reminders", "reminders", [("customer_name","Customer","text",True),("customer_phone","Phone","tel",True),("type","Type","select:insurance,vehicle_service,amc,warranty,checkup,followup,general",False),("item_description","Description","text",False),("due_date","Due Date","date",True),("recurrence","Repeat","select:none,monthly,quarterly,yearly",False)]),
    "inventory": ("Inventory", "&#128230;", "/inventory/products", "products", [("name","Product","text",True),("sku","SKU","text",False),("price","Price","number",True),("cost_price","Cost","number",False),("stock_quantity","Stock","number",False),("unit","Unit","select:pcs,kg,ltr,box,mtr",False)]),
}


@router.get("/{slug_or_id}/crm", response_class=HTMLResponse)
async def crm_page(slug_or_id: str):
    """CRM - full page served separately (already defined in earlier code)."""
    org = get_org_from_slug(slug_or_id)
    if not org:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    # For CRM we have a more complex page - use generic for now
    return HTMLResponse(build_generic_page(org["id"], org["name"], "crm", "CRM", "&#128101;", "/api/org/" + org["id"] + "/crm/contacts", "contacts",
        [("name","Name","text",True),("phone","Phone","tel",False),("email","Email","email",False),("type","Type","select:lead,customer,vendor,partner",False),("company","Company","text",False),("source","Source","text",False)]))


@router.get("/{slug_or_id}/billing", response_class=HTMLResponse)
async def billing_page(slug_or_id: str):
    org = get_org_from_slug(slug_or_id)
    if not org:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    return HTMLResponse(build_generic_page(org["id"], org["name"], "billing", "Billing", "&#129534;", "/api/org/" + org["id"] + "/billing/invoices", "invoices",
        [("type","Type","select:invoice,quotation",False),("notes","Notes","text",False)]))


@router.get("/{slug_or_id}/whatsapp", response_class=HTMLResponse)
async def whatsapp_page(slug_or_id: str):
    org = get_org_from_slug(slug_or_id)
    if not org:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    # Simple send page for now
    return HTMLResponse(build_generic_page(org["id"], org["name"], "whatsapp", "WhatsApp", "&#128172;", "/api/org/" + org["id"] + "/whatsapp/messages", "messages",
        [("phone","Phone","tel",True),("message","Message","textarea",True)]))


@router.get("/{slug_or_id}/{module_id}", response_class=HTMLResponse)
async def generic_module_page(slug_or_id: str, module_id: str):
    org = get_org_from_slug(slug_or_id)
    if not org:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    
    config = MODULES.get(module_id)
    if not config:
        return HTMLResponse("<h2>Module '" + module_id + "' not available</h2><p><a href='javascript:history.back()'>Back</a></p>")
    
    name, emoji, api_suffix, list_key, fields = config
    api_path = "/api/org/" + org["id"] + api_suffix
    
    return HTMLResponse(build_generic_page(org["id"], org["name"], module_id, name, emoji, api_path, list_key, fields))


@router.get("/{slug_or_id}/subscriptions/deliver", response_class=HTMLResponse)
async def delivery_board(slug_or_id: str):
    org = get_org_from_slug(slug_or_id)
    if not org:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    org_id = org["id"]
    # Simple delivery board
    page = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Deliveries - ' + org["name"] + '</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"><style>' + base_css() + '</style></head><body><div class="hd"><div class="hd-in"><h1>&#128666; Today\'s Deliveries</h1><a href="#" style="color:#64748b;text-decoration:none;font-size:1.4rem" onclick="history.back();return false">&times;</a></div></div><div class="mn"><div class="stats" id="stats"><div class="st"><div class="n" id="tc">-</div><div class="l">Total</div></div><div class="st"><div class="n" id="dc" style="color:#22c55e">-</div><div class="l">Done</div></div><div class="st"><div class="n" id="pc" style="color:#f59e0b">-</div><div class="l">Pending</div></div></div><div class="card" id="list"><div class="empty">Loading...</div></div></div><script>var API="/api/org/' + org_id + '/subscriptions";async function load(){var r=await fetch(API+"/today");var d=await r.json();var items=d.deliveries||[];document.getElementById("tc").textContent=items.length;var done=items.filter(function(i){return i.delivery_status==="delivered"}).length;document.getElementById("dc").textContent=done;document.getElementById("pc").textContent=items.length-done;if(items.length===0){document.getElementById("list").innerHTML=\'<div class="empty">No deliveries today</div>\';return;}document.getElementById("list").innerHTML=items.map(function(d,i){var cls=d.delivery_status==="delivered"?"color:#22c55e":"";return \'<div class="list-item"><div><div class="li-name" style="\'+cls+\'">\'+(d.delivery_status==="delivered"?"&#10003; ":"")+d.customer_name+\'</div><div class="li-meta">\'+((d.product_name||"")+" "+(d.address||""))+\'</div></div><div>\'+((d.delivery_status!=="delivered")?\'<button class="btn btn-sm" onclick="mark(\\\'\'+d.id+\'\\\')">Done</button>\':\'<span class="badge" style="background:#dcfce7;color:#166534">Delivered</span>\')+\'</div></div>\';}).join("");}async function mark(id){await fetch(API+"/mark-delivery",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({subscription_id:id,status:"delivered"})});load();}load();</script></body></html>'
    return HTMLResponse(page)