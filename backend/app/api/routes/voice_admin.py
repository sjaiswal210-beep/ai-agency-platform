from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/admin/voice-calls", tags=["voice-admin"])


@router.get("", response_class=HTMLResponse)
async def voice_call_admin_ui(pwd: str = ""):
    if pwd != "kalpdev2024":
        return HTMLResponse('<html><body style="background:#0f172a;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh"><div style="text-align:center"><h1>Voice Calls Admin</h1><form method="GET"><input name="pwd" type="password" placeholder="Password" style="padding:10px;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#fff;margin:10px"><button style="padding:10px 20px;background:#6366f1;color:#fff;border:none;border-radius:8px">Access</button></form></div></body></html>')
    db = get_supabase()
    import json
    calls = db.table("voice_calls").select("*").order("created_at", desc=True).limit(100).execute()
    config = db.table("voice_call_config").select("*").limit(1).execute()
    all_calls = calls.data or []
    total = len(all_calls)
    completed = sum(1 for c in all_calls if c.get("call_status") == "completed")
    interested = sum(1 for c in all_calls if c.get("outcome") == "interested")
    subscribed = sum(1 for c in all_calls if c.get("outcome") == "subscribed")
    not_interested = sum(1 for c in all_calls if c.get("outcome") == "not_interested")
    whatsapp_sent = sum(1 for c in all_calls if c.get("whatsapp_sent"))
    cfg = config.data[0] if config.data else {}
    auto_enabled = cfg.get("auto_call_enabled", False)
    calls_today = cfg.get("calls_made_today", 0)
    max_daily = cfg.get("max_calls_per_day", 50)
    calls_json = json.dumps(all_calls[:50])
    auto_class = "active" if auto_enabled else ""

    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Voice Calls Admin</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:800px;margin:0 auto}}h1{{font-size:1.3rem;margin-bottom:4px}}.sub{{font-size:.75rem;color:#64748b;margin-bottom:20px}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin-bottom:20px}}.stat{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:12px;text-align:center}}.stat-num{{font-size:1.4rem;font-weight:800;color:#6366f1}}.stat-label{{font-size:.65rem;color:#64748b;margin-top:2px}}.card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:12px}}.card h3{{font-size:.85rem;margin-bottom:10px}}table{{width:100%;border-collapse:collapse;font-size:.7rem}}th{{text-align:left;padding:8px 6px;color:#64748b;border-bottom:1px solid #334155}}td{{padding:8px 6px;border-bottom:1px solid #1e293b}}.badge{{display:inline-block;padding:2px 8px;border-radius:8px;font-size:.6rem;font-weight:600}}.badge-green{{background:#064e3b;color:#6ee7b7}}.badge-red{{background:#450a0a;color:#fca5a5}}.badge-gray{{background:#1e293b;color:#94a3b8}}.badge-yellow{{background:#422006;color:#fcd34d}}.badge-blue{{background:#1e3a5f;color:#7dd3fc}}.btn{{padding:8px 16px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:600;font-size:.75rem;cursor:pointer}}.actions{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}}</style></head><body>
<h1>Voice Calls</h1><p class="sub">Today: {calls_today}/{max_daily} | Auto: {"ON" if auto_enabled else "OFF"}</p>
<div class="stats"><div class="stat"><div class="stat-num">{total}</div><div class="stat-label">Total</div></div><div class="stat"><div class="stat-num">{completed}</div><div class="stat-label">Completed</div></div><div class="stat"><div class="stat-num" style="color:#10b981">{interested}</div><div class="stat-label">Interested</div></div><div class="stat"><div class="stat-num" style="color:#f59e0b">{subscribed}</div><div class="stat-label">Subscribed</div></div><div class="stat"><div class="stat-num" style="color:#ef4444">{not_interested}</div><div class="stat-label">Not Interested</div></div><div class="stat"><div class="stat-num">{whatsapp_sent}</div><div class="stat-label">WA Sent</div></div></div>
<div class="card"><h3>Actions</h3><div class="actions"><button class="btn" onclick="triggerAutoCall()">Trigger Auto-Call</button><button class="btn" onclick="triggerFollowups()">Process Follow-ups</button></div></div>
<div class="card"><h3>Recent Calls</h3><div style="overflow-x:auto"><table><tr><th>Business</th><th>Phone</th><th>Status</th><th>Outcome</th><th>Duration</th><th>WA</th></tr><tbody id="tbl"></tbody></table></div></div>
<script>var calls={calls_json};document.getElementById("tbl").innerHTML=calls.map(function(c){{var badge={{"interested":"badge-green","subscribed":"badge-yellow","not_interested":"badge-red","callback_requested":"badge-blue"}}[c.outcome]||"badge-gray";return "<tr><td>"+(c.business_name||"-")+"</td><td>"+(c.recipient_phone||"-")+"</td><td>"+c.call_status+"</td><td><span class=\\"badge "+badge+"\\">"+(c.outcome||"-")+"</span></td><td>"+(c.call_duration_seconds?c.call_duration_seconds+"s":"-")+"</td><td>"+(c.whatsapp_sent?"Yes":"-")+"</td></tr>"}}).join("");
async function triggerAutoCall(){{var r=await fetch("/api/cron/voice-auto-call?pwd=kalpdev2024",{{method:"POST"}});var d=await r.json();alert(d.message||JSON.stringify(d));location.reload()}}
async function triggerFollowups(){{var r=await fetch("/api/cron/voice-followups?pwd=kalpdev2024",{{method:"POST"}});var d=await r.json();alert(d.message||JSON.stringify(d));location.reload()}}</script></body></html>'''
    return HTMLResponse(content=html)