from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/biz", tags=["business-ui-crm"])


@router.get("/{slug_or_id}/crm", response_class=HTMLResponse)
async def crm_full_ui(slug_or_id: str):
    """Full CRM interface - contacts, pipeline, activities."""
    db = get_supabase()
    org = db.table("organizations").select("id, name, slug").eq("slug", slug_or_id).limit(1).execute()
    if not org.data:
        org = db.table("organizations").select("id, name, slug").eq("id", slug_or_id).limit(1).execute()
    if not org.data:
        return HTMLResponse("<h2>Business not found</h2>", status_code=404)
    
    org_id = org.data[0]["id"]
    org_name = org.data[0]["name"]
    slug = org.data[0]["slug"]
    
    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>CRM - {org_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#f8fafc;color:#1e293b;min-height:100vh;padding-bottom:70px}}
.header{{background:#fff;border-bottom:1px solid #e2e8f0;padding:12px 16px;position:sticky;top:0;z-index:50}}
.header-inner{{max-width:700px;margin:0 auto;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:1rem;font-weight:700}}
.header .back{{color:#64748b;text-decoration:none;font-size:1.3rem}}
.header .add-btn{{background:#6366f1;color:#fff;border:none;padding:6px 14px;border-radius:8px;font-size:.75rem;font-weight:600;cursor:pointer}}
.main{{max-width:700px;margin:0 auto;padding:12px 16px}}
.search-row{{display:flex;gap:8px;margin-bottom:12px}}
.search{{flex:1;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;outline:none}}
.search:focus{{border-color:#6366f1}}
.filter{{padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:.75rem;background:#fff;cursor:pointer}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}}
.stat{{background:#fff;border:1px solid #f1f5f9;border-radius:10px;padding:10px;text-align:center}}
.stat .n{{font-size:1.1rem;font-weight:800;color:#6366f1}}
.stat .l{{font-size:.55rem;color:#64748b;margin-top:2px}}
.contact-list{{background:#fff;border:1px solid #f1f5f9;border-radius:12px;overflow:hidden}}
.contact{{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid #f8fafc;cursor:pointer;transition:background .15s}}
.contact:hover{{background:#f8fafc}}
.contact:last-child{{border:none}}
.contact .info .name{{font-size:.8rem;font-weight:600}}
.contact .info .meta{{font-size:.65rem;color:#94a3b8;margin-top:2px}}
.contact .right{{display:flex;align-items:center;gap:6px}}
.badge{{font-size:.55rem;padding:2px 6px;border-radius:8px;font-weight:600}}
.badge-lead{{background:#dbeafe;color:#2563eb}}
.badge-customer{{background:#dcfce7;color:#16a34a}}
.badge-new{{background:#e0e7ff;color:#4f46e5}}
.badge-contacted{{background:#fef9c3;color:#a16207}}
.badge-won{{background:#dcfce7;color:#16a34a}}
.empty{{text-align:center;padding:40px 20px;color:#94a3b8;font-size:.8rem}}
.modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;align-items:center;justify-content:center;padding:16px}}
.modal.show{{display:flex}}
.modal-content{{background:#fff;border-radius:16px;padding:20px;width:100%;max-width:420px;max-height:85vh;overflow-y:auto}}
.modal h2{{font-size:1rem;font-weight:700;margin-bottom:12px}}
.form-group{{margin-bottom:10px}}
.form-group label{{font-size:.7rem;font-weight:600;color:#64748b;display:block;margin-bottom:3px}}
.form-group input,.form-group select,.form-group textarea{{width:100%;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;outline:none;font-family:inherit}}
.form-group input:focus,.form-group select:focus{{border-color:#6366f1}}
.form-row{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.btn{{width:100%;padding:11px;border:none;border-radius:10px;font-weight:700;font-size:.8rem;cursor:pointer;margin-top:8px}}
.btn-primary{{background:#6366f1;color:#fff}}
.btn-danger{{background:#fee2e2;color:#dc2626;margin-top:6px}}
.btn-secondary{{background:#f1f5f9;color:#475569}}
.close-btn{{position:absolute;top:12px;right:14px;background:none;border:none;font-size:1.3rem;cursor:pointer;color:#94a3b8}}
.pipeline{{display:flex;gap:4px;margin-bottom:12px;overflow-x:auto;padding-bottom:4px}}
.pipe-btn{{padding:6px 12px;border-radius:16px;font-size:.65rem;font-weight:600;border:1px solid #e2e8f0;background:#fff;color:#64748b;cursor:pointer;white-space:nowrap}}
.pipe-btn.active{{background:#6366f1;color:#fff;border-color:#6366f1}}
.detail-panel{{background:#fff;border:1px solid #f1f5f9;border-radius:12px;padding:16px;margin-bottom:12px;display:none}}
.detail-panel.show{{display:block}}
.activity{{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #f8fafc}}
.activity:last-child{{border:none}}
.activity .dot{{width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0}}
.activity .text{{font-size:.75rem}}
.activity .time{{font-size:.6rem;color:#94a3b8;margin-top:2px}}
.tabs{{display:flex;gap:4px;margin-bottom:12px;background:#f1f5f9;border-radius:8px;padding:3px}}
.tab{{flex:1;padding:7px;border-radius:6px;font-size:.7rem;font-weight:600;text-align:center;cursor:pointer;color:#64748b}}
.tab.active{{background:#fff;color:#1e293b;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
</style></head><body>

<div class="header"><div class="header-inner">
<h1>&#128101; CRM</h1>
<div style="display:flex;gap:8px;align-items:center">
<span style="font-size:.7rem;color:#94a3b8" id="countLabel">0 contacts</span>
<button class="add-btn" onclick="showAddModal()">+ Add</button>
</div>
</div></div>

<div class="main">
<!-- Stats -->
<div class="stats" id="statsRow"></div>

<!-- Search + Filter -->
<div class="search-row">
<input class="search" id="searchInput" placeholder="Search name, phone..." oninput="searchContacts()">
<select class="filter" id="typeFilter" onchange="loadContacts()">
<option value="">All Types</option>
<option value="lead">Leads</option>
<option value="customer">Customers</option>
<option value="vendor">Vendors</option>
</select>
</div>

<!-- Pipeline filter -->
<div class="pipeline" id="pipelineBar">
<button class="pipe-btn active" onclick="filterStage('',this)">All</button>
<button class="pipe-btn" onclick="filterStage('new',this)">New</button>
<button class="pipe-btn" onclick="filterStage('contacted',this)">Contacted</button>
<button class="pipe-btn" onclick="filterStage('qualified',this)">Qualified</button>
<button class="pipe-btn" onclick="filterStage('proposal',this)">Proposal</button>
<button class="pipe-btn" onclick="filterStage('won',this)">Won</button>
<button class="pipe-btn" onclick="filterStage('lost',this)">Lost</button>
</div>

<!-- Contact List -->
<div class="contact-list" id="contactList">
<div class="empty" id="emptyState">Loading...</div>
</div>

<!-- Detail Panel -->
<div class="detail-panel" id="detailPanel">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
<h3 id="detailName" style="font-size:.9rem;font-weight:700"></h3>
<button onclick="closeDetail()" style="background:none;border:none;font-size:1.1rem;cursor:pointer;color:#94a3b8">&times;</button>
</div>
<div id="detailInfo" style="font-size:.75rem;color:#64748b;margin-bottom:10px"></div>
<div class="tabs">
<div class="tab active" onclick="showDetailTab('activities',this)">Activities</div>
<div class="tab" onclick="showDetailTab('actions',this)">Actions</div>
</div>
<div id="activitiesTab">
<div id="activityList"></div>
<div style="margin-top:10px">
<select id="actType" style="padding:6px;border:1px solid #e2e8f0;border-radius:6px;font-size:.7rem;margin-right:4px">
<option value="note">Note</option><option value="call">Call</option><option value="meeting">Meeting</option><option value="whatsapp">WhatsApp</option>
</select>
<input id="actTitle" placeholder="Activity note..." style="padding:6px 10px;border:1px solid #e2e8f0;border-radius:6px;font-size:.75rem;width:55%">
<button onclick="addActivity()" style="padding:6px 12px;background:#6366f1;color:#fff;border:none;border-radius:6px;font-size:.7rem;font-weight:600;cursor:pointer">Add</button>
</div>
</div>
<div id="actionsTab" style="display:none">
<button class="btn btn-secondary" onclick="editContact()">Edit Contact</button>
<button class="btn btn-danger" onclick="deleteContact()">Delete Contact</button>
</div>
</div>
</div>

<!-- Add/Edit Modal -->
<div class="modal" id="addModal">
<div class="modal-content" style="position:relative">
<button class="close-btn" onclick="closeModal()">&times;</button>
<h2 id="modalTitle">Add Contact</h2>
<div class="form-group"><label>Name *</label><input id="fName" placeholder="Full name"></div>
<div class="form-row">
<div class="form-group"><label>Phone</label><input id="fPhone" placeholder="9876543210" type="tel"></div>
<div class="form-group"><label>Email</label><input id="fEmail" placeholder="email@..." type="email"></div>
</div>
<div class="form-row">
<div class="form-group"><label>Type</label><select id="fType"><option value="lead">Lead</option><option value="customer">Customer</option><option value="vendor">Vendor</option><option value="partner">Partner</option></select></div>
<div class="form-group"><label>Stage</label><select id="fStage"><option value="new">New</option><option value="contacted">Contacted</option><option value="qualified">Qualified</option><option value="proposal">Proposal</option><option value="won">Won</option><option value="lost">Lost</option></select></div>
</div>
<div class="form-row">
<div class="form-group"><label>Company</label><input id="fCompany" placeholder="Company name"></div>
<div class="form-group"><label>Source</label><input id="fSource" placeholder="Google, Referral..."></div>
</div>
<div class="form-group"><label>Notes</label><textarea id="fNotes" rows="2" placeholder="Any notes..."></textarea></div>
<button class="btn btn-primary" id="saveBtn" onclick="saveContact()">Save Contact</button>
</div>
</div>

<script>
var ORG_ID = "{org_id}";
var API = "/api/org/{org_id}/crm";
var contacts = [];
var currentContact = null;
var editingId = null;
var stageFilter = "";

// Load on start
loadDashboard();
loadContacts();

async function loadDashboard() {{
  try {{
    var r = await fetch(API + "/dashboard");
    var d = await r.json();
    document.getElementById("statsRow").innerHTML = 
      '<div class="stat"><div class="n">' + (d.total_contacts||0) + '</div><div class="l">Total</div></div>' +
      '<div class="stat"><div class="n">' + (d.by_type?.lead||0) + '</div><div class="l">Leads</div></div>' +
      '<div class="stat"><div class="n">' + (d.by_type?.customer||0) + '</div><div class="l">Customers</div></div>' +
      '<div class="stat"><div class="n">' + (d.by_stage?.won||0) + '</div><div class="l">Won</div></div>';
  }} catch(e) {{}}
}}

async function loadContacts() {{
  var search = document.getElementById("searchInput").value;
  var type = document.getElementById("typeFilter").value;
  var url = API + "/contacts?limit=200";
  if (type) url += "&type=" + type;
  if (stageFilter) url += "&stage=" + stageFilter;
  if (search) url += "&search=" + encodeURIComponent(search);
  
  try {{
    var r = await fetch(url);
    var d = await r.json();
    contacts = d.contacts || [];
    renderContacts();
  }} catch(e) {{
    document.getElementById("emptyState").textContent = "Error loading contacts";
  }}
}}

function searchContacts() {{ clearTimeout(window._st); window._st = setTimeout(loadContacts, 300); }}

function filterStage(stage, btn) {{
  stageFilter = stage;
  document.querySelectorAll(".pipe-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  loadContacts();
}}

function renderContacts() {{
  var list = document.getElementById("contactList");
  document.getElementById("countLabel").textContent = contacts.length + " contacts";
  
  if (contacts.length === 0) {{
    list.innerHTML = '<div class="empty">No contacts found. Click + Add to create one.</div>';
    return;
  }}
  
  list.innerHTML = contacts.map(function(c) {{
    var typeBadge = c.type === "customer" ? "badge-customer" : c.type === "lead" ? "badge-lead" : "badge-new";
    var stageBadge = c.stage === "won" ? "badge-won" : c.stage === "contacted" ? "badge-contacted" : "badge-new";
    return '<div class="contact" onclick="openContact(\'' + c.id + '\')">' +
      '<div class="info"><div class="name">' + c.name + '</div>' +
      '<div class="meta">' + (c.phone||"") + (c.company ? " · " + c.company : "") + '</div></div>' +
      '<div class="right"><span class="badge ' + typeBadge + '">' + c.type + '</span>' +
      '<span class="badge ' + stageBadge + '">' + c.stage + '</span></div></div>';
  }}).join("");
}}

function openContact(id) {{
  currentContact = contacts.find(c => c.id === id);
  if (!currentContact) return;
  
  document.getElementById("detailName").textContent = currentContact.name;
  document.getElementById("detailInfo").innerHTML = 
    (currentContact.phone ? "&#128222; " + currentContact.phone + " &nbsp;" : "") +
    (currentContact.email ? "&#9993; " + currentContact.email + " &nbsp;" : "") +
    (currentContact.company ? "&#127970; " + currentContact.company : "");
  
  document.getElementById("detailPanel").classList.add("show");
  loadActivities(id);
}}

function closeDetail() {{ document.getElementById("detailPanel").classList.remove("show"); currentContact = null; }}

async function loadActivities(contactId) {{
  try {{
    var r = await fetch(API + "/contacts/" + contactId + "/activities");
    var d = await r.json();
    var activities = d.activities || [];
    if (activities.length === 0) {{
      document.getElementById("activityList").innerHTML = '<p style="font-size:.7rem;color:#94a3b8;padding:10px 0">No activities yet</p>';
      return;
    }}
    document.getElementById("activityList").innerHTML = activities.map(function(a) {{
      var color = a.type==="call"?"#22c55e":a.type==="meeting"?"#3b82f6":a.type==="whatsapp"?"#25D366":"#94a3b8";
      var time = new Date(a.created_at).toLocaleDateString("en-IN",{{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"}});
      return '<div class="activity"><div class="dot" style="background:' + color + '"></div><div><div class="text">' + (a.title||a.type) + '</div><div class="time">' + time + '</div></div></div>';
    }}).join("");
  }} catch(e) {{}}
}}

async function addActivity() {{
  if (!currentContact) return;
  var type = document.getElementById("actType").value;
  var title = document.getElementById("actTitle").value;
  if (!title) return;
  
  await fetch(API + "/contacts/" + currentContact.id + "/activities", {{
    method: "POST", headers: {{"Content-Type": "application/json"}},
    body: JSON.stringify({{type: type, title: title}})
  }});
  document.getElementById("actTitle").value = "";
  loadActivities(currentContact.id);
}}

function showDetailTab(tab, btn) {{
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("activitiesTab").style.display = tab === "activities" ? "block" : "none";
  document.getElementById("actionsTab").style.display = tab === "actions" ? "block" : "none";
}}

function showAddModal() {{
  editingId = null;
  document.getElementById("modalTitle").textContent = "Add Contact";
  document.getElementById("fName").value = "";
  document.getElementById("fPhone").value = "";
  document.getElementById("fEmail").value = "";
  document.getElementById("fType").value = "lead";
  document.getElementById("fStage").value = "new";
  document.getElementById("fCompany").value = "";
  document.getElementById("fSource").value = "";
  document.getElementById("fNotes").value = "";
  document.getElementById("addModal").classList.add("show");
}}

function editContact() {{
  if (!currentContact) return;
  editingId = currentContact.id;
  document.getElementById("modalTitle").textContent = "Edit Contact";
  document.getElementById("fName").value = currentContact.name || "";
  document.getElementById("fPhone").value = currentContact.phone || "";
  document.getElementById("fEmail").value = currentContact.email || "";
  document.getElementById("fType").value = currentContact.type || "lead";
  document.getElementById("fStage").value = currentContact.stage || "new";
  document.getElementById("fCompany").value = currentContact.company || "";
  document.getElementById("fSource").value = currentContact.source || "";
  document.getElementById("fNotes").value = currentContact.notes || "";
  document.getElementById("addModal").classList.add("show");
}}

function closeModal() {{ document.getElementById("addModal").classList.remove("show"); }}

async function saveContact() {{
  var name = document.getElementById("fName").value.trim();
  if (!name) {{ alert("Name is required"); return; }}
  
  var data = {{
    name: name,
    phone: document.getElementById("fPhone").value.trim(),
    email: document.getElementById("fEmail").value.trim(),
    type: document.getElementById("fType").value,
    stage: document.getElementById("fStage").value,
    company: document.getElementById("fCompany").value.trim(),
    source: document.getElementById("fSource").value.trim(),
    notes: document.getElementById("fNotes").value.trim(),
  }};
  
  var url = API + "/contacts";
  var method = "POST";
  if (editingId) {{ url += "/" + editingId; method = "PUT"; }}
  
  document.getElementById("saveBtn").textContent = "Saving...";
  await fetch(url, {{method: method, headers: {{"Content-Type": "application/json"}}, body: JSON.stringify(data)}});
  document.getElementById("saveBtn").textContent = "Save Contact";
  closeModal();
  closeDetail();
  loadContacts();
  loadDashboard();
}}

async function deleteContact() {{
  if (!currentContact || !confirm("Delete " + currentContact.name + "?")) return;
  await fetch(API + "/contacts/" + currentContact.id, {{method: "DELETE"}});
  closeDetail();
  loadContacts();
  loadDashboard();
}}
</script>
</body></html>'''
    return HTMLResponse(content=html)
