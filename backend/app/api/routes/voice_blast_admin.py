"""Voice Blast Admin Panel - Test calls with script editor, speed & voice selection."""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api/admin/voice-blast", tags=["voice-blast-admin"])


@router.get("", response_class=HTMLResponse)
async def voice_blast_admin(pwd: str = ""):
    if pwd != "kalpdev2024":
        return HTMLResponse('<html><body style="background:#0f172a;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh"><div style="text-align:center"><h1>Voice Blast</h1><form method="GET"><input name="pwd" type="password" placeholder="Password" style="padding:10px;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#fff;margin:10px"><button style="padding:10px 20px;background:#6366f1;color:#fff;border:none;border-radius:8px">Access</button></form></div></body></html>')

    html = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Voice Blast Admin</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:sans-serif;background:#0f172a;color:#fff;padding:20px;max-width:700px;margin:0 auto}
h1{font-size:1.4rem;margin-bottom:4px}.sub{font-size:.75rem;color:#64748b;margin-bottom:20px}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin-bottom:12px}
.card h3{font-size:.85rem;margin-bottom:10px;color:#94a3b8}
label{display:block;font-size:.7rem;color:#94a3b8;margin-bottom:4px;margin-top:10px}
input,textarea,select{width:100%;padding:10px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#fff;font-size:.8rem}
textarea{min-height:120px;resize:vertical}
.btn{padding:10px 20px;background:#6366f1;color:#fff;border:none;border-radius:8px;font-weight:600;font-size:.8rem;cursor:pointer;margin-top:12px}
.btn:disabled{opacity:.5;cursor:wait}
.btn-green{background:#10b981}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.result{margin-top:12px;padding:12px;border-radius:8px;font-size:.75rem;white-space:pre-wrap}
.success{background:#064e3b;border:1px solid #10b981;color:#6ee7b7}
.error{background:#450a0a;border:1px solid #ef4444;color:#fca5a5}
.audio-preview{margin-top:10px}
</style></head><body>
<h1>Voice Blast</h1>
<p class="sub">Test scripted Hindi calls with customizable voice settings</p>

<div class="card">
<h3>Call Script (Hindi)</h3>
<label>Script Template (use {name}, {business} as placeholders)</label>
<textarea id="script">Namaste {name} ji! Main Priya bol rahi hoon City Maps Online se. Aapke business {business} ke liye humne ek professional website bilkul free mein taiyaar ki hai. Is website se aapka business Google pe dikhai dega, WhatsApp se direct orders aa sakte hain, aur aapke products ka catalog bhi hoga. Yeh sab bilkul free hai. Agar aap interested hain toh hum aapko WhatsApp pe poori details bhej denge. Dhanyavaad ji, aapka din shubh ho!</textarea>
</div>

<div class="card">
<h3>Voice Settings</h3>
<div class="row">
<div>
<label>Speed</label>
<select id="speed">
<option value="1.0">Normal (1.0x)</option>
<option value="1.1">Slightly Fast (1.1x)</option>
<option value="1.2">Fast (1.2x)</option>
<option value="1.3" selected>Quick (1.3x)</option>
<option value="1.4">Very Fast (1.4x)</option>
<option value="1.5">Rapid (1.5x)</option>
</select>
</div>
<div>
<label>Language</label>
<select id="lang">
<option value="hi" selected>Hindi</option>
<option value="mr">Marathi</option>
<option value="en">English</option>
<option value="ta">Tamil</option>
<option value="te">Telugu</option>
<option value="bn">Bengali</option>
<option value="gu">Gujarati</option>
</select>
</div>
</div>
</div>

<div class="card">
<h3>Test Call</h3>
<div class="row">
<div>
<label>Phone Number</label>
<input id="phone" type="tel" value="+917350785606" placeholder="+91XXXXXXXXXX">
</div>
<div>
<label>Business Name</label>
<input id="business" type="text" value="Test Restaurant" placeholder="Business name">
</div>
</div>
<div class="row">
<div>
<label>Owner Name (optional)</label>
<input id="owner" type="text" value="" placeholder="Owner name or leave blank">
</div>
<div>
<label>Category</label>
<input id="category" type="text" value="restaurant" placeholder="Category">
</div>
</div>
<button class="btn" onclick="makeCall()" id="callBtn">Make Test Call</button>
<button class="btn btn-green" onclick="previewAudio()" id="previewBtn">Preview Audio Only</button>
<div id="result"></div>
<div id="audioPreview" class="audio-preview"></div>
</div>

<script>
const API = "https://ai-agency-platform.onrender.com";

function getScript() {
  let s = document.getElementById("script").value;
  const name = document.getElementById("owner").value || "Sir";
  const biz = document.getElementById("business").value || "Business";
  s = s.replace(/\{name\}/g, name).replace(/\{business\}/g, biz);
  return s;
}

async function makeCall() {
  const btn = document.getElementById("callBtn");
  btn.disabled = true; btn.textContent = "Calling...";
  const body = {
    phone: document.getElementById("phone").value,
    business_name: document.getElementById("business").value,
    owner_name: document.getElementById("owner").value,
    category: document.getElementById("category").value,
    script_override: getScript(),
    speed: document.getElementById("speed").value,
    lang: document.getElementById("lang").value,
  };
  try {
    const r = await fetch(API + "/api/voice-blast/call", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const d = await r.json();
    if (r.ok) {
      document.getElementById("result").innerHTML = '<div class="result success">Call initiated!\\nCall ID: '+(d.call_id||"")+'\\nAudio: '+d.audio_url+'</div>';
      if (d.audio_url) document.getElementById("audioPreview").innerHTML = '<audio controls src="'+d.audio_url+'" style="width:100%;margin-top:8px"></audio>';
    } else {
      document.getElementById("result").innerHTML = '<div class="result error">Error: '+JSON.stringify(d)+'</div>';
    }
  } catch(e) { document.getElementById("result").innerHTML = '<div class="result error">'+e.message+'</div>'; }
  btn.disabled = false; btn.textContent = "Make Test Call";
}

async function previewAudio() {
  const btn = document.getElementById("previewBtn");
  btn.disabled = true; btn.textContent = "Generating...";
  const body = {
    text: getScript(),
    speed: document.getElementById("speed").value,
    lang: document.getElementById("lang").value,
  };
  try {
    const r = await fetch(API + "/api/voice-blast/preview", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const d = await r.json();
    if (r.ok && d.audio_url) {
      document.getElementById("audioPreview").innerHTML = '<audio controls autoplay src="'+d.audio_url+'" style="width:100%;margin-top:8px"></audio>';
    } else {
      document.getElementById("result").innerHTML = '<div class="result error">'+JSON.stringify(d)+'</div>';
    }
  } catch(e) { document.getElementById("result").innerHTML = '<div class="result error">'+e.message+'</div>'; }
  btn.disabled = false; btn.textContent = "Preview Audio Only";
}
</script></body></html>'''
    return HTMLResponse(content=html)