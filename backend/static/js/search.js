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
      var html="<div class='glass' style='padding:12px;margin-top:8px;max-height:300px;overflow-y:auto'><p style='font-size:.7rem;color:#64748b;margin-bottom:8px'>"+data.results.length+" businesses found:</p>";
      data.results.forEach(function(b){
        if(b.has_website && b.slug){
          // Already has website - show link directly
          html+="<div style='display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border:1px solid rgba(34,197,94,.2);background:rgba(34,197,94,.04);border-radius:8px;margin-bottom:6px'><div><p style='font-size:.78rem;font-weight:600;color:#e2e8f0'>"+b.name+"</p><p style='font-size:.65rem;color:#64748b;margin-top:2px'>"+(b.address||"").substring(0,45)+"</p>"+(b.phone?"<p style='font-size:.65rem;color:#94a3b8;margin-top:2px'>&#128222; "+b.phone+"</p>":"")+"</div><a href='https://"+b.slug+".city-maps.online' target='_blank' style='font-size:.65rem;color:#22c55e;font-weight:700;background:rgba(34,197,94,.1);padding:6px 12px;border-radius:6px;text-decoration:none;white-space:nowrap'>View Site &rarr;</a></div>";
        } else {
          // No website yet - show select button
          html+="<div onclick=\"selectBiz(this)\" data-name=\""+b.name.replace(/"/g,'&quot;')+"\" data-phone=\""+(b.phone||"")+"\" data-address=\""+(b.address||"").replace(/"/g,'&quot;')+"\" data-category=\""+(b.category||biz)+"\" style='display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border:1px solid rgba(255,255,255,.06);border-radius:8px;margin-bottom:6px;cursor:pointer;transition:all .2s' onmouseover=\"this.style.borderColor='rgba(0,229,255,.3)'\" onmouseout=\"this.style.borderColor='rgba(255,255,255,.06)'\"><div><p style='font-size:.78rem;font-weight:600;color:#e2e8f0'>"+b.name+"</p><p style='font-size:.65rem;color:#64748b;margin-top:2px'>"+(b.address||"").substring(0,45)+"</p>"+(b.phone?"<p style='font-size:.65rem;color:#94a3b8;margin-top:2px'>&#128222; "+b.phone+"</p>":"")+"</div><span style='font-size:.65rem;color:#00e5ff;font-weight:600;background:rgba(0,229,255,.08);padding:6px 12px;border-radius:6px;white-space:nowrap'>Find Link</span></div>";
        }
      });
      html+="</div>";
      r.innerHTML=html;
    }else{
      r.innerHTML="<div class='glass' style='padding:14px;margin-top:8px;text-align:center'><p style='font-size:.78rem;color:#e2e8f0;margin-bottom:6px'>No results found</p><p style='font-size:.7rem;color:#64748b'>Try a different name or area</p></div>";
    }
  }catch(e){
    r.innerHTML="<div class='glass' style='padding:12px;margin-top:8px;text-align:center'><p style='font-size:.75rem;color:#ef4444'>Search failed. Try again.</p></div>";
  }
}

async function selectBiz(el){
  var name=el.dataset.name;
  var phone=el.dataset.phone;
  var address=el.dataset.address;
  var category=el.dataset.category;
  var r=document.getElementById("searchResult");
  r.innerHTML="<div class='glass' style='padding:14px;margin-top:8px;text-align:center'><p style='font-size:.78rem;color:#00e5ff;font-weight:600'>&#9889; Finding website link for "+name+"...</p><p style='font-size:.7rem;color:#64748b;margin-top:4px'>Please wait a moment...</p><div style='margin-top:12px;width:40px;height:40px;border:3px solid rgba(0,229,255,.2);border-top:3px solid #00e5ff;border-radius:50%;animation:spin 1s linear infinite;margin:12px auto'></div></div><style>@keyframes spin{to{transform:rotate(360deg)}}</style>";
  try{
    var resp=await fetch("/api/leads/public-create-site",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({business_name:name,phone:phone,address:address,category:category})});
    var data=await resp.json();
    if(data.slug){
      r.innerHTML="";
      Swal.fire({icon:'success',title:'Done!',html:'<p style="font-size:.9rem">Check your <b>WhatsApp</b> for website details and link.</p><p style="font-size:.75rem;color:#64748b;margin-top:8px">Your site: <b>'+data.slug+'.city-maps.online</b></p>',confirmButtonText:'Open Website',confirmButtonColor:'#00e5ff',showCancelButton:true,cancelButtonText:'Close',background:'#0f172a',color:'#fff'}).then(function(result){if(result.isConfirmed){window.open('https://'+data.slug+'.city-maps.online','_blank');}});
    }else{
      r.innerHTML="<div class='glass' style='padding:12px;margin-top:8px;text-align:center'><p style='font-size:.75rem;color:#f59e0b'>"+(data.message||"Website creation in progress. Check back soon!")+"</p></div>";
    }
  }catch(e){
    r.innerHTML="<div class='glass' style='padding:12px;margin-top:8px;text-align:center'><p style='font-size:.75rem;color:#ef4444'>Failed to create. Please try again.</p></div>";
  }
}

document.addEventListener('mousemove',function(e){
  var x=(e.clientX/window.innerWidth-0.5)*20;
  var y=(e.clientY/window.innerHeight-0.5)*20;
  var g=document.querySelectorAll('.bg-depth .glow-1,.bg-depth .glow-2,.bg-depth .glow-3');
  g.forEach(function(el,i){var f=(i+1)*0.5;el.style.transform='translate('+x*f+'px,'+y*f+'px)';});
});
// Auto-detect user location
if(navigator.geolocation){
  navigator.geolocation.getCurrentPosition(function(pos){
    fetch("https://nominatim.openstreetmap.org/reverse?lat="+pos.coords.latitude+"&lon="+pos.coords.longitude+"&format=json").then(function(r){return r.json()}).then(function(d){
      var city=d.address.city||d.address.town||d.address.village||d.address.county||"";
      if(city&&document.getElementById("sArea")){
        document.getElementById("sArea").value=city;
        document.getElementById("sArea").placeholder=city+" (detected)";
      }
    }).catch(function(){});
  },function(){},{timeout:5000});
}