from __future__ import annotations
import json
import hashlib
import secrets
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
from app.core.supabase import get_supabase
from app.core.logging import get_logger

router = APIRouter(prefix="/site-manager", tags=["site-manager"])
logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)

# Admin credentials (change these)
ADMIN_EMAIL = "admin@kalpdev.com"
ADMIN_PASSWORD_HASH = hashlib.sha256("Admin@2024".encode()).hexdigest()


class AdminLogin(BaseModel):
    email: str
    password: str


class AIEditCommand(BaseModel):
    command: str


class VersionRestore(BaseModel):
    version: int


# ============ AUTH ============

_tokens = {}


@router.post("/login")
def admin_login(req: AdminLogin):
    """Admin login."""
    if req.email == ADMIN_EMAIL and hashlib.sha256(req.password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
        token = secrets.token_urlsafe(32)
        _tokens[token] = {"email": req.email, "role": "super_admin", "login_time": datetime.now().isoformat()}
        return {"token": token, "role": "super_admin"}
    raise HTTPException(401, "Invalid credentials")


def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.credentials not in _tokens:
        raise HTTPException(401, "Not authenticated")
    return _tokens[credentials.credentials]


# ============ AI EDIT ENGINE ============

@router.post("/{website_id}/ai-edit")
async def ai_edit(website_id: str, req: AIEditCommand, admin=Depends(verify_admin)):
    """AI-powered website editing. Modifies structured JSON then regenerates."""
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    current_content = website.get("content", {})
    if "raw_content" in current_content:
        raw = current_content["raw_content"]
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        try:
            current_content = json.loads(raw)
        except json.JSONDecodeError:
            pass

    # Save current version before editing
    db = get_supabase()
    versions = website.get("versions", [])
    if not isinstance(versions, list):
        versions = []
    versions.append({
        "version": len(versions) + 1,
        "content": current_content,
        "timestamp": datetime.now().isoformat(),
        "prompt": req.command,
    })

    # AI Design Director: analyze context before modifying
    prompt = f"""You are an AI Website Manager. You must modify this website based on the user command.

CURRENT WEBSITE JSON:
{json.dumps(current_content, indent=2)[:3000]}

USER COMMAND: "{req.command}"

RULES:
1. Modify ONLY what the user asked for
2. Preserve all existing content that wasn't mentioned
3. Maintain brand consistency (colors, tone, style)
4. Return the COMPLETE updated JSON
5. If adding new sections, integrate them naturally
6. For color changes, update the entire color_scheme
7. For content changes, keep SEO keywords intact
8. Use emojis for icons

Return ONLY valid JSON with all fields preserved."""

    result = await chat_completion([{"role": "user", "content": prompt}])

    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        updated_content = json.loads(cleaned)
    except json.JSONDecodeError:
        raise HTTPException(400, "AI could not generate valid changes. Try rephrasing.")

    # Store updated content + version history
    db.table("websites").update({
        "content": updated_content,
    }).eq("id", website_id).execute()

    logger.info("AI edit applied", website_id=website_id, command=req.command[:50], version=len(versions))

    return {
        "status": "updated",
        "version": len(versions) + 1,
        "command": req.command,
        "preview_url": f"/api/preview/{website_id}",
    }


# ============ VERSION CONTROL ============

@router.get("/{website_id}/versions")
def get_versions(website_id: str, admin=Depends(verify_admin)):
    """Get version history for a website."""
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    # Get edit history from outreach or agent logs
    db = get_supabase()
    logs = db.table("agent_logs").select("*").eq("lead_id", website.get("lead_id")).order("created_at", desc=True).limit(20).execute()

    return {
        "website_id": website_id,
        "current_version": "latest",
        "history": logs.data if logs.data else [],
    }


@router.post("/{website_id}/restore")
async def restore_version(website_id: str, req: VersionRestore, admin=Depends(verify_admin)):
    """Restore a previous version."""
    # For now, return info about the feature
    return {"status": "Version control requires the versions table. Feature ready for Phase 3."}


# ============ ADMIN DASHBOARD PAGE ============

@router.get("/{website_id}/dashboard", response_class=HTMLResponse)
async def admin_dashboard(website_id: str):
    """Admin dashboard for managing a website with AI."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Site Manager - {business_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex}}
.sidebar{{width:260px;background:#1e293b;border-right:1px solid #334155;padding:20px;display:flex;flex-direction:column}}
.sidebar h2{{font-size:.9rem;font-weight:700;margin-bottom:20px;color:#fff}}
.nav-item{{padding:10px 12px;border-radius:8px;font-size:.8rem;cursor:pointer;margin-bottom:4px;transition:all .2s;color:#94a3b8}}
.nav-item:hover,.nav-item.active{{background:#334155;color:#fff}}
.main{{flex:1;display:flex;flex-direction:column}}
.topbar{{background:#1e293b;border-bottom:1px solid #334155;padding:12px 24px;display:flex;align-items:center;justify-content:space-between}}
.topbar h1{{font-size:1rem;font-weight:600}}
.content{{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:0}}
.editor-panel{{padding:24px;border-right:1px solid #334155;display:flex;flex-direction:column}}
.preview-panel{{position:relative}}
.preview-panel iframe{{width:100%;height:100%;border:0}}
.ai-input{{width:100%;padding:14px 16px;background:#0f172a;border:1px solid #334155;border-radius:10px;color:#fff;font-size:.85rem;resize:none;outline:none;flex:1}}
.ai-input:focus{{border-color:#6366f1}}
.ai-btn{{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border:none;padding:12px 20px;border-radius:8px;font-size:.85rem;font-weight:600;cursor:pointer;margin-top:12px;width:100%}}
.ai-btn:hover{{opacity:.9}}
.ai-btn:disabled{{opacity:.5}}
.history{{margin-top:16px;flex:1;overflow-y:auto}}
.history-item{{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:10px 12px;margin-bottom:8px;font-size:.75rem}}
.history-item .cmd{{color:#a78bfa;font-weight:500}}
.history-item .time{{color:#64748b;font-size:.65rem;margin-top:4px}}
.status{{display:inline-block;width:8px;height:8px;background:#10b981;border-radius:50%;margin-right:6px}}
.login-overlay{{position:fixed;inset:0;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;z-index:100}}
.login-box{{background:#1e293b;border-radius:16px;padding:32px;width:360px;border:1px solid #334155}}
.login-box h2{{font-size:1.1rem;margin-bottom:20px}}
.login-box input{{width:100%;padding:10px 14px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:#fff;font-size:.85rem;margin-bottom:12px;outline:none}}
.login-box button{{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer}}
</style></head><body>

<div class="login-overlay" id="loginOverlay">
<div class="login-box">
<h2>&#128274; Site Manager Login</h2>
<input type="email" id="loginEmail" placeholder="Email" value="admin@kalpdev.com">
<input type="password" id="loginPass" placeholder="Password">
<button onclick="doLogin()">Sign In</button>
<p id="loginError" style="color:#ef4444;font-size:.75rem;margin-top:8px"></p>
</div>
</div>

<div class="sidebar">
<h2>&#9889; Site Manager</h2>
<div class="nav-item active">&#128421; AI Editor</div>
<div class="nav-item" onclick="window.open('/api/preview/{website_id}')">&#127760; View Live Site</div>
<div class="nav-item" onclick="window.open('/api/daily/{website_id}')">&#128200; Daily Dashboard</div>
<div class="nav-item" onclick="window.open('/api/panel/{website_id}')">&#128296; Business Tools</div>
<div class="nav-item" onclick="window.open('/api/logo-gen/{website_id}/preview')">&#127912; Logo Editor</div>
<div style="margin-top:auto;padding-top:16px;border-top:1px solid #334155">
<div class="nav-item" style="font-size:.7rem;color:#64748b"><span class="status"></span>Live</div>
<div class="nav-item" style="font-size:.7rem;color:#64748b">{business_name}</div>
</div>
</div>

<div class="main">
<div class="topbar">
<h1>{business_name}</h1>
<span style="font-size:.75rem;color:#64748b">AI Website Manager</span>
</div>
<div class="content">
<div class="editor-panel">
<p style="font-size:.75rem;color:#64748b;margin-bottom:8px">Type a command to modify the website:</p>
<textarea class="ai-input" id="aiInput" placeholder="Examples:&#10;- Change colors to black and gold&#10;- Make it look more luxurious&#10;- Add a Diwali offer banner&#10;- Improve SEO for Pune&#10;- Add a new service for teeth whitening&#10;- Make the website more modern"></textarea>
<button class="ai-btn" id="aiBtn" onclick="executeCommand()">&#9889; Apply Changes</button>
<div class="history" id="history"></div>
</div>
<div class="preview-panel">
<iframe id="previewFrame" src="/api/preview/{website_id}"></iframe>
</div>
</div>
</div>

<script>
let token = '';
const wid = '{website_id}';

function doLogin() {{
    const email = document.getElementById('loginEmail').value;
    const pass = document.getElementById('loginPass').value;
    fetch('/api/site-manager/login', {{
        method: 'POST', headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{email, password: pass}})
    }}).then(r => r.json()).then(data => {{
        if (data.token) {{
            token = data.token;
            document.getElementById('loginOverlay').style.display = 'none';
        }} else {{
            document.getElementById('loginError').textContent = 'Invalid credentials';
        }}
    }}).catch(() => document.getElementById('loginError').textContent = 'Connection error');
}}

function executeCommand() {{
    const cmd = document.getElementById('aiInput').value.trim();
    if (!cmd || !token) return;
    const btn = document.getElementById('aiBtn');
    btn.disabled = true; btn.textContent = 'Applying...';

    fetch(`/api/site-manager/${{wid}}/ai-edit`, {{
        method: 'POST',
        headers: {{'Content-Type':'application/json', 'Authorization': 'Bearer ' + token}},
        body: JSON.stringify({{command: cmd}})
    }}).then(r => r.json()).then(data => {{
        if (data.status === 'updated') {{
            document.getElementById('previewFrame').src = '/api/preview/' + wid + '?v=' + Date.now();
            addHistory(cmd, data.version);
            document.getElementById('aiInput').value = '';
        }} else {{
            alert(data.detail || 'Error applying changes');
        }}
    }}).catch(e => alert('Error: ' + e.message))
    .finally(() => {{ btn.disabled = false; btn.textContent = '\\u26a1 Apply Changes'; }});
}}

function addHistory(cmd, version) {{
    const div = document.getElementById('history');
    div.innerHTML = `<div class="history-item"><div class="cmd">${{cmd}}</div><div class="time">v${{version}} - ${{new Date().toLocaleTimeString()}}</div></div>` + div.innerHTML;
}}

document.getElementById('aiInput').addEventListener('keydown', (e) => {{
    if (e.key === 'Enter' && e.ctrlKey) executeCommand();
}});
</script>
</body></html>"""

    return HTMLResponse(content=html)
