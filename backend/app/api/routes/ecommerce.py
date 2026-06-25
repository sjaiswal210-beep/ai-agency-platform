from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from pydantic import BaseModel
from typing import Optional
import json
import hashlib

router = APIRouter(prefix="/store", tags=["store"])


class ProductCreate(BaseModel):
    name: str
    price: str
    description: str = ""
    image_url: str = ""
    category: str = ""
    in_stock: bool = True


class StoreLogin(BaseModel):
    phone: str
    password: str


def _get_store_password(phone: str) -> str:
    """Generate default password from phone number."""
    return phone[-4:] + "@store"


@router.get("/{website_id}", response_class=HTMLResponse)
def view_store(website_id: str):
    """Render the e-commerce store page for a business."""
    db = get_supabase()
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Store not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Store") if lead else "Store"
    phone = lead.get("phone", "") if lead else ""
    category = lead.get("category", "store") if lead else "store"
    whatsapp_num = "".join(ch for ch in phone if ch.isdigit()) if phone else ""
    slug = website.get("slug", "")

    content = website.get("content", {})
    colors = content.get("color_scheme", {})
    primary = colors.get("primary", "#7C3AED")

    # Get products
    try:
        products_r = db.table("store_products").select("*").eq("website_id", website_id).eq("in_stock", True).order("created_at", desc=True).execute()
        products = products_r.data or []
    except Exception:
        products = []

    # Build product cards
    product_cards = ""
    for p in products:
        img = p.get("image_url") or f"https://source.unsplash.com/300x300/?{p.get('name','product').replace(' ','+')}"
        wa_msg = f"Hi, I'm interested in {p.get('name','')} (Rs.{p.get('price','')}). Is it available?"
        import urllib.parse
        wa_url = f"https://wa.me/{whatsapp_num}?text={urllib.parse.quote(wa_msg)}"

        product_cards += f'''<div class="product-card">
<img src="{img}" alt="{p.get('name','')}" class="product-img">
<div class="product-body">
<h3>{p.get('name','')}</h3>
<p class="product-desc">{p.get('description','')}</p>
<div class="product-price">Rs. {p.get('price','')}</div>
<div class="product-actions">
<a href="{wa_url}" target="_blank" class="btn-buy">Buy Now</a>
<a href="{wa_url}" target="_blank" class="btn-enquire">Enquire</a>
</div>
</div>
</div>'''

    if not products:
        product_cards = '<div class="empty-store"><p>No products added yet.</p><p>Owner can add products from the Store Manager.</p></div>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{business_name} - Shop</title>
<meta name="theme-color" content="{primary}">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Plus Jakarta Sans',sans-serif;background:#f8fafc;color:#1e293b}}
.store-header{{background:linear-gradient(135deg,{primary},color-mix(in srgb,{primary} 70%,#000));color:#fff;padding:20px 24px;text-align:center}}
.store-header h1{{font-size:1.4rem;font-weight:800}}.store-header p{{font-size:.8rem;opacity:.8;margin-top:4px}}
.store-nav{{display:flex;gap:8px;padding:12px 16px;overflow-x:auto;background:#fff;border-bottom:1px solid #e2e8f0}}
.store-nav a{{flex-shrink:0;padding:6px 14px;border-radius:50px;font-size:.78rem;font-weight:600;text-decoration:none;background:#f1f5f9;color:#64748b}}.store-nav a.active{{background:{primary};color:#fff}}
.products{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;padding:16px;max-width:600px;margin:0 auto}}
.product-card{{background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0;transition:transform .2s}}.product-card:hover{{transform:translateY(-3px);box-shadow:0 8px 20px rgba(0,0,0,.08)}}
.product-img{{width:100%;aspect-ratio:1;object-fit:cover}}
.product-body{{padding:12px}}
.product-body h3{{font-size:.88rem;font-weight:700;margin-bottom:4px}}
.product-desc{{font-size:.72rem;color:#64748b;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.product-price{{font-size:1rem;font-weight:800;color:{primary};margin-bottom:10px}}
.product-actions{{display:flex;gap:6px}}
.btn-buy{{flex:1;text-align:center;padding:8px;background:{primary};color:#fff;border-radius:8px;font-size:.72rem;font-weight:700;text-decoration:none}}
.btn-enquire{{flex:1;text-align:center;padding:8px;background:#f1f5f9;color:#64748b;border-radius:8px;font-size:.72rem;font-weight:700;text-decoration:none;border:1px solid #e2e8f0}}
.empty-store{{text-align:center;padding:60px 20px;color:#94a3b8}}.empty-store p{{margin-bottom:8px}}
.store-footer{{text-align:center;padding:20px;font-size:.75rem;color:#94a3b8;border-top:1px solid #e2e8f0;margin-top:20px}}
.store-wa{{position:fixed;bottom:16px;right:16px;background:#25D366;color:#fff;width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(37,211,102,.4);text-decoration:none;font-size:1.5rem}}
@media(max-width:400px){{.products{{grid-template-columns:1fr;gap:10px}}}}
</style>
</head>
<body>
<div class="store-header">
<h1>{business_name}</h1>
<p>Shop & Order via WhatsApp</p>
</div>
<div class="products">{product_cards}</div>
<a href="https://wa.me/{whatsapp_num}" target="_blank" class="store-wa">\U0001f4ac</a>
<div class="store-footer">Powered by <a href="https://city-maps.online/{slug}" style="color:{primary}">City Maps</a></div>
</body>
</html>'''
    return HTMLResponse(content=html)


@router.post("/{website_id}/login")
def store_login(website_id: str, creds: StoreLogin):
    """Owner login to manage store products."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Store not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    phone = lead.get("phone", "") if lead else ""

    # Default password: last 4 digits of phone + @store
    expected_pass = _get_store_password(phone)

    if creds.phone == phone and creds.password == expected_pass:
        return {"authenticated": True, "website_id": website_id, "business": lead.get("business_name")}

    raise HTTPException(401, "Invalid credentials. Default password: last 4 digits of phone + @store")


@router.post("/{website_id}/products")
def add_product(website_id: str, product: ProductCreate):
    """Add a product to the store."""
    db = get_supabase()

    data = {
        "website_id": website_id,
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "image_url": product.image_url,
        "category": product.category,
        "in_stock": product.in_stock,
    }

    result = db.table("store_products").insert(data).execute()
    return {"added": True, "product": result.data[0] if result.data else data}


@router.get("/{website_id}/products")
def list_products(website_id: str):
    """List all products in a store."""
    db = get_supabase()
    result = db.table("store_products").select("*").eq("website_id", website_id).order("created_at", desc=True).execute()
    return result.data or []


@router.delete("/{website_id}/products/{product_id}")
def delete_product(website_id: str, product_id: str):
    """Delete a product."""
    db = get_supabase()
    db.table("store_products").delete().eq("id", product_id).eq("website_id", website_id).execute()
    return {"deleted": True}


@router.patch("/{website_id}/products/{product_id}")
def update_product(website_id: str, product_id: str, product: ProductCreate):
    """Update a product."""
    db = get_supabase()
    data = {
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "image_url": product.image_url,
        "category": product.category,
        "in_stock": product.in_stock,
    }
    db.table("store_products").update(data).eq("id", product_id).eq("website_id", website_id).execute()
    return {"updated": True}


STORE_MGR_TEMPLATE = r"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Store Manager - __BIZNAME__</title>
<meta name="theme-color" content="__PRIMARY__">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
:root{--p:__PRIMARY__;--ink:#0f172a;--mute:#64748b;--line:#e8edf3;--soft:#f6f8fb;--ok:#10b981;--bad:#ef4444}
body{font-family:'Plus Jakarta Sans',system-ui,sans-serif;background:#f0f3f8;color:var(--ink);padding-bottom:calc(90px + env(safe-area-inset-bottom));-webkit-overflow-scrolling:touch;overscroll-behavior-y:contain}
.appbar{position:sticky;top:0;z-index:50;background:linear-gradient(135deg,var(--p),color-mix(in srgb,var(--p) 70%,#000));color:#fff;padding:calc(14px + env(safe-area-inset-top)) 18px 14px;box-shadow:0 2px 12px rgba(0,0,0,.12)}
.appbar h1{font-size:1.05rem;font-weight:800;display:flex;align-items:center;gap:8px}
.appbar p{font-size:.72rem;opacity:.85;margin-top:2px}
.appbar-actions{display:flex;gap:8px;margin-top:12px}
.appbar-actions a{flex:1;text-align:center;padding:8px;background:rgba(255,255,255,.18);border-radius:10px;color:#fff;font-size:.72rem;font-weight:700;text-decoration:none;backdrop-filter:blur(6px)}
.appbar-actions a:active{transform:scale(.96)}
.wrap{max-width:640px;margin:0 auto;padding:16px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}
.stat{background:#fff;border-radius:14px;padding:14px 10px;text-align:center;border:1px solid var(--line)}
.stat .n{font-size:1.4rem;font-weight:800;color:var(--p)}
.stat .l{font-size:.62rem;color:var(--mute);margin-top:2px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.stat.g .n{color:var(--ok)}.stat.r .n{color:var(--bad)}
.creds{background:#fffbeb;border:1px solid #fde68a;padding:12px 14px;border-radius:12px;font-size:.74rem;margin-bottom:16px;color:#92400e}
.creds b{color:#78350f}
.search{position:relative;margin-bottom:14px}
.search input{width:100%;padding:12px 14px 12px 40px;border:1px solid var(--line);border-radius:12px;font-size:.88rem;background:#fff;outline:none}
.search svg{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--mute)}
.sec-title{font-size:.82rem;font-weight:800;color:var(--ink);margin-bottom:10px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.pcard{background:#fff;border-radius:16px;overflow:hidden;border:1px solid var(--line);position:relative}
.pcard img{width:100%;aspect-ratio:1;object-fit:cover;background:var(--soft)}
.pcard .body{padding:10px 12px 12px}
.pcard .nm{font-size:.82rem;font-weight:700;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pcard .pr{font-size:.95rem;font-weight:800;color:var(--p)}
.pcard .stk{position:absolute;top:8px;left:8px;font-size:.58rem;font-weight:700;padding:3px 8px;border-radius:50px;backdrop-filter:blur(4px)}
.stk.in{background:rgba(16,185,129,.92);color:#fff}.stk.out{background:rgba(239,68,68,.92);color:#fff}
.pacts{display:flex;gap:4px;margin-top:8px}
.pacts button{flex:1;padding:7px;border:none;border-radius:8px;font-size:.66rem;font-weight:700;cursor:pointer}
.b-edit{background:#eef2ff;color:#4f46e5}.b-del{background:#fef2f2;color:#ef4444}.b-tog{background:var(--soft);color:var(--mute)}
.fab{position:fixed;bottom:calc(20px + env(safe-area-inset-bottom));left:50%;transform:translateX(-50%);background:var(--p);color:#fff;border:none;padding:14px 28px;border-radius:50px;font-size:.9rem;font-weight:800;box-shadow:0 6px 20px color-mix(in srgb,var(--p) 45%,transparent);cursor:pointer;z-index:60;display:flex;align-items:center;gap:8px}
.fab:active{transform:translateX(-50%) scale(.95)}
.sheet{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;display:none;align-items:flex-end;justify-content:center}
.sheet.open{display:flex}
.sheet-box{background:#fff;width:100%;max-width:640px;border-radius:22px 22px 0 0;padding:20px 18px calc(20px + env(safe-area-inset-bottom));max-height:90vh;overflow-y:auto;animation:slideUp .25s ease}
@keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}
.sheet-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.sheet-h h2{font-size:1.05rem;font-weight:800}
.sheet-h button{background:var(--soft);border:none;width:32px;height:32px;border-radius:50%;font-size:1.1rem;cursor:pointer;color:var(--mute)}
label{display:block;font-size:.72rem;font-weight:700;color:var(--mute);margin-bottom:5px;margin-top:12px}
input,textarea,select{width:100%;padding:12px;border:1px solid var(--line);border-radius:12px;font-size:.9rem;background:var(--soft);outline:none;transition:border .2s}
input:focus,textarea:focus{border-color:var(--p);background:#fff}
.img-prev{width:100%;height:140px;object-fit:cover;border-radius:12px;margin-top:8px;display:none;background:var(--soft)}
.save-btn{width:100%;padding:14px;background:var(--p);color:#fff;border:none;border-radius:14px;font-size:.95rem;font-weight:800;cursor:pointer;margin-top:18px}
.save-btn:active{transform:scale(.98)}
.empty{text-align:center;padding:50px 20px;color:var(--mute)}.empty svg{opacity:.3;margin-bottom:12px}
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:var(--ink);color:#fff;padding:10px 18px;border-radius:50px;font-size:.78rem;font-weight:600;z-index:200;opacity:0;transition:opacity .3s;pointer-events:none}
.toast.show{opacity:1}
</style></head><body>
<div class="appbar">
<h1>Store Manager</h1>
<p>__BIZNAME__</p>
<div class="appbar-actions">
<a href="/api/store/__WID__/store-page" target="_blank">View Store</a>
<a href="javascript:void(0)" onclick="shareStore()">Share</a>
<a href="/api/panel/__WID__">Dashboard</a>
</div>
</div>
<div class="wrap">
<div class="stats">
<div class="stat"><div class="n" id="st-total">__TOTAL__</div><div class="l">Products</div></div>
<div class="stat g"><div class="n" id="st-in">__INSTOCK__</div><div class="l">In Stock</div></div>
<div class="stat r"><div class="n" id="st-out">__OUTSTOCK__</div><div class="l">Out</div></div>
</div>
<div class="creds"><b>Login:</b> __PHONE__ &nbsp;|&nbsp; <b>Password:</b> __PASSWORD__</div>
<div class="search">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
<input id="search" placeholder="Search products..." oninput="renderProducts()">
</div>
<div class="sec-title">Products</div>
<div class="grid" id="pgrid"></div>
</div>
<button class="fab" onclick="openSheet()">+ Add Product</button>
<div class="sheet" id="sheet"><div class="sheet-box">
<div class="sheet-h"><h2 id="sheet-title">Add Product</h2><button onclick="closeSheet()">&times;</button></div>
<form onsubmit="saveProduct(event)">
<input type="hidden" id="f-id">
<label>Product Name *</label><input id="f-name" placeholder="e.g. Margherita Pizza" required>
<label>Price (Rs.) *</label><input id="f-price" placeholder="e.g. 299" required>
<label>Description</label><textarea id="f-desc" rows="2" placeholder="Short description"></textarea>
<label>Category</label><input id="f-cat" placeholder="e.g. Pizza, Beverages">
<label>Image URL</label><input id="f-img" placeholder="https://..." oninput="previewImg()">
<img id="img-prev" class="img-prev">
<label>Availability</label><select id="f-stock"><option value="true">In Stock</option><option value="false">Out of Stock</option></select>
<button type="submit" class="save-btn" id="save-btn">Save Product</button>
</form></div></div>
<div class="toast" id="toast"></div>
<script>
var WID="__WID__";
var PRODUCTS=__PRODUCTS_JSON__;
function toast(m){var t=document.getElementById("toast");t.textContent=m;t.classList.add("show");setTimeout(function(){t.classList.remove("show")},2200);}
function updateStats(){var inS=PRODUCTS.filter(function(p){return p.in_stock}).length;document.getElementById("st-total").textContent=PRODUCTS.length;document.getElementById("st-in").textContent=inS;document.getElementById("st-out").textContent=PRODUCTS.length-inS;}
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;");}
function renderProducts(){
var q=(document.getElementById("search").value||"").toLowerCase();
var list=PRODUCTS.filter(function(p){return !q||(p.name||"").toLowerCase().indexOf(q)>=0||(p.category||"").toLowerCase().indexOf(q)>=0});
var grid=document.getElementById("pgrid");
if(!list.length){grid.innerHTML='<div class="empty" style="grid-column:1/-1"><p>No products yet. Tap Add Product below.</p></div>';return;}
grid.innerHTML=list.map(function(p){
var img=p.image_url||"https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&h=300&fit=crop";
var stk=p.in_stock?'<span class="stk in">In Stock</span>':'<span class="stk out">Out</span>';
return '<div class="pcard">'+stk+'<img src="'+esc(img)+'" alt="">'+
'<div class="body"><div class="nm">'+esc(p.name)+'</div><div class="pr">Rs. '+esc(p.price)+'</div>'+
'<div class="pacts"><button class="b-edit" onclick="editProduct(\''+p.id+'\')">Edit</button>'+
'<button class="b-tog" onclick="toggleStock(\''+p.id+'\')">'+(p.in_stock?"Hide":"Show")+'</button>'+
'<button class="b-del" onclick="delProduct(\''+p.id+'\')">Del</button></div></div></div>';
}).join("");
}
function openSheet(){document.getElementById("sheet-title").textContent="Add Product";["f-id","f-name","f-price","f-desc","f-cat","f-img"].forEach(function(i){document.getElementById(i).value="";});document.getElementById("f-stock").value="true";document.getElementById("img-prev").style.display="none";document.getElementById("sheet").classList.add("open");}
function closeSheet(){document.getElementById("sheet").classList.remove("open");}
function previewImg(){var u=document.getElementById("f-img").value;var p=document.getElementById("img-prev");if(u){p.src=u;p.style.display="block";}else{p.style.display="none";}}
function editProduct(id){var p=PRODUCTS.find(function(x){return x.id===id});if(!p)return;document.getElementById("sheet-title").textContent="Edit Product";document.getElementById("f-id").value=p.id;document.getElementById("f-name").value=p.name||"";document.getElementById("f-price").value=p.price||"";document.getElementById("f-desc").value=p.description||"";document.getElementById("f-cat").value=p.category||"";document.getElementById("f-img").value=p.image_url||"";document.getElementById("f-stock").value=p.in_stock?"true":"false";previewImg();document.getElementById("sheet").classList.add("open");}
async function saveProduct(e){e.preventDefault();
var id=document.getElementById("f-id").value;
var body={name:document.getElementById("f-name").value,price:document.getElementById("f-price").value,description:document.getElementById("f-desc").value,image_url:document.getElementById("f-img").value,category:document.getElementById("f-cat").value,in_stock:document.getElementById("f-stock").value==="true"};
var btn=document.getElementById("save-btn");btn.disabled=true;btn.textContent="Saving...";
try{
var url=id?("/api/store/"+WID+"/products/"+id):("/api/store/"+WID+"/products");
var r=await fetch(url,{method:id?"PATCH":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
if(r.ok){var d=await r.json();
if(id){var idx=PRODUCTS.findIndex(function(x){return x.id===id});if(idx>=0){body.id=id;PRODUCTS[idx]=body;}}
else{var np=d.product||body;PRODUCTS.unshift(np);}
closeSheet();renderProducts();updateStats();toast(id?"Updated":"Added");}
else{toast("Failed to save");}
}catch(err){toast("Error. Try again");}
btn.disabled=false;btn.textContent="Save Product";
}
async function delProduct(id){if(!confirm("Delete this product?"))return;
try{await fetch("/api/store/"+WID+"/products/"+id,{method:"DELETE"});PRODUCTS=PRODUCTS.filter(function(p){return p.id!==id});renderProducts();updateStats();toast("Deleted");}catch(e){toast("Failed");}}
async function toggleStock(id){var p=PRODUCTS.find(function(x){return x.id===id});if(!p)return;var body={name:p.name,price:p.price,description:p.description||"",image_url:p.image_url||"",category:p.category||"",in_stock:!p.in_stock};
try{var r=await fetch("/api/store/"+WID+"/products/"+id,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});if(r.ok){p.in_stock=!p.in_stock;renderProducts();updateStats();toast(p.in_stock?"Now visible":"Hidden");}}catch(e){toast("Failed");}}
function shareStore(){var url=location.origin+"/api/store/"+WID+"/store-page";window.open("https://wa.me/?text="+encodeURIComponent("Check out our online store: "+url),"_blank");}
document.getElementById("sheet").addEventListener("click",function(e){if(e.target===this)closeSheet();});
renderProducts();
</script>
</body></html>"""


@router.get("/{website_id}/manage", response_class=HTMLResponse)
def store_manager(website_id: str):
    """Owner management page for the store - app-style e-commerce admin."""
    service = WebsiteService()
    lead_service = LeadService()
    db = get_supabase()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Store not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Store") if lead else "Store"
    phone = lead.get("phone", "") if lead else ""
    password = _get_store_password(phone)
    content = website.get("content", {}) or {}
    colors = content.get("color_scheme", {}) or {}
    primary = colors.get("primary", "#7C3AED")
    try:
        products = db.table("store_products").select("*").eq("website_id", website_id).order("created_at", desc=True).execute()
        product_list = products.data or []
    except Exception:
        product_list = []
    total = len(product_list)
    in_stock = sum(1 for p in product_list if p.get("in_stock"))
    out_stock = total - in_stock
    import json as _json
    products_json = _json.dumps(product_list)
    html = (STORE_MGR_TEMPLATE
        .replace("__BIZNAME__", str(business_name))
        .replace("__WID__", str(website_id))
        .replace("__PRIMARY__", str(primary))
        .replace("__PHONE__", str(phone))
        .replace("__PASSWORD__", str(password))
        .replace("__TOTAL__", str(total))
        .replace("__INSTOCK__", str(in_stock))
        .replace("__OUTSTOCK__", str(out_stock))
        .replace("__PRODUCTS_JSON__", products_json))
    return HTMLResponse(content=html)

@router.get("/{website_id}/store-page", response_class=HTMLResponse)
def store_page(website_id: str):
    """Full e-commerce store page with cart, search, categories, WhatsApp checkout."""
    from app.services.website_service import WebsiteService
    from app.services.lead_service import LeadService
    from fastapi.responses import HTMLResponse
    
    ws = WebsiteService()
    ls = LeadService()
    website = ws.get(website_id)
    if not website:
        raise HTTPException(404, "Not found")
    lead = ls.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""
    address = lead.get("address", "") if lead else ""
    slug = website.get("slug", "")
    whatsapp_num = phone.replace("-", "").replace(" ", "").replace("+", "") if phone else ""
    if whatsapp_num and not whatsapp_num.startswith("91"):
        whatsapp_num = "91" + whatsapp_num

    # Get products
    db = get_supabase()
    products = []
    try:
        result = db.table("store_products").select("*").eq("website_id", website_id).eq("in_stock", True).order("name").execute()
        products = result.data or []
    except Exception:
        pass

    # Build product JSON for frontend
    import json
    products_json = json.dumps([{
        "id": p.get("id", ""),
        "name": p.get("name", ""),
        "description": p.get("description", ""),
        "price": p.get("price", 0),
        "image_url": p.get("image_url", ""),
        "category": p.get("category", "General"),
        "stock": p.get("stock_qty", 99),
    } for p in products])

    html = f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{business_name} - Store</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:sans-serif;background:#0f172a;color:#fff;padding:12px;padding-bottom:70px;max-width:600px;margin:0 auto}}
input,select{{font-size:16px!important}}
.hdr{{text-align:center;padding:10px 0}}.hdr h1{{font-size:1rem;font-weight:800}}.hdr p{{font-size:.7rem;color:#64748b}}
.search{{width:100%;padding:10px 14px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;color:#fff;font-size:14px;outline:none;margin-bottom:10px}}
.cats{{display:flex;gap:6px;overflow-x:auto;margin-bottom:12px;padding-bottom:4px}}.cat{{padding:5px 12px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:50px;font-size:.68rem;white-space:nowrap;cursor:pointer;color:#94a3b8}}.cat.active{{background:#6366f1;color:#fff;border-color:#6366f1}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}
.prod{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:12px;overflow:hidden;transition:all .2s}}.prod:active{{transform:scale(.97)}}
.prod img{{width:100%;height:70px;object-fit:cover;background:#1e293b}}
.prod-info{{padding:6px}}.prod-name{{font-size:.68rem;font-weight:600;margin-bottom:1px;line-height:1.2}}.prod-price{{font-size:.72rem;font-weight:800;color:#00e5ff}}.prod-desc{{font-size:.55rem;color:#64748b;margin-top:1px;line-height:1.2}}
.add-btn{{display:block;width:100%;padding:4px;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);border-radius:6px;color:#a78bfa;font-size:.62rem;font-weight:600;cursor:pointer;margin-top:4px;text-align:center}}
.cart-float{{position:fixed;bottom:16px;right:16px;width:50px;height:50px;background:#6366f1;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(99,102,241,.4);cursor:pointer;z-index:999}}.cart-float svg{{width:22px;height:22px;fill:#fff}}.cart-badge{{position:absolute;top:-4px;right:-4px;width:20px;height:20px;background:#ef4444;border-radius:50%;font-size:.6rem;font-weight:700;color:#fff;display:flex;align-items:center;justify-content:center}}
@keyframes cartBounce{{0%{{transform:scale(1)}}30%{{transform:scale(1.3)}}50%{{transform:scale(.9)}}70%{{transform:scale(1.1)}}100%{{transform:scale(1)}}}}
@keyframes addPulse{{0%{{box-shadow:0 0 0 0 rgba(99,102,241,.5)}}70%{{box-shadow:0 0 0 12px rgba(99,102,241,0)}}100%{{box-shadow:0 0 0 0 rgba(99,102,241,0)}}}}
.cart-float.bounce{{animation:cartBounce .5s ease}}
.cart-badge.pulse{{animation:addPulse .6s ease}}
.cart-panel{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;padding:16px;overflow-y:auto;backdrop-filter:blur(8px)}}
.cart-panel.open{{display:block}}
.cart-box{{background:#1e293b;border-radius:16px;padding:16px;max-width:400px;margin:20px auto}}
.cart-item{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:.75rem}}
.cart-total{{display:flex;justify-content:space-between;padding:12px 0;font-weight:800;font-size:.9rem;border-top:2px solid rgba(255,255,255,.1);margin-top:8px}}
.checkout-btn{{width:100%;padding:14px;background:#25D366;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.9rem;cursor:pointer;margin-top:10px}}
.addr-input{{width:100%;padding:10px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;color:#fff;font-size:14px;margin-top:8px;outline:none}}
.empty{{text-align:center;padding:40px;color:#475569;font-size:.8rem}}
.s-toast{{position:fixed;bottom:80px;left:50%;transform:translateX(-50%) translateY(20px);background:#10b981;color:#fff;padding:10px 20px;border-radius:50px;font-size:.78rem;font-weight:700;z-index:10000;opacity:0;transition:all .3s cubic-bezier(.4,0,.2,1);pointer-events:none;box-shadow:0 6px 20px rgba(16,185,129,.4);display:flex;align-items:center;gap:6px}}
.s-toast.show{{opacity:1;transform:translateX(-50%) translateY(0)}}
.add-btn.added{{background:rgba(16,185,129,.2)!important;border-color:rgba(16,185,129,.45)!important;color:#10b981!important}}
.cart-float{{transition:transform .2s}}.cart-badge{{transition:transform .2s}}
</style></head><body>

<div class="hdr">
<h1>&#128722; {business_name}</h1>
<p>Shop & Order via WhatsApp</p>
</div>

<input class="search" id="searchBox" placeholder="Search products..." oninput="filterProducts()">
<div class="cats" id="catBar"></div>
<div class="grid" id="prodGrid"></div>

<div class="s-toast" id="sToast">&#10003; Added to cart</div>
<div class="cart-float" id="cartFloat" onclick="toggleCart()">
<svg viewBox="0 0 24 24"><path d="M7 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>
<div class="cart-badge" id="cartCount">0</div>
</div>

<div class="cart-panel" id="cartPanel">
<div class="cart-box">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
<h2 style="font-size:1rem;font-weight:800">Your Cart</h2>
<button onclick="toggleCart()" style="background:none;border:none;color:#94a3b8;font-size:1.3rem;cursor:pointer">&times;</button>
</div>
<div id="cartItems"></div>
<div class="cart-total"><span>Total</span><span id="cartTotal">Rs.0</span></div>
<input class="addr-input" id="custAddr" placeholder="Delivery address (optional)">
<input class="addr-input" id="custName" placeholder="Your name" style="margin-top:6px">
<button class="checkout-btn" onclick="checkout()">&#128172; Order on WhatsApp</button>
</div>
</div>

<script>
var products={products_json};
var cart=JSON.parse(localStorage.getItem('cart_{website_id}')||'{{}}');
var activeCat='All';

function init(){{
  // Build categories
  var cats=['All',...new Set(products.map(p=>p.category||'General'))];
  var catHtml=cats.map(c=>'<div class="cat'+(c===activeCat?' active':'')+'" onclick="filterCat(this.textContent)">'+c+'</div>').join('');
  document.getElementById('catBar').innerHTML=catHtml;
  renderProducts(products);
  updateCartUI();
}}

function renderProducts(list){{
  if(!list.length){{document.getElementById('prodGrid').innerHTML='<div class="empty" style="grid-column:span 2">No products found</div>';return;}}
  var html=list.map(p=>{{
    var img=p.image_url||'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&h=200&fit=crop';
    return '<div class="prod"><img src="'+img+'" alt="'+p.name+'"><div class="prod-info"><div class="prod-name">'+p.name+'</div><div class="prod-price">Rs.'+p.price+'</div><div class="prod-desc">'+( p.description||'').substring(0,40)+'</div><button class="add-btn" onclick="addToCart(this.dataset.pid)" data-pid="'+p.id+'">+ Add to Cart</button></div></div>';
  }}).join('');
  document.getElementById('prodGrid').innerHTML=html;
}}

function filterProducts(){{
  var q=document.getElementById('searchBox').value.toLowerCase();
  var filtered=products.filter(p=>(p.name+' '+p.description+' '+p.category).toLowerCase().includes(q));
  if(activeCat!=='All')filtered=filtered.filter(p=>(p.category||'General')===activeCat);
  renderProducts(filtered);
}}

function filterCat(cat){{
  activeCat=cat;
  document.querySelectorAll('.cat').forEach(c=>c.classList.remove('active'));
  event.target.classList.add('active');
  filterProducts();
}}

function showToast(msg){{var t=document.getElementById("sToast");if(!t)return;t.innerHTML="&#10003; "+msg;t.classList.add("show");clearTimeout(window._tt);window._tt=setTimeout(function(){{t.classList.remove("show")}},1600);}}
function addToCart(id){{
  cart[id]=(cart[id]||0)+1;
  localStorage.setItem('cart_{website_id}',JSON.stringify(cart));
  updateCartUI();
  var cf=document.getElementById("cartFloat");
  if(cf){{cf.classList.remove("bounce");void cf.offsetWidth;cf.classList.add("bounce");}}
  var bd=document.getElementById("cartCount");
  if(bd){{bd.classList.remove("pulse");void bd.offsetWidth;bd.classList.add("pulse");}}
  var btn=document.querySelector('.add-btn[data-pid="'+id+'"]');
  if(btn){{var orig=btn.textContent;btn.classList.add("added");btn.textContent="\u2713 Added";setTimeout(function(){{btn.classList.remove("added");btn.textContent=orig;}},1000);}}
  showToast("Added to cart");
}}

function removeFromCart(id){{
  if(cart[id])cart[id]--;
  if(cart[id]<=0)delete cart[id];
  localStorage.setItem('cart_{website_id}',JSON.stringify(cart));
  updateCartUI();
  renderCartItems();
}}

function updateCartUI(){{
  var count=Object.values(cart).reduce((a,b)=>a+b,0);
  var bd=document.getElementById('cartCount');
  bd.textContent=count;
  bd.style.display=count>0?"flex":"none";
  var cf=document.getElementById("cartFloat");
  if(cf)cf.style.opacity=count>0?"1":".6";
}}

function toggleCart(){{
  var panel=document.getElementById('cartPanel');
  panel.classList.toggle('open');
  if(panel.classList.contains('open'))renderCartItems();
}}

function renderCartItems(){{
  var items='';var total=0;
  Object.keys(cart).forEach(id=>{{
    var p=products.find(x=>x.id===id);
    if(!p)return;
    var subtotal=p.price*cart[id];total+=subtotal;
    items+='<div class="cart-item"><div><b>'+p.name+'</b><br><span style="font-size:.6rem;color:#64748b">Rs.'+p.price+' x '+cart[id]+'</span></div><div style="display:flex;align-items:center;gap:8px"><span>Rs.'+subtotal+'</span><button onclick="removeFromCart(this.dataset.pid);renderCartItems()" data-pid="'+id+'" style="background:none;border:none;color:#ef4444;cursor:pointer;font-size:.8rem">-</button></div></div>';
  }});
  document.getElementById('cartItems').innerHTML=items||'<p style="text-align:center;color:#475569;padding:16px;font-size:.75rem">Cart is empty</p>';
  document.getElementById('cartTotal').textContent='Rs.'+total;
}}

function checkout(){{
  var items=[];var total=0;
  Object.keys(cart).forEach(id=>{{
    var p=products.find(x=>x.id===id);
    if(!p)return;
    items.push(p.name+' x'+cart[id]+' = Rs.'+(p.price*cart[id]));
    total+=p.price*cart[id];
  }});
  if(!items.length){{alert('Cart is empty');return;}}
  var name=document.getElementById('custName').value||'Customer';
  var addr=document.getElementById('custAddr').value;
  var msg='*New Order from {business_name} Store*%0A%0A';
  msg+='Customer: '+encodeURIComponent(name)+'%0A';
  if(addr)msg+='Address: '+encodeURIComponent(addr)+'%0A';
  msg+='%0A*Items:*%0A'+items.map(i=>encodeURIComponent('- '+i)).join('%0A');
  msg+='%0A%0A*Total: Rs.'+total+'*';
  msg+='%0A%0APlease confirm my order. Thank you!';
  // Save order history
  var history=JSON.parse(localStorage.getItem('orders_{website_id}')||'[]');
  history.unshift({{items:items,total:total,date:new Date().toISOString().slice(0,10)}});
  localStorage.setItem('orders_{website_id}',JSON.stringify(history.slice(0,20)));
  // Clear cart
  cart={{}};localStorage.setItem('cart_{website_id}','{{}}');updateCartUI();
  window.open('https://wa.me/{whatsapp_num}?text='+msg,'_blank');
  toggleCart();
}}

init();
</script>
</body></html>"""
    return HTMLResponse(content=html)
