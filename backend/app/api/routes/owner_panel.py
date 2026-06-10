from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.api.routes.toolkit import get_tools_for_category

router = APIRouter(prefix="/panel", tags=["owner-panel"])


@router.get("/{website_id}", response_class=HTMLResponse)
def owner_panel(website_id: str):
    """Business owner panel with tools, accessible from their website."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "default") if lead else "default"
    phone = lead.get("phone", "") if lead else ""

    tools = get_tools_for_category(category)

    # Build tools HTML
    tools_html = ""
    for t in tools:
        tools_html += f'''
        <button class="tool-card" onclick="runTool('{t['id']}', '{t['name']}')">
            <span class="tool-icon">{t['icon']}</span>
            <div class="tool-info">
                <strong>{t['name']}</strong>
                <span>{t['desc']}</span>
            </div>
        </button>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{business_name} - Business Panel</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#f1f5f9;color:#1e293b;min-height:100vh}}
.header{{background:#fff;border-bottom:1px solid #e2e8f0;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}}
.header h1{{font-size:1.1rem;font-weight:700}}
.header .badge{{background:#e0f2fe;color:#0369a1;padding:4px 10px;border-radius:20px;font-size:.75rem;font-weight:500}}
.container{{max-width:900px;margin:0 auto;padding:24px}}
.section-title{{font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:12px}}
.tools-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-bottom:32px}}
.tool-card{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;display:flex;align-items:flex-start;gap:12px;cursor:pointer;transition:all .2s;text-align:left;width:100%}}
.tool-card:hover{{border-color:#6366f1;box-shadow:0 4px 12px rgba(99,102,241,.1);transform:translateY(-1px)}}
.tool-icon{{font-size:1.5rem;flex-shrink:0;margin-top:2px}}
.tool-info{{display:flex;flex-direction:column;gap:2px}}
.tool-info strong{{font-size:.85rem}}
.tool-info span{{font-size:.75rem;color:#64748b}}
.output-area{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-top:16px;display:none}}
.output-area.active{{display:block}}
.output-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
.output-header h3{{font-size:.9rem;font-weight:600}}
.output-content{{white-space:pre-wrap;font-size:.85rem;line-height:1.7;color:#374151}}
.context-input{{width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:8px;font-size:.85rem;margin-bottom:12px;font-family:Inter,sans-serif}}
.btn{{background:#6366f1;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:.85rem;font-weight:600;cursor:pointer}}
.btn:hover{{background:#4f46e5}}
.btn:disabled{{opacity:.5;cursor:not-allowed}}
.btn-copy{{background:#f1f5f9;color:#475569;border:1px solid #e2e8f0;padding:6px 12px;border-radius:6px;font-size:.75rem;cursor:pointer}}
.btn-copy:hover{{background:#e2e8f0}}
.loading{{color:#6366f1;font-size:.85rem;padding:20px 0}}
.quick-links{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px}}
.quick-link{{background:#fff;border:1px solid #e2e8f0;padding:8px 14px;border-radius:8px;font-size:.8rem;text-decoration:none;color:#475569;transition:all .2s}}
.quick-link:hover{{border-color:#6366f1;color:#6366f1}}
</style>
</head>
<body>

<div class="header">
    <h1>{business_name}</h1>
    <span class="badge">{category.capitalize()} Tools</span>
</div>

<div class="container">
    <div class="quick-links">
        <a href="/api/preview/{website_id}" class="quick-link" target="_blank">\U0001f310 View Website</a>
        <a href="/api/owner-analytics/{website_id}" class="quick-link" target="_blank">\U0001f4ca Analytics</a>
        <a href="/api/daily/{website_id}" class="quick-link" target="_blank">\U0001f4f1 Daily Content</a>
        <a href="/api/store/{website_id}" class="quick-link" target="_blank">\U0001f6cd Store</a>
        <a href="/api/store/{website_id}/manage" class="quick-link" target="_blank">\U0001f4e6 Manage Products</a>
        <a href="/api/qr/{website_id}" class="quick-link" target="_blank">\U0001f4f7 QR Code</a>
        <a href="/api/branding/{website_id}/logo/preview" class="quick-link" target="_blank">\U0001f3a8 Logo</a>
        <a href="/api/branding/{website_id}/social-post/preview?platform=instagram" class="quick-link" target="_blank">\U0001f4f8 Social Post</a>
        <a href="https://wa.me/{phone.replace('-','').replace(' ','').replace('+','')}" class="quick-link" target="_blank">\U0001f4ac WhatsApp</a>
    </div>

    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin-bottom:24px">
        <p class="section-title" style="margin-bottom:12px">Social Media Links</p>
        <p style="font-size:.75rem;color:#94a3b8;margin-bottom:12px">Add your social media links. These will appear on your website.</p>
        <form onsubmit="saveSocial(event)" style="display:flex;flex-direction:column;gap:8px">
            <input id="instaUrl" placeholder="Instagram URL (e.g., https://instagram.com/yourbusiness)" style="padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.85rem">
            <input id="fbUrl" placeholder="Facebook URL (e.g., https://facebook.com/yourbusiness)" style="padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.85rem">
            <input id="ytUrl" placeholder="YouTube URL (optional)" style="padding:10px;border:1px solid #e2e8f0;border-radius:8px;font-size:.85rem">
            <button type="submit" class="btn" style="align-self:flex-start">Save Social Links</button>
        </form>
    </div>

    <p class="section-title">Your Business Tools</p>
    <div class="tools-grid">{tools_html}</div>

    <div class="output-area" id="outputArea">
        <div class="output-header">
            <h3 id="outputTitle">Result</h3>
            <button class="btn-copy" onclick="copyOutput()">Copy</button>
        </div>
        <input class="context-input" id="contextInput" placeholder="Add context (optional)... e.g., for Diwali, target families, 30% discount" />
        <button class="btn" id="generateBtn" onclick="generate()">Generate</button>
        <div class="loading" id="loadingEl" style="display:none">Generating content...</div>
        <div class="output-content" id="outputContent"></div>
    </div>
</div>

<script>
let currentToolId = '';
let currentToolName = '';

function runTool(toolId, toolName) {{
    currentToolId = toolId;
    currentToolName = toolName;
    document.getElementById('outputArea').classList.add('active');
    document.getElementById('outputTitle').textContent = toolName;
    document.getElementById('outputContent').textContent = '';
    document.getElementById('contextInput').value = '';
    document.getElementById('contextInput').focus();
}}

async function generate() {{
    const ctx = document.getElementById('contextInput').value;
    const btn = document.getElementById('generateBtn');
    const loading = document.getElementById('loadingEl');
    const output = document.getElementById('outputContent');

    btn.disabled = true;
    loading.style.display = 'block';
    output.textContent = '';

    try {{
        const res = await fetch('/api/toolkit/{website_id}/tools/run', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{tool_id: currentToolId, context: ctx}})
        }});
        const data = await res.json();
        output.textContent = data.content;
    }} catch(e) {{
        output.textContent = 'Error generating content. Please try again.';
    }} finally {{
        btn.disabled = false;
        loading.style.display = 'none';
    }}
}}

async function saveSocial(e) {
    e.preventDefault();
    const data = {
        instagram: document.getElementById('instaUrl').value,
        facebook: document.getElementById('fbUrl').value,
        youtube: document.getElementById('ytUrl').value,
    };
    try {
        const r = await fetch('/api/panel/' + '{website_id}' + '/social-links', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (r.ok) { alert('Social links saved! They will appear on your website.'); }
        else { alert('Failed to save. Try again.'); }
    } catch(e) { alert('Error saving links.'); }
}

function copyOutput() {{
    const text = document.getElementById('outputContent').textContent;
    navigator.clipboard.writeText(text);
    const btn = event.target;
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 2000);
}}
</script>
</body>
</html>'''
    return HTMLResponse(content=html)
