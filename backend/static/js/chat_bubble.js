(function(){
  function ensureBubble(){
    if(document.getElementById("chatBubble"))return;
    var s=document.createElement("style");
    s.textContent="@keyframes chatPulse{0%,100%{box-shadow:0 4px 16px rgba(99,102,241,.4)}50%{box-shadow:0 4px 24px rgba(99,102,241,.7),0 0 0 8px rgba(99,102,241,.1)}}";
    document.head.appendChild(s);
    var b=document.createElement("div");
    b.id="chatBubble";
    b.innerHTML="&#128172;";
    b.style.cssText="position:fixed;bottom:70px;right:14px;width:54px;height:54px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 20px rgba(99,102,241,.5);z-index:99999;font-size:24px;animation:chatPulse 2s ease infinite";
    b.onclick=toggleChat;
    document.body.appendChild(b);
  }
  window.toggleChat=function(){
    var p=document.getElementById("chatPanel");
    if(!p)return;
    p.style.display=(p.style.display==="flex")?"none":"flex";
    if(p.style.display==="flex")p.style.flexDirection="column";
  };
  window.sendChat=function(){
    var inp=document.getElementById("chatIn");
    if(!inp)return;
    var q=inp.value.trim();
    if(!q)return;
    inp.value="";
    var msgs=document.getElementById("chatMsgs");
    msgs.innerHTML+='<div style="text-align:right;margin-bottom:6px"><span style="background:rgba(99,102,241,.25);padding:6px 10px;border-radius:10px;font-size:.72rem;display:inline-block">'+q+'</span></div>';
    msgs.innerHTML+='<div id="typing" style="margin-bottom:6px;color:#64748b;font-size:.68rem">Thinking...</div>';
    msgs.scrollTop=msgs.scrollHeight;
    var wid=window._wid||"";
    fetch("https://ai-agency-platform.onrender.com/api/panel/"+wid+"/assistant-ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q})})
      .then(function(r){return r.json()})
      .then(function(d){
        var t=document.getElementById("typing");if(t)t.remove();
        var ans=(d.answer||d.reply||"No response").split(String.fromCharCode(10)).join("<br>");
        msgs.innerHTML+='<div style="margin-bottom:6px"><span style="background:rgba(255,255,255,.06);padding:6px 10px;border-radius:10px;font-size:.72rem;display:inline-block;max-width:85%">'+ans+'</span></div>';
        msgs.scrollTop=msgs.scrollHeight;
      })
      .catch(function(){var t=document.getElementById("typing");if(t)t.textContent="Error. Try again.";});
  };
  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",ensureBubble);
  }else{
    ensureBubble();
  }
})();