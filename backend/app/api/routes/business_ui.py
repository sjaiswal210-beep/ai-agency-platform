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


def base_style(color="#6366f1"):
    return f'''
:root{{--p:{color};--pl:{color}15}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,-apple-system,sans-serif;background:#f8fafc;color:#1e293b;min-height:100vh;padding-bottom:70px}}
.hd{{background:#fff;border-bottom:1px solid #e2e8f0;padding:12px 16px;position:sticky;top:0;z-index:50}}
.hd-in{{max-width:640px;margin:0 auto;display:flex;align-items:center;justify-content:space-between}}
.hd h1{{font-size:.95rem;font-weight:700}}
.hd .back{{color:#64748b;text-decoration:none;font-size:1.4rem;line-height:1}}
.mn{{max-width:640px;margin:0 auto;padding:12px 16px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px}}
.st{{background:#fff;border:1px solid #f1f5f9;border-radius:10px;padding:12px;text-align:center}}
.st .n{{font-size:1.2rem;font-weight:800;color:var(--p)}}
.st .l{{font-size:.6rem;color:#94a3b8;margin-top:2px}}
.card{{background:#fff;border:1px solid #f1f5f9;border-radius:10px;margin-bottom:8px}}
.srch{{display:flex;gap:6px;margin-bottom:12px}}
.srch input{{flex:1;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;outline:none}}
.srch input:focus{{border-color:var(--p)}}
.srch select{{padding:9px;border:1px solid #e2e8f0;border-radius:8px;font-size:.75rem;background:#fff}}
.btn{{padding:9px 16px;background:var(--p);color:#fff;border:none;border-radius:8px;font-weight:600;font-size:.8rem;cursor:pointer}}
.btn:hover{{opacity:.9}}
.btn-sm{{padding:5px 10px;font-size:.7rem;border-radius:6px}}
.btn-outline{{background:none;border:1px solid #e2e8f0;color:#475569}}
.list-item{{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid #f8fafc;cursor:pointer}}
.list-item:hover{{background:#f8fafc}}
.list-item:last-child{{border:none}}
.li-name{{font-size:.82rem;font-weight:600}}
.li-meta{{font-size:.65rem;color:#94a3b8;margin-top:1px}}
.badge{{font-size:.6rem;padding:2px 8px;border-radius:10px;font-weight:600}}
.badge-blue{{background:#eff6ff;color:#3b82f6}}
.badge-green{{background:#f0fdf4;color:#22c55e}}
.badge-yellow{{background:#fffbeb;color:#d97706}}
.badge-purple{{background:#faf5ff;color:#9333ea}}
.badge-red{{background:#fef2f2;color:#ef4444}}
.modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;align-items:center;justify-content:center;padding:16px}}
.modal.show{{display:flex}}
.modal-box{{background:#fff;border-radius:14px;padding:20px;width:100%;max-width:440px;max-height:85vh;overflow-y:auto}}
.modal-box h2{{font-size:1rem;font-weight:700;margin-bottom:12px}}
.field{{margin-bottom:10px}}
.field label{{display:block;font-size:.7rem;font-weight:600;color:#64748b;margin-bottom:3px}}
.field input,.field select,.field textarea{{width:100%;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;outline:none;font-family:inherit}}
.field input:focus,.field select:focus,.field textarea:focus{{border-color:var(--p)}}
.field textarea{{resize:vertical;min-height:60px}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.empty{{text-align:center;padding:40px 16px;color:#94a3b8;font-size:.8rem}}
.tabs{{display:flex;gap:3px;background:#f1f5f9;border-radius:8px;padding:3px;margin-bottom:12px}}
.tab{{flex:1;padding:7px;border-radius:6px;font-size:.7rem;font-weight:600;text-align:center;cursor:pointer;color:#64748b}}
.tab.active{{background:#fff;color:#1e293b;box-shadow:0 1px 2px rgba(0,0,0,.05)}}
.footer{{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #e2e8f0;padding:10px 16px;max-width:640px;margin:0 auto}}
.footer .btn{{width:100%}}
.detail{{padding:14px}}
.detail h2{{font-size:1rem;font-weight:700;margin-bottom:4px}}
.detail .meta{{font-size:.72rem;color:#64748b}}
.stages{{display:flex;gap:4px;overflow-x:auto;padding:8px 0;margin:8px 0}}
.stage{{padding:5px 10px;border-radius:12px;font-size:.65rem;font-weight:600;cursor:pointer;white-space:nowrap;border:1px solid #e2e8f0;color:#64748b}}
.stage.active{{background:var(--p);color:#fff;border-color:var(--p)}}
.timeline{{margin-top:12px}}
.tl-item{{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #f8fafc}}
.tl-icon{{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.7rem;flex-shrink:0}}
.tl-body{{flex:1}}
.tl-body .title{{font-size:.78rem;font-weight:500}}
.tl-body .desc{{font-size:.65rem;color:#94a3b8;margin-top:1px}}
.tl-body .time{{font-size:.6rem;color:#cbd5e1;margin-top:2px}}
'''


@router.get("/{slug_or_id}/crm", response_class=HTMLResponse)
async def crm_full_ui(slug_or_id: str):
    org = get_org_from_slug(slug_or_id)
    if not org:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    
    org_id = org["id"]
    org_name = org["name"]
    slug = org["slug"]
    color = org.get("brand_color", "#6366f1")
    
    html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>CRM - {org_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{base_style(color)}</style>
</head><body>

<div class="hd"><div class="hd-in">
<h1>&#128101; CRM</h1>
<a href="/api/panel/{{website_id}}" class="back" onclick="history.back();return false">&times;</a>
</div></div>

<div class="mn">
<!-- Stats -->
<div class="stats" id="stats"><div class="st"><div class="n">-</div><div class="l">Total</div></div><div class="st"><div class="n">-</div><div class="l">Leads</div></div><div class="st"><div class="n">-</div><div class="l">Customers</div></div></div>

<!-- Search + Filter -->
<div class="srch">
<input type="text" id="search" placeholder="Search contacts..." onkeydown="if(event.key==='Enter')loadContacts()">
<select id="filterType" onchange="loadContacts()"><option value="">All</option><option value="lead">Leads</option><option value="customer">Customers</option><option value="vendor">Vendors</option></select>
<button class="btn btn-sm" onclick="showAdd()">+ Add</button>
</div>

<!-- Tabs -->
<div class="tabs">
<div class="tab active" onclick="showSection('list',this)">Contacts</div>
<div class="tab" onclick="showSection('pipeline',this)">Pipeline</div>
</div>

<!-- Contact List -->
<div id="sec-list">
<div class="card" id="contactList"><div class="empty">Loading...</div></div>
</div>

<!-- Pipeline View -->
<div id="sec-pipeline" style="display:none">
<div id="pipelineView"><div class="empty">Loading pipeline...</div></div>
</div>

<!-- Contact Detail (hidden initially) -->
<div id="sec-detail" style="display:none">
<div class="card detail" id="detailView"></div>
</div>
</div>

<!-- Add Contact Modal -->
<div class="modal" id="addModal">
<div class="modal-box">
<h2>Add Contact</h2>
<div class="field"><label>Name *</label><input id="f_name" placeholder="Contact name"></div>
<div class="row">
<div class="field"><label>Phone</label><input id="f_phone" type="tel" placeholder="9876543210"></div>
<div class="field"><label>Email</label><input id="f_email" type="email" placeholder="email@example.com"></div>
</div>
<div class="row">
<div class="field"><label>Type</label><select id="f_type"><option value="lead">Lead</option><option value="customer">Customer</option><option value="vendor">Vendor</option><option value="partner">Partner</option></select></div>
<div class="field"><label>Source</label><input id="f_source" placeholder="Google, Referral..."></div>
</div>
<div class="field"><label>Company</label><input id="f_company" placeholder="Company name"></div>
<div class="field"><label>Notes</label><textarea id="f_notes" placeholder="Any notes..."></textarea></div>
<div style="display:flex;gap:8px;margin-top:12px">
<button class="btn" onclick="saveContact()" style="flex:1">Save Contact</button>
<button class="btn btn-outline" onclick="closeModal('addModal')" style="flex:.5">Cancel</button>
</div>
</div>
</div>

<!-- Add Activity Modal -->
<div class="modal" id="actModal">
<div class="modal-box">
<h2>Add Activity</h2>
<div class="field"><label>Type</label>
<div style="display:flex;gap:4px;flex-wrap:wrap" id="actTypes">
<span class="stage active" onclick="selectActType(this,'note')">Note</span>
<span class="stage" onclick="selectActType(this,'call')">Call</span>
<span class="stage" onclick="selectActType(this,'meeting')">Meeting</span>
<span class="stage" onclick="selectActType(this,'task')">Task</span>
<span class="stage" onclick="selectActType(this,'whatsapp')">WhatsApp</span>
</div></div>
<div class="field"><label>Title *</label><input id="a_title" placeholder="e.g., Follow-up call done"></div>
<div class="field"><label>Notes</label><textarea id="a_desc" placeholder="Details..."></textarea></div>
<div style="display:flex;gap:8px;margin-top:12px">
<button class="btn" onclick="saveActivity()" style="flex:1">Save</button>
<button class="btn btn-outline" onclick="closeModal('actModal')" style="flex:.5">Cancel</button>
</div>
</div>
</div>

<script>
var API = "/api/org/{org_id}/crm";
var contacts = [];
var currentContact = null;
var actType = "note";
var STAGES = ["new","contacted","qualified","proposal","won","lost"];
var STAGE_COLORS = {{"new":"badge-blue","contacted":"badge-yellow","qualified":"badge-purple","proposal":"badge-yellow","won":"badge-green","lost":"badge-red"}};

// Load
loadContacts();
loadStats();

function showSection(name, btn) {{
  document.querySelectorAll("[id^=sec-]").forEach(s=>s.style.display="none");
  document.getElementById("sec-"+name).style.display="block";
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  if(btn)btn.classList.add("active");
  if(name==="pipeline")loadPipeline();
}}

async function loadStats() {{
  var r = await fetch(API+"/dashboard");
  var d = await r.json();
  var byType = d.by_type||{{}};
  document.getElementById("stats").innerHTML =
    '<div class="st"><div class="n">'+(d.total_contacts||0)+'</div><div class="l">Total</div></div>'+
    '<div class="st"><div class="n">'+(byType.lead||0)+'</div><div class="l">Leads</div></div>'+
    '<div class="st"><div class="n">'+(byType.customer||0)+'</div><div class="l">Customers</div></div>';
}}

async function loadContacts() {{
  var search = document.getElementById("search").value;
  var type = document.getElementById("filterType").value;
  var url = API+"/contacts?limit=100";
  if(search) url+="&search="+encodeURIComponent(search);
  if(type) url+="&type="+type;
  var r = await fetch(url);
  var d = await r.json();
  contacts = d.contacts||[];
  renderList();
}}

function renderList() {{
  var el = document.getElementById("contactList");
  if(contacts.length===0){{ el.innerHTML='<div class="empty">No contacts yet. Tap + Add to start.</div>'; return; }}
  el.innerHTML = contacts.map(function(c){{
    var badge = '<span class="badge '+STAGE_COLORS[c.stage]+'">'+c.stage+'</span>';
    return '<div class="list-item" onclick="viewContact(\''+c.id+'\')"><div><div class="li-name">'+c.name+'</div><div class="li-meta">'+(c.phone||c.email||c.company||"")+'</div></div><div>'+badge+'</div></div>';
  }}).join("");
}}

async function loadPipeline() {{
  var url = API+"/contacts?limit=200";
  var r = await fetch(url);
  var d = await r.json();
  var all = d.contacts||[];
  var html = "";
  STAGES.forEach(function(stage){{
    var items = all.filter(function(c){{return c.stage===stage}});
    html += '<div style="margin-bottom:12px"><div style="font-size:.7rem;font-weight:700;color:#64748b;text-transform:uppercase;margin-bottom:6px">'+stage.replace("_"," ")+' ('+items.length+')</div>';
    items.forEach(function(c){{
      html += '<div class="list-item" style="border:1px solid #f1f5f9;border-radius:8px;margin-bottom:4px" onclick="viewContact(\''+c.id+'\')"><div><div class="li-name">'+c.name+'</div><div class="li-meta">'+(c.phone||"")+'</div></div></div>';
    }});
    html += '</div>';
  }});
  document.getElementById("pipelineView").innerHTML = html||'<div class="empty">No contacts</div>';
}}

async function viewContact(id) {{
  var r = await fetch(API+"/contacts/"+id);
  currentContact = await r.json();
  var c = currentContact;
  // Load activities
  var ar = await fetch(API+"/contacts/"+id+"/activities");
  var ad = await ar.json();
  var activities = ad.activities||[];
  
  var stagesHtml = STAGES.map(function(s){{
    return '<span class="stage'+(c.stage===s?' active':'')+'" onclick="changeStage(\''+id+'\',\''+s+'\')">'+s+'</span>';
  }}).join("");
  
  var tlHtml = activities.map(function(a){{
    var icon = a.type==="call"?"&#128222;":a.type==="meeting"?"&#128197;":a.type==="whatsapp"?"&#128172;":"&#128221;";
    var bg = a.type==="call"?"#f0fdf4":a.type==="meeting"?"#eff6ff":"#fffbeb";
    return '<div class="tl-item"><div class="tl-icon" style="background:'+bg+'">'+icon+'</div><div class="tl-body"><div class="title">'+(a.title||a.type)+'</div>'+(a.description?'<div class="desc">'+a.description+'</div>':'')+'<div class="time">'+new Date(a.created_at).toLocaleDateString("en-IN",{{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"}})+'</div></div></div>';
  }}).join("")||'<div class="empty" style="padding:16px">No activities yet</div>';
  
  document.getElementById("detailView").innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:start">
      <div><h2>${{c.name}}</h2><div class="meta">${{c.phone||""}} ${{c.email?" &middot; "+c.email:""}} ${{c.company?" &middot; "+c.company:""}}</div></div>
      <button class="btn btn-sm btn-outline" onclick="showSection('list');loadContacts()">Back</button>
    </div>
    <div class="stages">${{stagesHtml}}</div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">
      <span style="font-size:.75rem;font-weight:600;color:#475569">Activity</span>
      <button class="btn btn-sm" onclick="showActModal()">+ Add</button>
    </div>
    <div class="timeline">${{tlHtml}}</div>
  `;
  showSection("detail");
}}

async function changeStage(id, stage) {{
  await fetch(API+"/contacts/"+id,{{method:"PUT",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{stage:stage}})}});
  viewContact(id);
  loadStats();
}}

function showAdd(){{ document.getElementById("addModal").classList.add("show"); }}
function showActModal(){{ document.getElementById("actModal").classList.add("show"); }}
function closeModal(id){{ document.getElementById(id).classList.remove("show"); }}

async function saveContact() {{
  var name = document.getElementById("f_name").value.trim();
  if(!name){{ alert("Name required"); return; }}
  await fetch(API+"/contacts",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{
    name: name,
    phone: document.getElementById("f_phone").value,
    email: document.getElementById("f_email").value,
    type: document.getElementById("f_type").value,
    source: document.getElementById("f_source").value,
    company: document.getElementById("f_company").value,
    notes: document.getElementById("f_notes").value,
  }})}});
  closeModal("addModal");
  document.getElementById("f_name").value="";document.getElementById("f_phone").value="";document.getElementById("f_email").value="";
  document.getElementById("f_company").value="";document.getElementById("f_notes").value="";document.getElementById("f_source").value="";
  loadContacts(); loadStats();
}}

function selectActType(el, type) {{
  document.querySelectorAll("#actTypes .stage").forEach(s=>s.classList.remove("active"));
  el.classList.add("active");
  actType = type;
}}

async function saveActivity() {{
  var title = document.getElementById("a_title").value.trim();
  if(!title||!currentContact){{ alert("Title required"); return; }}
  await fetch(API+"/contacts/"+currentContact.id+"/activities",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{
    type: actType, title: title, description: document.getElementById("a_desc").value,
  }})}});
  closeModal("actModal");
  document.getElementById("a_title").value="";document.getElementById("a_desc").value="";
  viewContact(currentContact.id);
}}
</script>
</body></html>'''
    return HTMLResponse(content=html)


@router.get("/{slug_or_id}/billing", response_class=HTMLResponse)
async def billing_full_ui(slug_or_id: str):
    org = get_org_from_slug(slug_or_id)
    if not org:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    org_id = org["id"]
    org_name = org["name"]
    color = org.get("brand_color", "#10b981")

    html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Billing - {org_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{base_style(color)}</style>
</head><body>
<div class="hd"><div class="hd-in"><h1>&#129534; Billing</h1><a href="#" class="back" onclick="history.back();return false">&times;</a></div></div>
<div class="mn">
<div class="stats" id="stats" style="grid-template-columns:repeat(4,1fr)"><div class="st"><div class="n">-</div><div class="l">Revenue</div></div><div class="st"><div class="n">-</div><div class="l">Expenses</div></div><div class="st"><div class="n">-</div><div class="l">Pending</div></div><div class="st"><div class="n">-</div><div class="l">Net</div></div></div>

<div class="srch">
<select id="filterType" onchange="loadInvoices()"><option value="">All</option><option value="invoice">Invoices</option><option value="quotation">Quotations</option></select>
<select id="filterStatus" onchange="loadInvoices()"><option value="">All Status</option><option value="draft">Draft</option><option value="sent">Sent</option><option value="paid">Paid</option><option value="overdue">Overdue</option></select>
<button class="btn btn-sm" onclick="showAdd()">+ New</button>
</div>

<div class="card" id="invoiceList"><div class="empty">Loading...</div></div>
</div>

<!-- Create Invoice Modal -->
<div class="modal" id="addModal"><div class="modal-box">
<h2>Create Invoice</h2>
<div class="row" style="margin-bottom:10px">
<button class="btn" id="btnInv" onclick="setInvType('invoice')" style="flex:1">Invoice</button>
<button class="btn btn-outline" id="btnQot" onclick="setInvType('quotation')" style="flex:1">Quotation</button>
</div>
<div id="lineItems">
<div class="field"><label>Line Items</label></div>
<div class="li-row" style="display:flex;gap:4px;margin-bottom:6px"><input class="li-name" placeholder="Item name" style="flex:2;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:.8rem"><input class="li-qty" type="number" value="1" min="1" style="width:50px;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:.8rem;text-align:center"><input class="li-price" type="number" placeholder="Price" style="width:80px;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:.8rem;text-align:right"></div>
</div>
<button class="btn btn-outline btn-sm" onclick="addLineItem()" style="margin-bottom:10px">+ Add item</button>
<div style="background:#f8fafc;border-radius:8px;padding:10px;margin-bottom:10px;display:flex;justify-content:space-between"><span style="font-size:.8rem;color:#64748b">Subtotal</span><span id="subtotal" style="font-size:1rem;font-weight:700">&#8377;0</span></div>
<div class="row">
<div class="field"><label>Due Date</label><input id="f_due" type="date"></div>
<div class="field"><label>Notes</label><input id="f_notes" placeholder="Thank you!"></div>
</div>
<div style="display:flex;gap:8px;margin-top:12px">
<button class="btn" onclick="saveInvoice()" style="flex:1">Create</button>
<button class="btn btn-outline" onclick="closeModal('addModal')" style="flex:.4">Cancel</button>
</div>
</div></div>

<script>
var API = "/api/org/{org_id}/billing";
var invType = "invoice";

loadStats(); loadInvoices();

async function loadStats() {{
  var r = await fetch(API+"/dashboard"); var d = await r.json();
  document.getElementById("stats").innerHTML =
    '<div class="st"><div class="n">&#8377;'+(d.total_revenue||0).toLocaleString("en-IN")+'</div><div class="l">Revenue</div></div>'+
    '<div class="st"><div class="n">&#8377;'+(d.total_expenses||0).toLocaleString("en-IN")+'</div><div class="l">Expenses</div></div>'+
    '<div class="st"><div class="n">&#8377;'+(d.total_pending||0).toLocaleString("en-IN")+'</div><div class="l">Pending</div></div>'+
    '<div class="st"><div class="n">&#8377;'+(d.net_income||0).toLocaleString("en-IN")+'</div><div class="l">Net</div></div>';
}}

async function loadInvoices() {{
  var type = document.getElementById("filterType").value;
  var status = document.getElementById("filterStatus").value;
  var url = API+"/invoices?limit=50";
  if(type) url+="&type="+type;
  if(status) url+="&status="+status;
  var r = await fetch(url); var d = await r.json();
  var inv = d.invoices||[];
  if(inv.length===0){{ document.getElementById("invoiceList").innerHTML='<div class="empty">No invoices yet. Create your first one!</div>'; return; }}
  document.getElementById("invoiceList").innerHTML = inv.map(function(i){{
    var statusColors = {{"draft":"badge-blue","sent":"badge-blue","paid":"badge-green","overdue":"badge-red","partially_paid":"badge-yellow"}};
    return '<div class="list-item"><div><div class="li-name">'+i.invoice_number+'</div><div class="li-meta">'+(i.crm_contacts?i.crm_contacts.name:"")+" &middot; "+new Date(i.created_at).toLocaleDateString("en-IN",{{day:"numeric",month:"short"}})+'</div></div><div style="text-align:right"><div style="font-size:.85rem;font-weight:700">&#8377;'+Number(i.total).toLocaleString("en-IN")+'</div><span class="badge '+(statusColors[i.status]||"badge-blue")+'">'+i.status+'</span></div></div>';
  }}).join("");
}}

function setInvType(type) {{
  invType = type;
  document.getElementById("btnInv").className = type==="invoice"?"btn":"btn btn-outline";
  document.getElementById("btnQot").className = type==="quotation"?"btn":"btn btn-outline";
}}

function addLineItem() {{
  var row = document.createElement("div");
  row.className="li-row";row.style.cssText="display:flex;gap:4px;margin-bottom:6px";
  row.innerHTML='<input class="li-name" placeholder="Item" style="flex:2;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:.8rem"><input class="li-qty" type="number" value="1" min="1" style="width:50px;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:.8rem;text-align:center"><input class="li-price" type="number" placeholder="Price" style="width:80px;padding:8px;border:1px solid #e2e8f0;border-radius:6px;font-size:.8rem;text-align:right"><button onclick="this.parentElement.remove();calcTotal()" style="border:none;background:none;color:#ef4444;cursor:pointer;font-size:1rem">&#10005;</button>';
  document.getElementById("lineItems").appendChild(row);
  row.querySelectorAll("input").forEach(function(i){{i.addEventListener("input",calcTotal)}});
}}

function calcTotal() {{
  var rows = document.querySelectorAll(".li-row");
  var total = 0;
  rows.forEach(function(row){{
    var qty = parseInt(row.querySelector(".li-qty").value)||1;
    var price = parseFloat(row.querySelector(".li-price").value)||0;
    total += qty * price;
  }});
  document.getElementById("subtotal").textContent = "\\u20B9"+total.toLocaleString("en-IN");
}}
document.querySelectorAll(".li-row input").forEach(function(i){{i.addEventListener("input",calcTotal)}});

function showAdd(){{ document.getElementById("addModal").classList.add("show"); }}
function closeModal(id){{ document.getElementById(id).classList.remove("show"); }}

async function saveInvoice() {{
  var rows = document.querySelectorAll(".li-row");
  var items = [];
  rows.forEach(function(row){{
    var name = row.querySelector(".li-name").value.trim();
    var qty = parseInt(row.querySelector(".li-qty").value)||1;
    var price = parseFloat(row.querySelector(".li-price").value)||0;
    if(name && price) items.push({{name:name,quantity:qty,price:price}});
  }});
  if(items.length===0){{ alert("Add at least one item"); return; }}
  await fetch(API+"/invoices",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{
    type: invType, items: items, due_date: document.getElementById("f_due").value||undefined, notes: document.getElementById("f_notes").value,
  }})}});
  closeModal("addModal");
  loadInvoices(); loadStats();
}}
</script>
</body></html>'''
    return HTMLResponse(content=html)


@router.get("/{slug_or_id}/{module_id}", response_class=HTMLResponse)
async def generic_module_ui(slug_or_id: str, module_id: str):
    """Generic interactive UI for any module with dashboard + add form."""
    org = get_org_from_slug(slug_or_id)
    if not org:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    org_id = org["id"]
    org_name = org["name"]
    color = org.get("brand_color", "#6366f1")
    
    # Module configs
    MODULES = {
        "booking": {"name": "Booking", "emoji": "&#128197;", "api": f"/api/org/{org_id}/booking", "list_key": "appointments", "add_fields": [("customer_name","Customer Name","text",True),("customer_phone","Phone","tel",False),("date","Date","date",True),("start_time","Time","time",True),("notes","Notes","text",False)]},
        "subscriptions": {"name": "Subscriptions", "emoji": "&#128257;", "api": f"/api/org/{org_id}/subscriptions", "list_key": "subscriptions", "add_fields": [("customer_name","Customer Name","text",True),("customer_phone","Phone","tel",True),("address","Address","text",False),("product_name","Product","text",True),("quantity","Qty","number",False),("price_per_unit","Price/Unit","number",True),("frequency","Frequency","select:daily,alternate,weekdays,weekly",False)]},
        "job_cards": {"name": "Job Cards", "emoji": "&#128295;", "api": f"/api/org/{org_id}/job-cards", "list_key": "job_cards", "add_fields": [("customer_name","Customer Name","text",True),("customer_phone","Phone","tel",False),("device_type","Type","select:vehicle_2w,vehicle_4w,mobile,laptop,appliance,electrical,plumbing,ac_hvac,other",False),("device_brand","Brand/Make","text",False),("device_model","Model","text",False),("problem_description","Problem","textarea",True),("estimated_cost","Est. Cost","number",False)]},
        "custom_orders": {"name": "Custom Orders", "emoji": "&#128203;", "api": f"/api/org/{org_id}/custom-orders", "list_key": "orders", "add_fields": [("customer_name","Customer Name","text",True),("customer_phone","Phone","tel",False),("item_description","Item Description","textarea",True),("material","Material","text",False),("material_cost","Material Cost","number",False),("making_charges","Making Charges","number",False),("promised_date","Delivery Date","date",False)]},
        "clinic": {"name": "Clinic", "emoji": "&#129657;", "api": f"/api/org/{org_id}/clinic", "list_key": "patients", "add_fields": [("name","Patient Name","text",True),("phone","Phone","tel",False),("age","Age","number",False),("gender","Gender","select:male,female,other",False),("blood_group","Blood Group","text",False),("medical_history","Medical History","textarea",False)]},
        "students": {"name": "Students", "emoji": "&#127891;", "api": f"/api/org/{org_id}/students", "list_key": "students", "add_fields": [("name","Student Name","text",True),("phone","Phone","tel",False),("parent_phone","Parent Phone","tel",False),("email","Email","email",False),("date_of_birth","Date of Birth","date",False)]},
        "events": {"name": "Events", "emoji": "&#127881;", "api": f"/api/org/{org_id}/events", "list_key": "bookings", "add_fields": [("client_name","Client Name","text",True),("client_phone","Phone","tel",False),("event_type","Event Type","select:wedding,reception,birthday,corporate,engagement,anniversary,other",False),("event_date","Event Date","date",True),("guest_count","Guests","number",False),("total_amount","Total Amount","number",False),("advance_paid","Advance Paid","number",False)]},
        "fleet": {"name": "Fleet", "emoji": "&#128663;", "api": f"/api/org/{org_id}/fleet", "list_key": "vehicles", "add_fields": [("vehicle_number","Vehicle Number","text",True),("type","Type","select:car,bike,auto,truck,van,bus,other",False),("make","Make","text",False),("model","Model","text",False),("fuel_type","Fuel","select:petrol,diesel,cng,electric",False)]},
        "reminders": {"name": "Reminders", "emoji": "&#128276;", "api": f"/api/org/{org_id}/reminders", "list_key": "reminders", "add_fields": [("customer_name","Customer Name","text",True),("customer_phone","Phone","tel",True),("type","Type","select:insurance,vehicle_service,amc,warranty,checkup,subscription,followup,general",False),("item_description","Description","text",False),("due_date","Due Date","date",True),("recurrence","Repeat","select:none,monthly,quarterly,half_yearly,yearly",False)]},
        "inventory": {"name": "Inventory", "emoji": "&#128230;", "api": f"/api/org/{org_id}/inventory", "list_key": "products", "add_fields": [("name","Product Name","text",True),("sku","SKU","text",False),("price","Sell Price","number",True),("cost_price","Cost Price","number",False),("stock_quantity","Stock Qty","number",False),("unit","Unit","select:pcs,kg,ltr,box,pack,mtr",False)]},
    }
    
    config = MODULES.get(module_id)
    if not config:
        return HTMLResponse(f"<h2>Module '{module_id}' UI not available yet.</h2><p><a href='javascript:history.back()'>Go back</a></p>")
    
    # Build form fields HTML
    fields_html = ""
    for (fid, label, ftype, required) in config["add_fields"]:
        req = " *" if required else ""
        if ftype.startswith("select:"):
            options = ftype.split(":")[1].split(",")
            opts = "".join([f'<option value="{o}">{o.replace("_"," ").title()}</option>' for o in options])
            fields_html += f'<div class="field"><label>{label}{req}</label><select id="f_{fid}">{opts}</select></div>'
        elif ftype == "textarea":
            fields_html += f'<div class="field"><label>{label}{req}</label><textarea id="f_{fid}" placeholder="{label}"></textarea></div>'
        else:
            fields_html += f'<div class="field"><label>{label}{req}</label><input id="f_{fid}" type="{ftype}" placeholder="{label}"></div>'
    
    # Build JS field collection
    fields_js = ",".join([f'"{fid}":document.getElementById("f_{fid}").value' for (fid,_,_,_) in config["add_fields"]])
    required_checks = " || ".join([f'!document.getElementById("f_{fid}").value.trim()' for (fid,_,_,req) in config["add_fields"] if req])
    
    api_url = config["api"]
    list_endpoint = f'{api_url}/{"patients" if module_id=="clinic" else "vehicles" if module_id=="fleet" else ""}'
    if module_id == "clinic": list_endpoint = f'{api_url}/patients'
    elif module_id == "fleet": list_endpoint = f'{api_url}/vehicles'
    elif module_id == "booking": list_endpoint = f'{api_url}/appointments'
    elif module_id == "events": list_endpoint = f'{api_url}/bookings'
    elif module_id == "inventory": list_endpoint = f'{api_url}/products'
    else: list_endpoint = api_url
    
    # Create endpoint
    create_endpoint = list_endpoint
    if module_id == "booking": create_endpoint = f'{api_url}/appointments'
    elif module_id == "fleet": create_endpoint = f'{api_url}/vehicles'
    elif module_id == "inventory": create_endpoint = f'{api_url}/products'
    elif module_id == "clinic": create_endpoint = f'{api_url}/patients'
    elif module_id == "students": create_endpoint = api_url
    elif module_id == "events": create_endpoint = f'{api_url}/bookings'
    elif module_id == "reminders": create_endpoint = api_url

    html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{config["name"]} - {org_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{base_style(color)}</style>
</head><body>
<div class="hd"><div class="hd-in"><h1>{config["emoji"]} {config["name"]}</h1><a href="#" class="back" onclick="history.back();return false">&times;</a></div></div>
<div class="mn">
<div class="stats" id="stats"><div class="st"><div class="n">-</div><div class="l">Loading...</div></div></div>
<div style="display:flex;justify-content:flex-end;margin-bottom:10px"><button class="btn btn-sm" onclick="showAdd()">+ Add New</button></div>
<div class="card" id="mainList"><div class="empty">Loading...</div></div>
</div>

<div class="modal" id="addModal"><div class="modal-box">
<h2>Add {config["name"]}</h2>
{fields_html}
<div style="display:flex;gap:8px;margin-top:14px">
<button class="btn" onclick="saveItem()" style="flex:1">Save</button>
<button class="btn btn-outline" onclick="closeModal()" style="flex:.4">Cancel</button>
</div>
</div></div>

<script>
var API_DASH = "{api_url}/dashboard";
var API_LIST = "{list_endpoint}";
var API_CREATE = "{create_endpoint}";
var LIST_KEY = "{config["list_key"]}";

loadDash(); loadList();

async function loadDash() {{
  try {{
    var r = await fetch(API_DASH); var d = await r.json();
    var html = "";
    Object.entries(d).slice(0,4).forEach(function(e){{
      var lbl = e[0].replace(/_/g," ").replace(/\\b\\w/g,function(c){{return c.toUpperCase()}});
      var val = typeof e[1]==="number"?(e[1]>999?"\\u20B9"+e[1].toLocaleString("en-IN"):e[1]):JSON.stringify(e[1]).substring(0,20);
      html += '<div class="st"><div class="n">'+val+'</div><div class="l">'+lbl+'</div></div>';
    }});
    document.getElementById("stats").innerHTML = html;
  }} catch(e){{}}
}}

async function loadList() {{
  try {{
    var r = await fetch(API_LIST+"?limit=50"); var d = await r.json();
    var items = d[LIST_KEY] || d.items || d.data || [];
    if(!Array.isArray(items)) items = Object.values(d)[0];
    if(!items||items.length===0){{ document.getElementById("mainList").innerHTML='<div class="empty">No records yet. Add your first one!</div>'; return; }}
    document.getElementById("mainList").innerHTML = items.map(function(item){{
      var name = item.customer_name||item.name||item.client_name||item.vehicle_number||item.title||"Record";
      var meta = item.phone||item.customer_phone||item.client_phone||item.status||item.type||item.due_date||"";
      var badge = item.status?'<span class="badge badge-blue">'+item.status+'</span>':"";
      return '<div class="list-item"><div><div class="li-name">'+name+'</div><div class="li-meta">'+meta+'</div></div>'+badge+'</div>';
    }}).join("");
  }} catch(e){{ document.getElementById("mainList").innerHTML='<div class="empty">Error loading</div>'; }}
}}

function showAdd(){{ document.getElementById("addModal").classList.add("show"); }}
function closeModal(){{ document.getElementById("addModal").classList.remove("show"); }}

async function saveItem() {{
  if({required_checks}){{ alert("Fill required fields"); return; }}
  var body = {{{fields_js}}};
  // Convert number fields
  Object.keys(body).forEach(function(k){{
    if(body[k]&&!isNaN(body[k])&&k!=="customer_phone"&&k!=="phone"&&k!=="parent_phone"&&k!=="vehicle_number") body[k]=Number(body[k]);
  }});
  await fetch(API_CREATE,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(body)}});
  closeModal();
  // Clear fields
  document.querySelectorAll("#addModal input, #addModal textarea, #addModal select").forEach(function(el){{if(el.type!=="button")el.value="";}});
  loadList(); loadDash();
}}
</script>
</body></html>'''
    return HTMLResponse(content=html)
