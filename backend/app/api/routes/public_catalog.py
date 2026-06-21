from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.supabase import get_supabase

router = APIRouter(tags=["public-catalog"])


@router.get("/menu/{org_slug}", response_class=HTMLResponse)
async def public_catalog_page(org_slug: str):
    """Public catalog/menu page - shareable via WhatsApp. No auth required."""
    db = get_supabase()
    
    # Get org
    org = db.table("organizations").select("*").eq("slug", org_slug).single().execute()
    if not org.data:
        return HTMLResponse("<h1>Business not found</h1>", status_code=404)
    
    org_data = org.data
    org_id = org_data["id"]
    biz_name = org_data["name"]
    brand_color = org_data.get("brand_color", "#6366f1")
    phone = org_data.get("phone", "")
    
    # Get categories
    categories = db.table("catalog_categories").select("*").eq("organization_id", org_id).eq("is_active", True).order("sort_order").execute()
    
    # Get items
    items = db.table("catalog_items").select("*, catalog_categories(name)").eq("organization_id", org_id).eq("is_active", True).order("sort_order").execute()
    
    # Build categories nav
    cat_list = categories.data or []
    items_list = items.data or []
    
    # Group items by category
    import json
    items_json = json.dumps(items_list)
    cats_json = json.dumps(cat_list)
    
    # Clean phone for WhatsApp
    wa_phone = phone.replace("-", "").replace(" ", "").replace("+", "")
    if wa_phone and not wa_phone.startswith("91") and len(wa_phone) == 10:
        wa_phone = "91" + wa_phone

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{biz_name} - Menu & Catalog</title>
<meta name="description" content="Browse products and services from {biz_name}. Order via WhatsApp.">
<meta property="og:title" content="{biz_name} - Menu & Catalog">
<meta property="og:description" content="Browse our products and services. Order via WhatsApp.">
<meta property="og:type" content="website">
<style>
:root {{ --primary: {brand_color}; --primary-light: {brand_color}15; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; min-height: 100vh; padding-bottom: 70px; }}

/* Header */
.header {{ background: #fff; border-bottom: 1px solid #e2e8f0; padding: 14px 16px; position: sticky; top: 0; z-index: 50; }}
.header-inner {{ max-width: 600px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; }}
.header h1 {{ font-size: 1.1rem; font-weight: 800; color: #1e293b; }}
.header .badge {{ font-size: .6rem; background: var(--primary-light); color: var(--primary); padding: 2px 8px; border-radius: 10px; font-weight: 600; }}
.share-btn {{ background: none; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 10px; font-size: .7rem; cursor: pointer; color: #64748b; }}

/* Search */
.search-wrap {{ max-width: 600px; margin: 12px auto; padding: 0 16px; }}
.search {{ width: 100%; padding: 10px 14px 10px 36px; border: 1px solid #e2e8f0; border-radius: 10px; font-size: .85rem; outline: none; background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%2394a3b8' viewBox='0 0 24 24'%3E%3Cpath d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' stroke='%2394a3b8' stroke-width='2' fill='none'/%3E%3C/svg%3E") no-repeat 12px center; }}
.search:focus {{ border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-light); }}

/* Categories */
.cats {{ max-width: 600px; margin: 0 auto; padding: 8px 16px; display: flex; gap: 6px; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
.cats::-webkit-scrollbar {{ display: none; }}
.cat-btn {{ padding: 6px 14px; border-radius: 20px; font-size: .75rem; font-weight: 600; white-space: nowrap; border: 1px solid #e2e8f0; background: #fff; color: #64748b; cursor: pointer; transition: all .2s; }}
.cat-btn.active {{ background: var(--primary); color: #fff; border-color: var(--primary); }}

/* Items Grid */
.items {{ max-width: 600px; margin: 0 auto; padding: 12px 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.item {{ background: #fff; border: 1px solid #f1f5f9; border-radius: 12px; overflow: hidden; transition: transform .2s, box-shadow .2s; }}
.item:active {{ transform: scale(.98); }}
.item-img {{ width: 100%; aspect-ratio: 1; object-fit: cover; background: #f1f5f9; }}
.item-img-placeholder {{ width: 100%; aspect-ratio: 1; background: linear-gradient(135deg, #f1f5f9, #e2e8f0); display: flex; align-items: center; justify-content: center; font-size: 2rem; }}
.item-body {{ padding: 10px 12px; }}
.item-name {{ font-size: .8rem; font-weight: 600; color: #1e293b; line-height: 1.3; }}
.item-desc {{ font-size: .65rem; color: #94a3b8; margin-top: 2px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
.item-footer {{ display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }}
.item-price {{ font-size: .85rem; font-weight: 700; color: var(--primary); }}
.item-old-price {{ font-size: .65rem; color: #94a3b8; text-decoration: line-through; margin-left: 4px; }}
.item-btn {{ background: var(--primary); color: #fff; border: none; padding: 4px 10px; border-radius: 6px; font-size: .65rem; font-weight: 600; cursor: pointer; }}
.item-tag {{ position: absolute; top: 8px; left: 8px; background: #ef4444; color: #fff; font-size: .55rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }}
.item-wrap {{ position: relative; }}
.out-of-stock {{ opacity: .5; }}
.out-of-stock .item-btn {{ background: #94a3b8; }}

/* Empty */
.empty {{ text-align: center; padding: 40px 20px; color: #94a3b8; }}
.empty-icon {{ font-size: 3rem; margin-bottom: 8px; }}

/* Footer bar */
.footer-bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: #fff; border-top: 1px solid #e2e8f0; padding: 10px 16px; display: flex; gap: 8px; max-width: 600px; margin: 0 auto; z-index: 50; }}
.footer-bar a {{ flex: 1; text-align: center; padding: 10px; border-radius: 10px; font-size: .8rem; font-weight: 700; text-decoration: none; }}
.btn-wa {{ background: #25D366; color: #fff; }}
.btn-call {{ background: var(--primary); color: #fff; }}

/* Count badge */
.count {{ font-size: .6rem; color: #94a3b8; text-align: center; padding: 4px; }}

@media(min-width: 500px) {{ .items {{ grid-template-columns: 1fr 1fr 1fr; }} }}
</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <div>
      <h1>{biz_name}</h1>
    </div>
    <button class="share-btn" onclick="shareMenu()">&#128279; Share</button>
  </div>
</div>

<div class="search-wrap">
  <input type="text" class="search" id="searchInput" placeholder="Search products..." oninput="filterItems()">
</div>

<div class="cats" id="catsBar">
  <button class="cat-btn active" onclick="filterByCategory(null, this)">All</button>
</div>

<p class="count" id="itemCount"></p>

<div class="items" id="itemsGrid"></div>

<div class="empty" id="emptyState" style="display:none">
  <div class="empty-icon">&#128722;</div>
  <p>No products found</p>
</div>

<div class="footer-bar">
  <a href="https://wa.me/{wa_phone}?text=Hi%2C%20I%27d%20like%20to%20order%20from%20your%20catalog" class="btn-wa" target="_blank">&#128172; WhatsApp Order</a>
  <a href="tel:{phone}" class="btn-call">&#128222; Call</a>
</div>

<script>
var allItems = {items_json};
var allCats = {cats_json};
var activeCategory = null;
var searchText = "";

// Render categories
var catsBar = document.getElementById("catsBar");
allCats.forEach(function(cat) {{
  var btn = document.createElement("button");
  btn.className = "cat-btn";
  btn.textContent = cat.name;
  btn.onclick = function() {{ filterByCategory(cat.id, btn); }};
  catsBar.appendChild(btn);
}});

// Initial render
renderItems(allItems);

function filterByCategory(catId, btn) {{
  activeCategory = catId;
  document.querySelectorAll(".cat-btn").forEach(function(b) {{ b.classList.remove("active"); }});
  btn.classList.add("active");
  filterItems();
}}

function filterItems() {{
  searchText = document.getElementById("searchInput").value.toLowerCase();
  var filtered = allItems.filter(function(item) {{
    var matchCat = !activeCategory || item.category_id === activeCategory;
    var matchSearch = !searchText || item.name.toLowerCase().includes(searchText) || (item.description || "").toLowerCase().includes(searchText);
    return matchCat && matchSearch;
  }});
  renderItems(filtered);
}}

function renderItems(items) {{
  var grid = document.getElementById("itemsGrid");
  var empty = document.getElementById("emptyState");
  var countEl = document.getElementById("itemCount");
  
  if (items.length === 0) {{
    grid.innerHTML = "";
    empty.style.display = "block";
    countEl.textContent = "";
    return;
  }}
  
  empty.style.display = "none";
  countEl.textContent = items.length + " items";
  
  grid.innerHTML = items.map(function(item) {{
    var img = item.images && item.images.length > 0 
      ? '<img class="item-img" src="' + item.images[0] + '" loading="lazy" alt="' + item.name + '">'
      : '<div class="item-img-placeholder">&#128722;</div>';
    
    var tags = item.tags || [];
    var tagHtml = "";
    if (tags.includes("bestseller")) tagHtml = '<span class="item-tag" style="background:#f59e0b">Bestseller</span>';
    else if (tags.includes("new")) tagHtml = '<span class="item-tag" style="background:#10b981">New</span>';
    else if (tags.includes("featured")) tagHtml = '<span class="item-tag">Featured</span>';
    
    var priceHtml = item.price ? '<span class="item-price">&#8377;' + Number(item.price).toLocaleString("en-IN") + '</span>' : '';
    if (item.compare_price && item.compare_price > item.price) {{
      priceHtml += '<span class="item-old-price">&#8377;' + Number(item.compare_price).toLocaleString("en-IN") + '</span>';
    }}
    
    var stockClass = item.in_stock ? "" : " out-of-stock";
    var btnText = item.in_stock ? "Enquire" : "Out of Stock";
    
    var catName = item.catalog_categories ? item.catalog_categories.name : "";
    
    return '<div class="item' + stockClass + '"><div class="item-wrap">' + tagHtml + img + '</div><div class="item-body"><div class="item-name">' + item.name + '</div>' + (item.description ? '<div class="item-desc">' + item.description + '</div>' : '') + '<div class="item-footer">' + priceHtml + '<button class="item-btn" onclick="enquireItem(\'' + item.name + '\')">' + btnText + '</button></div></div></div>';
  }}).join("");
}}

function enquireItem(name) {{
  var msg = "Hi, I'm interested in: " + name + ". Please share details.";
  window.open("https://wa.me/{wa_phone}?text=" + encodeURIComponent(msg), "_blank");
}}

function shareMenu() {{
  var url = window.location.href;
  if (navigator.share) {{
    navigator.share({{ title: "{biz_name} - Catalog", url: url }});
  }} else {{
    navigator.clipboard.writeText(url);
    alert("Link copied! Share via WhatsApp or anywhere.");
  }}
}}
</script>
</body>
</html>'''
    return HTMLResponse(content=html)
