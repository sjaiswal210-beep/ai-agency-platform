async function pubSearch(){
  var biz=document.getElementById("sBiz").value.trim();
  var area=document.getElementById("sArea").value.trim();
  var country=document.getElementById("sCountry").value;
  if(!biz)return;
  var r=document.getElementById("searchResult");
  r.innerHTML="";Swal.fire({title:"Finding your website...",html:"<div style='margin-top:12px;width:40px;height:40px;border:3px solid rgba(0,229,255,.2);border-top:3px solid #00e5ff;border-radius:50%;animation:spin 1s linear infinite;margin:12px auto'></div><style>@keyframes spin{to{transform:rotate(360deg)}}</style>",showConfirmButton:false,allowOutsideClick:false,background:"#0f172a",color:"#fff"});
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
      Swal.fire({icon:"info",title:"No results found",text:"Try a different business name or area.",background:"#0f172a",color:"#fff"});
    }
  }catch(e){
    Swal.fire({icon:"error",title:"Search failed",text:"Please try again.",background:"#0f172a",color:"#fff"});
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
      Swal.fire({icon:"success",title:"Your Website Is Ready!",html:"<p style='font-size:.9rem;margin-bottom:10px'>Your website is:<br><b style='color:#00e5ff;font-size:1rem'>"+data.slug+".city-maps.online</b></p><p style='font-size:.75rem;color:#64748b'>Details shared on WhatsApp</p>",confirmButtonText:"Open Website",confirmButtonColor:"#22c55e",showCancelButton:true,cancelButtonText:"Close",background:"#0f172a",color:"#fff"}).then(function(result){if(result.isConfirmed){window.open("https://"+data.slug+".city-maps.online","_blank");}});
    }else{
      Swal.fire({icon:"info",title:"Processing",text:data.message||"Website creation in progress.",background:"#0f172a",color:"#fff"});
    }
  }catch(e){
    Swal.fire({icon:"error",title:"Failed",text:"Please try again.",background:"#0f172a",color:"#fff"});
  }
}


});