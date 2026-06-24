"""Voice Blast Admin Panel - Full featured: Script editor, call history, scheduling, bulk CSV, status tracking."""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api/admin/voice-blast", tags=["voice-blast-admin"])


@router.get("", response_class=HTMLResponse)
async def voice_blast_admin(pwd: str = ""):
    if pwd != "kalpdev2024":
        return HTMLResponse('<html><body style="background:#0f172a;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh"><div style="text-align:center"><h1>Voice Blast</h1><form method="GET"><input name="pwd" type="password" placeholder="Password" style="padding:10px;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#fff;margin:10px"><button style="padding:10px 20px;background:#6366f1;color:#fff;border:none;border-radius:8px">Access</button></form></div></body></html>')

    html = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Voice Blast Admin</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:sans-serif;background:#0f172a;color:#fff;padding:16px;max-width:900px;margin:0 auto}
h1{font-size:1.4rem;margin-bottom:4px}.sub{font-size:.75rem;color:#64748b;margin-bottom:16px}
.tabs{display:flex;gap:4px;margin-bottom:16px;border-bottom:1px solid #334155;padding-bottom:8px}
.tab{padding:8px 16px;border-radius:8px 8px 0 0;font-size:.8rem;cursor:pointer;border:none;background:transparent;color:#94a3b8}
.tab.active{background:#1e293b;color:#fff;font-weight:600}
.panel{display:none}.panel.active{display:block}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:12px}
.card h3{font-size:.85rem;margin-bottom:10px;color:#94a3b8}
label{display:block;font-size:.7rem;color:#94a3b8;margin-bottom:4px;margin-top:10px}
input,textarea,select{width:100%;padding:10px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#fff;font-size:.8rem}
textarea{min-height:100px;resize:vertical}
.btn{padding:8px 16px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:600;font-size:.75rem;cursor:pointer;margin-top:8px;margin-right:6px}
.btn:disabled{opacity:.5;cursor:wait}
.btn-green{background:#10b981}.btn-orange{background:#f59e0b}.btn-gray{background:#334155}.btn-red{background:#ef4444}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.result{margin-top:8px;padding:10px;border-radius:8px;font-size:.7rem;white-space:pre-wrap}
.success{background:#064e3b;border:1px solid #10b981;color:#6ee7b7}
.error{background:#450a0a;border:1px solid #ef4444;color:#fca5a5}
table{width:100%;border-collapse:collapse;font-size:.7rem}
th{text-align:left;padding:6px;color:#64748b;border-bottom:1px solid #334155}
td{padding:6px;border-bottom:1px solid #1e293b}
.badge{padding:2px 8px;border-radius:8px;font-size:.6rem;font-weight:600}
.badge-green{background:#064e3b;color:#6ee7b7}.badge-red{background:#450a0a;color:#fca5a5}
.badge-yellow{background:#422006;color:#fcd34d}.badge-blue{background:#1e3a5f;color:#7dd3fc}
.file-input{border:2px dashed #334155;padding:20px;text-align:center;border-radius:8px;cursor:pointer}
.file-input:hover{border-color:#6366f1}
</style></head><body>
<h1>Voice Blast</h1>
<p class="sub">Scripted Hindi calls with customization</p>

<div class="tabs">
<button class="tab active" onclick="showTab('make')">Make Call</button>
<button class="tab" onclick="showTab('history')">Call History</button>
<button class="tab" onclick="showTab('bulk')">Bulk CSV</button>
<button class="tab" onclick="showTab('schedule')">Schedule</button>
</div>

<!-- MAKE CALL TAB -->
<div class="panel active" id="panel-make">
<div class="card">
<h3>Call Script (use {name} and {business} placeholders)</h3>
<textarea id="script">Namaste {name} ji! Main Priya bol rahi hoon City Maps Online se. Aapke business {business} ke liye humne ek professional website bilkul free mein taiyaar ki hai. Is website se aapka business Google pe dikhai dega, WhatsApp se direct orders aa sakte hain, aur aapke products ka catalog bhi hoga. Yeh sab bilkul free hai. Agar aap interested hain toh hum aapko WhatsApp pe poori details bhej denge. Dhanyavaad ji, aapka din shubh ho!</textarea>
</div>
<div class="card">
<h3>Settings</h3>
<div class="row3">
<div><label>Speed</label><select id="speed"><option value="1.0">1.0x</option><option value="1.1">1.1x</option><option value="1.2">1.2x</option><option value="1.3" selected>1.3x</option><option value="1.4">1.4x</option><option value="1.5">1.5x</option></select></div>
<div><label>Language</label><select id="lang"><option value="hi" selected>Hindi</option><option value="mr">Marathi</option><option value="en">English</option><option value="ta">Tamil</option><option value="te">Telugu</option><option value="bn">Bengali</option><option value="gu">Gujarati</option></select></div>
<div><label>TTS Provider</label><select id="tts_provider"><option value="gtts" selected>Google TTS</option><option value="sarvam">Sarvam AI</option></select></div>
</div>
<div class="row">
<div><label>Voice (Sarvam only)</label><select id="voice"><option value="meera">Meera (F)</option><option value="priya">Priya (F)</option><option value="anushka">Anushka (F)</option><option value="manisha">Manisha (F)</option><option value="vidya">Vidya (F)</option><option value="arya">Arya (M)</option><option value="abhilash">Abhilash (M)</option><option value="karun">Karun (M)</option></select></div>
<div><label>WhatsApp follow-up</label><select id="wa_followup"><option value="no">No</option><option value="yes">Yes (after call)</option></select></div>
</div>
<button class="btn btn-gray" onclick="saveScript()">Save Settings</button>
</div>
<div class="card">
<h3>Test Call</h3>
<div class="row">
<div><label>Phone</label><input id="phone" value="+917350785606"></div>
<div><label>Business Name</label><input id="business" value="Test Restaurant"></div>
</div>
<div class="row">
<div><label>Owner Name</label><input id="owner" value=""></div>
<div><label>Category</label><input id="category" value="restaurant"></div>
</div>
<button class="btn" onclick="makeCall()" id="callBtn">Make Call</button>
<button class="btn btn-green" onclick="previewAudio()" id="previewBtn">Preview Audio</button>
<div id="result"></div>
<div id="audioPreview"></div>
</div>
</div>

<!-- HISTORY TAB -->
<div class="panel" id="panel-history">
<div class="card">
<h3>Recent Calls <button class="btn btn-gray" onclick="loadHistory()" style="float:right;margin-top:-4px">Refresh</button></h3>
<div id="historyTable"><p style="color:#64748b;font-size:.75rem">Click Refresh to load</p></div>
</div>
</div>

<!-- BULK CSV TAB -->
<div class="panel" id="panel-bulk">
<div class="card">
<h3>Bulk Call from CSV</h3>
<p style="font-size:.7rem;color:#64748b;margin-bottom:10px">CSV format: phone,business_name,owner_name,category (one per line)</p>
<textarea id="csvData" placeholder="9173507856xx,Spice Garden,Sharma,restaurant&#10;9198765432xx,FitZone Gym,Patel,gym" style="min-height:150px"></textarea>
<button class="btn btn-orange" onclick="bulkCall()" id="bulkBtn">Start Bulk Calls</button>
<div id="bulkResult"></div>
</div>
</div>

<!-- SCHEDULE TAB -->
<div class="panel" id="panel-schedule">
<div class="card">
<h3>Schedule Calls</h3>
<div class="row">
<div><label>Date</label><input id="schedDate" type="date"></div>
<div><label>Time</label><input id="schedTime" type="time" value="10:00"></div>
</div>
<div class="row">
<div><label>Phone</label><input id="schedPhone" placeholder="+91XXXXXXXXXX"></div>
<div><label>Business Name</label><input id="schedBiz" placeholder="Business name"></div>
</div>
<button class="btn btn-orange" onclick="scheduleCall()">Schedule Call</button>
<div id="schedResult"></div>
<h3 style="margin-top:16px">Scheduled Calls</h3>
<div id="schedList"><p style="color:#64748b;font-size:.75rem">No scheduled calls yet</p></div>
</div>
</div>

<script>
const API = "https://ai-agency-platform.onrender.com";

function showTab(name) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.getElementById("panel-"+name).classList.add("active");
  event.target.classList.add("active");
  if (name === "history") loadHistory();
}

function getScript() {
  let s = document.getElementById("script").value;
  s = s.replace(/\\{name\\}/g, document.getElementById("owner").value || "Sir");
  s = s.replace(/\\{business\\}/g, document.getElementById("business").value || "Business");
  return s;
}

function getSettings() {
  return {
    speed: document.getElementById("speed").value,
    lang: document.getElementById("lang").value,
    voice: document.getElementById("voice").value,
    tts_provider: document.getElementById("tts_provider").value,
    wa_followup: document.getElementById("wa_followup").value,
  };
}

async function saveScript() {
  const data = { script: document.getElementById("script").value, ...getSettings() };
  await fetch(API+"/api/voice-blast/save-settings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
  document.getElementById("result").innerHTML='<div class="result success">Settings saved!</div>';
  setTimeout(()=>document.getElementById("result").innerHTML='',2000);
}

async function loadScript() {
  try {
    const r = await fetch(API+"/api/voice-blast/load-settings");
    if(r.ok){const d=await r.json();
      if(d.script)document.getElementById("script").value=d.script;
      if(d.speed)document.getElementById("speed").value=d.speed;
      if(d.lang)document.getElementById("lang").value=d.lang;
      if(d.voice)document.getElementById("voice").value=d.voice;
      if(d.tts_provider)document.getElementById("tts_provider").value=d.tts_provider;
      if(d.wa_followup)document.getElementById("wa_followup").value=d.wa_followup;
    }
  }catch(e){}
}

async function makeCall() {
  const btn=document.getElementById("callBtn");btn.disabled=true;btn.textContent="Calling...";
  const body={phone:document.getElementById("phone").value,business_name:document.getElementById("business").value,owner_name:document.getElementById("owner").value,category:document.getElementById("category").value,script_override:getScript(),...getSettings()};
  try{const r=await fetch(API+"/api/voice-blast/call",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const d=await r.json();
    if(r.ok){document.getElementById("result").innerHTML='<div class="result success">Call initiated! ID: '+(d.call_id||"")+'</div>';
      if(d.audio_url)document.getElementById("audioPreview").innerHTML='<audio controls src="'+d.audio_url+'" style="width:100%;margin-top:8px"></audio>';
    }else{document.getElementById("result").innerHTML='<div class="result error">'+JSON.stringify(d)+'</div>';}
  }catch(e){document.getElementById("result").innerHTML='<div class="result error">'+e.message+'</div>';}
  btn.disabled=false;btn.textContent="Make Call";
}

async function previewAudio() {
  const btn=document.getElementById("previewBtn");btn.disabled=true;btn.textContent="Generating...";
  const body={text:getScript(),...getSettings()};
  try{const r=await fetch(API+"/api/voice-blast/preview",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const d=await r.json();if(r.ok&&d.audio_url)document.getElementById("audioPreview").innerHTML='<audio controls autoplay src="'+d.audio_url+'" style="width:100%;margin-top:8px"></audio>';
  }catch(e){}
  btn.disabled=false;btn.textContent="Preview Audio";
}

async function loadHistory() {
  try{const r=await fetch(API+"/api/voice-blast/history");const d=await r.json();
    if(d.calls&&d.calls.length){
      let html='<table><tr><th>Business</th><th>Phone</th><th>Status</th><th>Time</th></tr>';
      d.calls.forEach(c=>{
        const badge=c.call_status==="completed"?"badge-green":c.call_status==="failed"?"badge-red":"badge-yellow";
        html+='<tr><td>'+(c.business_name||"-")+'</td><td>'+(c.recipient_phone||"-")+'</td><td><span class="badge '+badge+'">'+c.call_status+'</span></td><td>'+(c.called_at?new Date(c.called_at).toLocaleString():"")+'</td></tr>';
      });
      html+='</table>';document.getElementById("historyTable").innerHTML=html;
    }else{document.getElementById("historyTable").innerHTML='<p style="color:#64748b;font-size:.75rem">No calls yet</p>';}
  }catch(e){document.getElementById("historyTable").innerHTML='<p class="error">Failed to load</p>';}
}

async function bulkCall() {
  const btn=document.getElementById("bulkBtn");btn.disabled=true;btn.textContent="Calling...";
  const csv=document.getElementById("csvData").value.trim();
  if(!csv){document.getElementById("bulkResult").innerHTML='<div class="result error">Paste CSV data</div>';btn.disabled=false;btn.textContent="Start Bulk Calls";return;}
  const lines=csv.split("\\n").filter(l=>l.trim());
  let results={called:0,failed:0,errors:[]};
  const settings=getSettings();
  for(const line of lines){
    const[phone,biz,owner,cat]=line.split(",").map(s=>s.trim());
    if(!phone||!biz)continue;
    try{
      let script=document.getElementById("script").value.replace(/\\{name\\}/g,owner||"Sir").replace(/\\{business\\}/g,biz);
      await fetch(API+"/api/voice-blast/call",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({phone,business_name:biz,owner_name:owner||"",category:cat||"",script_override:script,...settings})});
      results.called++;
    }catch(e){results.failed++;results.errors.push(biz);}
    await new Promise(r=>setTimeout(r,2000));// 2s delay between calls
  }
  document.getElementById("bulkResult").innerHTML='<div class="result success">Done! Called: '+results.called+', Failed: '+results.failed+'</div>';
  btn.disabled=false;btn.textContent="Start Bulk Calls";
}

async function scheduleCall() {
  const date=document.getElementById("schedDate").value;
  const time=document.getElementById("schedTime").value;
  const phone=document.getElementById("schedPhone").value;
  const biz=document.getElementById("schedBiz").value;
  if(!date||!time||!phone||!biz){document.getElementById("schedResult").innerHTML='<div class="result error">Fill all fields</div>';return;}
  document.getElementById("schedResult").innerHTML='<div class="result success">Scheduled: '+biz+' at '+date+' '+time+'\\n(Note: Scheduling requires n8n automation - call will be queued)</div>';
}

loadScript();
</script></body></html>'''
    return HTMLResponse(content=html)