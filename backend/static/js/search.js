async function pubSearch(){
  var biz=document.getElementById("sBiz").value.trim();
  var area=document.getElementById("sArea").value.trim();
  var country=document.getElementById("sCountry").value;
  if(!biz)return;
  var r=document.getElementById("searchResult");
  r.innerHTML="<p style='text-align:center;color:#64748b;font-size:.75rem'>Finding your website...</p>";
  try{
    var query=biz+(area?" "+area:"")+(country?" "+country:"");
    var resp=await fetch("/api/leads/public-search?query="+encodeURIComponent(query));
    var data=await resp.json();
    if(data.results&&data.results.length>0){
      var html="<div style='max-height:350px;overflow-y:auto;text-align:left'>";
      data.results.forEach(function(b){
        if(b.has_website && b.slug){
          html+="<div style='padding:10px 12px;border:1px solid rgba(34,197,94,.2);background:rgba(34,197,94,.04);border-radius:8px;margin-bottom:6px'><p style='font-size:.82rem;font-weight:600;color:#e2e8f0'>"+b.name+"</p><p style='font-size:.68rem;color:#64748b;margin-top:2px'>"+(b.address||"").substring(0,45)+"</p>"+(b.phone?"<p style='font-size:.68rem;color:#94a3b8;margin-top:2px'>"+b.phone+"</p>":"")+"<a href='https://"+b.slug+".city-maps.online' target='_blank' style='display:inline-block;margin-top:6px;font-size:.7rem;color:#22c55e;font-weight:700;background:rgba(34,197,94,.1);padding:4px 10px;border-radius:6px;text-decoration:none'>View Site &rarr;</a></div>";
        } else {
          html+="<div onclick=\"selectBiz(this)\" data-name=\""+b.name.replace(/"/g,'&quot;')+"\" data-phone=\""+(b.phone||"")+"\" data-address=\""+(b.address||"").replace(/"/g,'&quot;')+"\" data-category=\""+(b.category||biz)+"\" style='padding:10px 12px;border:1px solid rgba(255,255,255,.06);border-radius:8px;margin-bottom:6px;cursor:pointer' onmouseover=\"this.style.borderColor='rgba(0,229,255,.3)'\" onmouseout=\"this.style.borderColor='rgba(255,255,255,.06)'\"><p style='font-size:.82rem;font-weight:600;color:#e2e8f0'>"+b.name+"</p><p style='font-size:.68rem;color:#64748b;margin-top:2px'>"+(b.address||"").substring(0,45)+"</p>"+(b.phone?"<p style='font-size:.68rem;color:#94a3b8;margin-top:2px'>"+b.phone+"</p>":"")+"<span style='display:inline-block;margin-top:6px;font-size:.7rem;color:#00e5ff;font-weight:600;background:rgba(0,229,255,.08);padding:4px 10px;border-radius:6px'>Find Link</span></div>";
        }
      });
      html+="</div>";
      r.innerHTML="";
      Swal.fire({title:data.results.length+" businesses found",html:html,showConfirmButton:false,showCloseButton:true,background:"#0f172a",color:"#fff",width:"92%"});
    }else{
      r.innerHTML="<div style='padding:12px;margin-top:8px;text-align:center;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px'><p style='font-size:.78rem;color:#e2e8f0;margin-bottom:6px'>No results found</p><p style='font-size:.7rem;color:#64748b'>Try a different name or area</p></div>";
    }
  }catch(e){
    r.innerHTML="<div style='padding:12px;margin-top:8px;text-align:center'><p style='font-size:.75rem;color:#ef4444'>Search failed. Try again.</p></div>";
  }
}

async function selectBiz(el){
  var name=el.dataset.name;
  var phone=el.dataset.phone;
  var address=el.dataset.address;
  var category=el.dataset.category;
  Swal.fire({title:"Finding website link...",html:"<p style='font-size:.8rem;color:#64748b'>"+name+"</p><div style='margin-top:12px;width:40px;height:40px;border:3px solid rgba(0,229,255,.2);border-top:3px solid #00e5ff;border-radius:50%;animation:spin 1s linear infinite;margin:12px auto'></div><style>@keyframes spin{to{transform:rotate(360deg)}}</style>",showConfirmButton:false,allowOutsideClick:false,background:"#0f172a",color:"#fff"});
  try{
    var resp=await fetch("/api/leads/public-create-site",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({business_name:name,phone:phone,address:address,category:category})});
    var data=await resp.json();
    if(data.slug){
      Swal.fire({icon:"success",title:"Website Ready!",html:"<p style='font-size:.85rem'>Check your <b>WhatsApp</b> for details.</p><p style='font-size:.75rem;color:#64748b;margin-top:8px'>"+data.slug+".city-maps.online</p>",confirmButtonText:"Open Website",confirmButtonColor:"#00e5ff",showCancelButton:true,cancelButtonText:"Close",background:"#0f172a",color:"#fff"}).then(function(result){if(result.isConfirmed){window.open("https://"+data.slug+".city-maps.online","_blank");}});
    }else{
      Swal.fire({icon:"info",title:"Processing",text:data.message||"Website creation in progress.",background:"#0f172a",color:"#fff"});
    }
  }catch(e){
    Swal.fire({icon:"error",title:"Failed",text:"Please try again.",background:"#0f172a",color:"#fff"});
  }
}

// Auto-detect user location
if(navigator.geolocation){
  navigator.geolocation.getCurrentPosition(function(pos){
    fetch("https://nominatim.openstreetmap.org/reverse?lat="+pos.coords.latitude+"&lon="+pos.coords.longitude+"&format=json").then(function(r){return r.json()}).then(function(d){
      var city=d.address.city||d.address.town||d.address.village||d.address.county||"";
      if(city&&document.getElementById("sArea")){
        document.getElementById("sArea").placeholder=city+" (nearby)";
      }
    }).catch(function(){});
  },function(){},{timeout:5000});
}

document.addEventListener('mousemove',function(e){
  var x=(e.clientX/window.innerWidth-0.5)*20;
  var y=(e.clientY/window.innerHeight-0.5)*20;
  var g=document.querySelectorAll('.bg-depth .glow-1,.bg-depth .glow-2,.bg-depth .glow-3');
  g.forEach(function(el,i){var f=(i+1)*0.5;el.style.transform='translate('+x*f+'px,'+y*f+'px)';});
});