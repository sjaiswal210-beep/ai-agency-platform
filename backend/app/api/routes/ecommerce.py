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


@router.get("/{website_id}/manage", response_class=HTMLResponse)
def store_manager(website_id: str):
    """Owner management page for the store."""
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

    try:
        products = db.table("store_products").select("*").eq("website_id", website_id).order("created_at", desc=True).execute()
        product_list = products.data or []
    except Exception:
        product_list = []

    rows = ""
    for p in product_list:
        stock = "In Stock" if p.get("in_stock") else "Out of Stock"
        rows += f'<tr><td>{p.get("name","")}</td><td>Rs.{p.get("price","")}</td><td>{stock}</td><td><button onclick="deleteProduct(\'{p["id"]}\')">Delete</button></td></tr>'

    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Store Manager - {business_name}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:system-ui,sans-serif;background:#f8fafc;padding:20px}}
h1{{font-size:1.3rem;margin-bottom:4px}}p.sub{{font-size:.8rem;color:#64748b;margin-bottom:20px}}
.card{{background:#fff;border-radius:12px;padding:20px;border:1px solid #e2e8f0;margin-bottom:16px}}
.card h2{{font-size:1rem;margin-bottom:12px}}
input,textarea{{width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:8px;font-size:.9rem}}
button{{padding:10px 16px;background:#7c3aed;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #e2e8f0}}
.creds{{background:#fef3c7;padding:12px;border-radius:8px;font-size:.8rem;margin-bottom:16px}}
</style></head><body>
<h1>Store Manager</h1>
<p class="sub">{business_name}</p>
<div class="creds"><strong>Login Credentials:</strong><br>Phone: {phone}<br>Password: {password}</div>
<div class="card"><h2>Add Product</h2>
<form onsubmit="addProduct(event)">
<input name="name" placeholder="Product Name" required>
<input name="price" placeholder="Price (e.g., 599)" required>
<textarea name="description" placeholder="Short description" rows="2"></textarea>
<input name="image_url" placeholder="Image URL (optional)">
<input name="category" placeholder="Category (optional)">
<button type="submit">Add Product</button>
</form></div>
<div class="card"><h2>Products ({len(product_list)})</h2>
<table><thead><tr><th>Name</th><th>Price</th><th>Stock</th><th>Action</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<script>
const WID="{website_id}";
async function addProduct(e){{e.preventDefault();const f=new FormData(e.target);
const body={{name:f.get("name"),price:f.get("price"),description:f.get("description"),image_url:f.get("image_url"),category:f.get("category"),in_stock:true}};
const r=await fetch(`/api/store/${{WID}}/products`,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(body)}});
if(r.ok){{alert("Product added!");location.reload();}}else{{alert("Failed to add");}}}}
async function deleteProduct(id){{if(!confirm("Delete?"))return;
await fetch(`/api/store/${{WID}}/products/${{id}}`,{{method:"DELETE"}});location.reload();}}
</script>
</body></html>'''
    return HTMLResponse(content=html)
