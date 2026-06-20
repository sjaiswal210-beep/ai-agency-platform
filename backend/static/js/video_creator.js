function genScript(){
  var b=document.getElementById("blurb");
  var btn=document.getElementById("scriptBtn");
  var kw=b.value.trim()||window._cat;
  btn.disabled=true;btn.textContent="Generating...";
  b.value="Generating 6 scenes...";b.style.opacity="0.5";
  fetch("/api/video/"+window._wid+"/generate-script",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({blurb:kw,business_name:window._bname,category:window._cat})}).then(function(r){return r.json()}).then(function(d){
    b.style.opacity="1";
    if(d.script){b.value=d.script.map(function(s,i){return"Scene "+(i+1)+": "+s}).join(String.fromCharCode(10,10));}
    else{b.value="Could not generate. Write your own scenes.";}
    btn.disabled=false;btn.textContent="Generate Script";
  }).catch(function(){
    b.style.opacity="1";b.value="Error. Try again or write your own.";
    btn.disabled=false;btn.textContent="Generate Script";
  });
}

function genVideo(){
  var btn=document.getElementById("genBtn");
  var ct=document.getElementById("customText").value.trim();
  var prompt=document.getElementById("blurb").value.trim();
  if(!prompt){alert("Add a script first");return;}
  btn.disabled=true;btn.textContent="Generating...";
  var ov=document.createElement("div");ov.id="vidOverlay";
  ov.style.cssText="position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px";
  ov.innerHTML='<div style="background:#1e293b;border-radius:16px;padding:24px;text-align:center;max-width:300px;width:90%"><div style="width:36px;height:36px;border:3px solid rgba(99,102,241,.2);border-top:3px solid #6366f1;border-radius:50%;animation:sp 1s linear infinite;margin:0 auto 12px"></div><p style="font-size:.85rem;font-weight:700;color:#fff">Generating Video</p><p style="font-size:.7rem;color:#94a3b8;margin-top:6px">Creating 6 scenes (4-6 min)</p><style>@keyframes sp{to{transform:rotate(360deg)}}</style></div>';
  document.body.appendChild(ov);
  fetch("/api/video/"+window._wid+"/generate-free",{method:"POST",signal:AbortSignal.timeout(600000),headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt:prompt,custom_text:ct})}).then(function(r){return r.json()}).then(function(d){
    var ov2=document.getElementById("vidOverlay");
    if(d.status==="completed"&&(d.video_url||d.clips)){
      var vurl=d.video_url||(d.clips&&d.clips[0])||"";
      ov2.innerHTML='<div style="background:#1e293b;border-radius:16px;padding:16px;max-width:380px;width:92%;text-align:center;position:relative"><button onclick="this.parentNode.parentNode.remove()" style="position:absolute;top:8px;right:12px;background:none;border:none;color:#94a3b8;font-size:1.2rem;cursor:pointer">&times;</button><p style="font-size:.9rem;font-weight:700;color:#fff;margin:8px 0 10px">Video Ready!</p><video src="'+vurl+'" controls autoplay playsinline style="width:100%;border-radius:10px;margin-bottom:10px"></video><a href="'+vurl+'" download style="display:block;padding:12px;background:#22c55e;border-radius:10px;color:#fff;font-weight:700;text-decoration:none">Download Video</a></div>';
    }else{
      ov2.innerHTML='<div style="background:#1e293b;border-radius:16px;padding:20px;max-width:280px;width:90%;text-align:center"><p style="color:#ef4444;font-weight:600">Failed</p><p style="font-size:.72rem;color:#94a3b8;margin:8px 0">'+(d.message||"Try again")+'</p><button onclick="this.parentNode.parentNode.remove()" style="padding:8px 16px;background:#334155;border:none;border-radius:8px;color:#fff;cursor:pointer">Close</button></div>';
    }
    btn.disabled=false;btn.textContent="Generate 30-sec Video";
  }).catch(function(e){
    var ov3=document.getElementById("vidOverlay");
    if(ov3)ov3.innerHTML='<div style="background:#1e293b;border-radius:16px;padding:20px;max-width:280px;width:90%;text-align:center"><p style="color:#ef4444">Error</p><button onclick="this.parentNode.parentNode.remove()" style="margin-top:10px;padding:8px 16px;background:#334155;border:none;border-radius:8px;color:#fff;cursor:pointer">Close</button></div>';
    btn.disabled=false;btn.textContent="Generate 30-sec Video";
  });
}
