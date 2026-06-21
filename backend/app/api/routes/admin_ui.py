from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/admin/manage", tags=["admin-ui"])


@router.get("", response_class=HTMLResponse)
async def admin_portal_ui(pwd: str = ""):
    """Full admin portal - manage organizations, modules, templates."""
    if pwd != "kalpdev2024":
        return HTMLResponse('''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Admin Login</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,sans-serif;background:#0f172a;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:16px}
.box{background:#1e293b;border:1px solid #334155;border-radius:16px;padding:32px;max-width:360px;width:100%;text-align:center}h1{color:#fff;font-size:1.2rem;margin-bottom:8px}p{color:#64748b;font-size:.8rem;margin-bottom:20px}
input{width:100%;padding:12px;border:1px solid #334155;border-radius:8px;background:#0f172a;color:#fff;font-size:.85rem;outline:none;margin-bottom:12px}button{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.85rem}</style></head>
<body><div class="box"><h1>Admin Portal</h1><p>Enter password to access</p><form method="GET"><input type="password" name="pwd" placeholder="Password" autofocus><button type="submit">Access Portal</button></form></div></body></html>''')
    
    db = get_supabase()
    
    # Get data
    modules = db.table("modules").select("*").order("sort_order").execute()
    templates = db.table("industry_templates").select("*").order("sort_order").execute()
    
    import json
    modules_json = json.dumps(modules.data or [])
    templates_json = json.dumps(templates.data or [])
    
    html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>City Maps - Admin Portal</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#f1f5f9;color:#1e293b;min-height:100vh}}
.header{{background:#1e293b;color:#fff;padding:14px 20px;position:sticky;top:0;z-index:50}}
.header-inner{{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between}}
.header h1{{font-size:1rem;font-weight:800}}
.header .badge{{background:rgba(99,102,241,.2);color:#a5b4fc;padding:3px 10px;border-radius:8px;font-size:.65rem;font-weight:600}}
.main{{max-width:1100px;margin:0 auto;padding:20px}}
.tabs{{display:flex;gap:4px;margin-bottom:16px;background:#fff;border-radius:10px;padding:4px;border:1px solid #e2e8f0}}
.tab{{padding:10px 18px;border-radius:8px;font-size:.8rem;font-weight:600;cursor:pointer;color:#64748b}}
.tab.active{{background:#6366f1;color:#fff}}
.section{{display:none}}.section.active{{display:block}}
.search-bar{{display:flex;gap:8px;margin-bottom:14px}}
.search-bar input{{flex:1;padding:10px 14px;border:1px solid #e2e8f0;border-radius:8px;font-size:.8rem;outline:none}}
.search-bar input:focus{{border-color:#6366f1}}
.search-bar select{{padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.75rem;background:#fff}}
.org-card{{background:#fff;border:1px solid #f1f5f9;border-radius:10px;padding:14px;margin-bottom:8px;cursor:pointer;transition:border .2s}}
.org-card:hover{{border-color:#6366f1}}
.org-card.selected{{border-color:#6366f1;box-shadow:0 0 0 2px rgba(99,102,241,.15)}}
.org-name{{font-size:.85rem;font-weight:600}}
.org-meta{{font-size:.65rem;color:#94a3b8;margin-top:2px}}
.org-badges{{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap}}
.org-badges span{{font-size:.55rem;padding:2px 6px;border-radius:6px;font-weight:600}}
.mod-on{{background:#dcfce7;color:#166534}}
.mod-off{{background:#fef2f2;color:#991b1b}}
.panel{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-top:16px}}
.panel h2{{font-size:.9rem;font-weight:700;margin-bottom:12px}}
.module-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}}
.module-item{{display:flex;align-items:center;gap:8px;padding:10px 12px;border:1px solid #f1f5f9;border-radius:8px;cursor:pointer;transition:all .2s}}
.module-item:hover{{border-color:#cbd5e1}}
.module-item.enabled{{border-color:#22c55e;background:#f0fdf4}}
.module-item .name{{font-size:.75rem;font-weight:600}}
.module-item .desc{{font-size:.6rem;color:#94a3b8}}
.toggle{{width:36px;height:20px;border-radius:10px;background:#e2e8f0;position:relative;cursor:pointer;transition:background .2s;flex-shrink:0}}
.toggle.on{{background:#22c55e}}
.toggle::after{{content:'';position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:#fff;transition:transform .2s}}
.toggle.on::after{{transform:translateX(16px)}}
.btn{{padding:10px 18px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:700;font-size:.8rem;cursor:pointer}}
.btn:hover{{opacity:.9}}
.btn-green{{background:#22c55e}}
.btn-outline{{background:none;border:1px solid #e2e8f0;color:#475569}}
.template-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;margin-bottom:12px}}
.tmpl-btn{{padding:10px;border:1px solid #e2e8f0;border-radius:8px;text-align:center;cursor:pointer;font-size:.72rem;font-weight:600;transition:all .2s}}
.tmpl-btn:hover{{border-color:#6366f1;background:rgba(99,102,241,.05)}}
.toast{{position:fixed;bottom:20px;right:20px;background:#1e293b;color:#fff;padding:12px 20px;border-radius:8px;font-size:.8rem;display:none;z-index:999}}
.stats{{display:flex;gap:16px;margin-bottom:16px}}
.stat{{background:#fff;border:1px solid #f1f5f9;border-radius:10px;padding:14px 20px;text-align:center}}
.stat .n{{font-size:1.5rem;font-weight:800;color:#6366f1}}
.stat .l{{font-size:.65rem;color:#94a3b8;margin-top:2px}}
.org-list{{max-height:calc(100vh - 280px);overflow-y:auto}}
</style></head><body>
<div class="header"><div class="header-inner"><h1>&#9881; City Maps Admin</h1><span class="badge">Business OS</span></div></div>
<div class="main">

<div class="tabs">
<div class="tab active" onclick="showTab('orgs',this)">Organizations</div>
<div class="tab" onclick="showTab('modules',this)">Modules</div>
<div class="tab" onclick="showTab('templates',this)">Templates</div>
<div class="tab" onclick="showTab('create',this)">+ Create Org</div>
</div>

<!-- Organizations Tab -->
<div class="section active" id="sec-orgs">
<div class="stats" id="orgStats"></div>
<div class="search-bar">
<input type="text" id="orgSearch" placeholder="Search organizations..." oninput="searchOrgs()">
<select id="planFilter" onchange="searchOrgs()"><option value="">All Plans</option><option value="starter">Starter</option><option value="pro">Pro</option><option value="enterprise">Enterprise</option></select>
</div>
<div id="orgList" class="org-list"></div>
<div class="panel" id="orgPanel" style="display:none">
<h2 id="panelTitle">Select an organization</h2>
<p id="panelMeta" style="font-size:.7rem;color:#94a3b8;margin-bottom:12px"></p>
<div style="margin-bottom:12px">
<span style="font-size:.7rem;font-weight:600;color:#475569">Quick Apply Template:</span>
<div class="template-grid" id="quickTemplates" style="margin-top:6px"></div>
</div>
<h3 style="font-size:.8rem;font-weight:600;margin-bottom:8px">Module Access</h3>
<div class="module-grid" id="moduleGrid"></div>
<div style="margin-top:14px;display:flex;gap:8px">
<button class="btn btn-green" onclick="saveModules()">Save Changes</button>
<button class="btn btn-outline" onclick="document.getElementById('orgPanel').style.display='none'">Close</button>
</div>
</div>
</div>

<!-- Modules Tab -->
<div class="section" id="sec-modules">
<h2 style="font-size:1rem;font-weight:700;margin-bottom:12px">All Registered Modules</h2>
<div id="allModulesList"></div>
</div>

<!-- Templates Tab -->
<div class="section" id="sec-templates">
<h2 style="font-size:1rem;font-weight:700;margin-bottom:12px">Industry Templates</h2>
<div id="allTemplatesList"></div>
</div>

<!-- Create Org Tab -->
<div class="section" id="sec-create">
<div class="panel">
<h2>Create New Organization</h2>
<div style="display:grid;gap:10px;max-width:500px">
<div><label style="font-size:.7rem;font-weight:600;color:#64748b">Business Name *</label><input id="c_name" placeholder="e.g., ABC Gym" style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;margin-top:3px"></div>
<div><label style="font-size:.7rem;font-weight:600;color:#64748b">Slug (URL) *</label><input id="c_slug" placeholder="abcgym" style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;margin-top:3px"><span style="font-size:.6rem;color:#94a3b8">.city-maps.online</span></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
<div><label style="font-size:.7rem;font-weight:600;color:#64748b">Phone</label><input id="c_phone" placeholder="9876543210" style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;margin-top:3px"></div>
<div><label style="font-size:.7rem;font-weight:600;color:#64748b">Plan</label><select id="c_plan" style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;margin-top:3px"><option value="starter">Starter</option><option value="pro">Pro</option><option value="enterprise">Enterprise</option></select></div>
</div>
<div><label style="font-size:.7rem;font-weight:600;color:#64748b">Template (optional)</label><select id="c_template" style="width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.82rem;margin-top:3px"><option value="">None (core modules only)</option></select></div>
<button class="btn" onclick="createOrg()">Create Organization</button>
</div>
</div>
</div>

<div class="toast" id="toast"></div>
</div>

<script>
var API = "https://ai-agency-platform.onrender.com";
var allModules = {modules_json};
var allTemplates = {templates_json};
var orgs = [];
var selectedOrg = null;
var selectedModules = [];

// Init
loadOrgs();
renderModulesTab();
renderTemplatesTab();
populateTemplateSelect();

function showTab(name, btn) {{
  document.querySelectorAll(".section").forEach(s=>s.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  document.getElementById("sec-"+name).classList.add("active");
  btn.classList.add("active");
}}

function showToast(msg) {{
  var t = document.getElementById("toast");
  t.textContent = msg; t.style.display = "block";
  setTimeout(function(){{ t.style.display="none"; }}, 2500);
}}

// === ORGANIZATIONS ===
async function loadOrgs() {{
  var r = await fetch(API+"/api/admin/organizations?limit=200");
  var d = await r.json();
  orgs = d.organizations || [];
  renderOrgs(orgs);
  document.getElementById("orgStats").innerHTML = 
    '<div class="stat"><div class="n">'+orgs.length+'</div><div class="l">Total Orgs</div></div>'+
    '<div class="stat"><div class="n">'+orgs.filter(o=>o.plan==="pro").length+'</div><div class="l">Pro</div></div>'+
    '<div class="stat"><div class="n">'+orgs.filter(o=>o.plan==="enterprise").length+'</div><div class="l">Enterprise</div></div>';
}}

function searchOrgs() {{
  var q = document.getElementById("orgSearch").value.toLowerCase();
  var plan = document.getElementById("planFilter").value;
  var filtered = orgs.filter(function(o) {{
    var matchQ = !q || o.name.toLowerCase().includes(q) || o.slug.toLowerCase().includes(q);
    var matchP = !plan || o.plan === plan;
    return matchQ && matchP;
  }});
  renderOrgs(filtered);
}}

function renderOrgs(list) {{
  var el = document.getElementById("orgList");
  el.innerHTML = list.map(function(o) {{
    var mods = (o.enabled_modules||[]).map(function(m){{ return '<span class="mod-on">'+m+'</span>'; }}).join("");
    return '<div class="org-card'+(selectedOrg&&selectedOrg.id===o.id?' selected':'')+'" onclick="selectOrg(\''+o.id+'\')"><div class="org-name">'+o.name+'</div><div class="org-meta">'+o.slug+'.city-maps.online | '+o.plan+' | '+o.enabled_modules_count+' modules</div><div class="org-badges">'+mods+'</div></div>';
  }}).join("");
}}

async function selectOrg(id) {{
  selectedOrg = orgs.find(function(o){{ return o.id===id; }});
  document.getElementById("orgPanel").style.display = "block";
  document.getElementById("panelTitle").textContent = selectedOrg.name;
  document.getElementById("panelMeta").textContent = selectedOrg.slug+".city-maps.online | Plan: "+selectedOrg.plan;
  selectedModules = [...(selectedOrg.enabled_modules||[])];
  renderModuleGrid();
  renderQuickTemplates();
  renderOrgs(orgs); // refresh selected state
}}

function renderModuleGrid() {{
  var el = document.getElementById("moduleGrid");
  el.innerHTML = allModules.map(function(m) {{
    var enabled = selectedModules.includes(m.id);
    var isCore = m.is_core;
    return '<div class="module-item'+(enabled?' enabled':'')+'" onclick="'+(isCore?'':'toggleMod(\''+m.id+'\')')+'"><div class="toggle'+(enabled?' on':'')+'"></div><div><div class="name">'+m.name+(isCore?' (core)':'')+'</div><div class="desc">'+m.description+'</div></div></div>';
  }}).join("");
}}

function toggleMod(id) {{
  if(selectedModules.includes(id)) selectedModules = selectedModules.filter(m=>m!==id);
  else selectedModules.push(id);
  renderModuleGrid();
}}

function renderQuickTemplates() {{
  var el = document.getElementById("quickTemplates");
  el.innerHTML = allTemplates.slice(0,10).map(function(t) {{
    return '<div class="tmpl-btn" onclick="applyTemplate(\''+t.id+'\')">'+t.name+'</div>';
  }}).join("");
}}

function applyTemplate(id) {{
  var tmpl = allTemplates.find(function(t){{ return t.id===id; }});
  if(!tmpl) return;
  // Keep core modules + add template modules
  var core = allModules.filter(m=>m.is_core).map(m=>m.id);
  selectedModules = [...new Set([...core, ...tmpl.module_ids])];
  renderModuleGrid();
  showToast("Template '"+tmpl.name+"' applied. Click Save to confirm.");
}}

async function saveModules() {{
  if(!selectedOrg) return;
  await fetch(API+"/api/admin/organizations/"+selectedOrg.id+"/modules", {{
    method:"PUT", headers:{{"Content-Type":"application/json"}},
    body: JSON.stringify({{enabled_modules: selectedModules}})
  }});
  showToast("Modules saved for "+selectedOrg.name);
  // Refresh
  selectedOrg.enabled_modules = selectedModules;
  selectedOrg.enabled_modules_count = selectedModules.length;
  renderOrgs(orgs);
}}

// === MODULES TAB ===
function renderModulesTab() {{
  var el = document.getElementById("allModulesList");
  el.innerHTML = '<div class="module-grid">'+allModules.map(function(m) {{
    return '<div class="module-item enabled"><div><div class="name">'+m.name+'</div><div class="desc">'+m.description+'</div><div style="font-size:.55rem;color:#94a3b8;margin-top:2px">Plans: '+(m.default_plans||[]).join(", ")+'</div></div></div>';
  }}).join("")+'</div>';
}}

// === TEMPLATES TAB ===
function renderTemplatesTab() {{
  var el = document.getElementById("allTemplatesList");
  el.innerHTML = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px">'+allTemplates.map(function(t) {{
    var mods = (t.module_ids||[]).map(function(m){{ return '<span style="font-size:.55rem;padding:1px 5px;background:#eff6ff;color:#3b82f6;border-radius:4px">'+m+'</span>'; }}).join(" ");
    return '<div style="background:#fff;border:1px solid #f1f5f9;border-radius:10px;padding:14px"><div style="font-size:.82rem;font-weight:700">'+t.name+'</div><div style="font-size:.65rem;color:#94a3b8;margin:4px 0">'+(t.description||"")+'</div><div style="display:flex;flex-wrap:wrap;gap:3px">'+mods+'</div></div>';
  }}).join("")+'</div>';
}}

// === CREATE ORG ===
function populateTemplateSelect() {{
  var sel = document.getElementById("c_template");
  allTemplates.forEach(function(t) {{
    var opt = document.createElement("option");
    opt.value = t.id; opt.textContent = t.name+" ("+t.module_ids.length+" modules)";
    sel.appendChild(opt);
  }});
}}

document.getElementById("c_name").addEventListener("input", function() {{
  var slug = this.value.toLowerCase().replace(/[^a-z0-9\\s-]/g,"").replace(/\\s+/g,"-").slice(0,30);
  document.getElementById("c_slug").value = slug;
}});

async function createOrg() {{
  var name = document.getElementById("c_name").value.trim();
  var slug = document.getElementById("c_slug").value.trim();
  if(!name||!slug){{ alert("Name and slug required"); return; }}
  var body = {{name:name, slug:slug, plan:document.getElementById("c_plan").value, phone:document.getElementById("c_phone").value}};
  var tmpl = document.getElementById("c_template").value;
  if(tmpl) body.template_id = tmpl;
  
  var r = await fetch(API+"/api/organizations", {{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(body)}});
  var d = await r.json();
  if(r.ok) {{
    showToast("Created: "+name+" ("+slug+".city-maps.online)");
    document.getElementById("c_name").value="";document.getElementById("c_slug").value="";document.getElementById("c_phone").value="";
    loadOrgs();
  }} else {{
    alert(d.detail || "Failed to create");
  }}
}}
</script>
</body></html>'''
    return HTMLResponse(content=html)
