from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
import json
import urllib.parse
import asyncio

import re

def _get_real_photos(business_name: str, address: str) -> list:
    """Fetch real Google Maps photos using sync HTTP."""
    try:
        import httpx
        from app.core.config import get_settings
        settings = get_settings()
        api_key = settings.google_places_key
        if not api_key:
            return []
        
        query = f"{business_name} {address}".strip()
        
        with httpx.Client(timeout=8) as client:
            # Search for business
            resp = client.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": query, "key": api_key}
            )
            if resp.status_code != 200:
                return []
            results = resp.json().get("results", [])
            if not results:
                return []
            
            place_id = results[0]["place_id"]
            
            # Get photo references
            detail = client.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={"place_id": place_id, "fields": "photos", "key": api_key}
            )
            if detail.status_code != 200:
                return []
            
            photos = detail.json().get("result", {}).get("photos", [])
            photo_urls = []
            for p in photos[:6]:
                ref = p.get("photo_reference")
                if ref:
                    photo_urls.append(f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=600&photo_reference={ref}&key={api_key}")
            return photo_urls
    except Exception:
        return []

router = APIRouter(prefix="/preview", tags=["preview"])

# Direct Unsplash image URLs (these are permanent, never break)
IMAGES = {
    "restaurant": {
        "hero": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=500&h=500&fit=crop",
        ],
    },
    "cafe": {
        "hero": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1442512595331-e89e73853f31?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1498804103079-a6351b050096?w=500&h=500&fit=crop",
        ],
    },
    "salon": {
        "hero": "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1562322140-8baeececf3df?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1633681926022-84c23e8cb2d6?w=500&h=500&fit=crop",
        ],
    },
    "gym": {
        "hero": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1576678927484-cc907957088c?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1549060279-7e168fcee0c2?w=500&h=500&fit=crop",
        ],
    },
    "clinic": {
        "hero": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1551076805-e1869033e561?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1581056771107-24ca5f033842?w=500&h=500&fit=crop",
        ],
    },
    "dentist": {
        "hero": "https://images.unsplash.com/photo-1629909613654-28e377c37b09?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1606811841689-23dfddce3e95?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1606265752439-1f18756aa5fc?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1598256989800-fe5f95da9787?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1609840114035-3c981b782dfe?w=500&h=500&fit=crop",
        ],
    },
    "doctor": {
        "hero": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1551076805-e1869033e561?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1581056771107-24ca5f033842?w=500&h=500&fit=crop",
        ],
    },
    "store": {
        "hero": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1567401893414-76b7b1e5a7a5?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=500&h=500&fit=crop",
        ],
    },
    "plumber": {
        "hero": "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=500&h=500&fit=crop",
        ],
    },
    "realestate": {
        "hero": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1582407947304-fd86f028f716?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=500&h=500&fit=crop",
        ],
    },
    "doctor": {
        "hero": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1551076805-e1869033e561?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1581056771107-24ca5f033842?w=500&h=500&fit=crop",
        ],
    },
    "yoga": {
        "hero": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1575052814086-f385e2e2ad1b?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1552196563-55cd4e45efb3?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=500&h=500&fit=crop",
        ],
    },
    "spa": {
        "hero": "https://images.unsplash.com/photo-1540555700478-4be289fbec6d?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1600334129128-685c5582fd35?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1515377905703-c4788e51af15?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1507652313519-d4e9174996dd?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1596178060671-7a80dc8059ea?w=500&h=500&fit=crop",
        ],
    },
    "hotel": {
        "hero": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=500&h=500&fit=crop",
        ],
    },
    "lawyer": {
        "hero": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1521791055366-0d553872125f?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1436450412740-6b988f486c6b?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=500&h=500&fit=crop",
        ],
    },
    "photographer": {
        "hero": "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1554048612-b6a482bc67e5?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1471341971476-ae15ff5dd4ea?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1493863641943-9b68992a8d07?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&h=500&fit=crop",
        ],
    },
    "solar": {
        "hero": "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1559302504-64aae6ca6b6d?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1611365892117-00ac6fb5136d?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1595437193398-f24279553f4f?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1613665813446-82a78c468a1d?w=500&h=500&fit=crop",
        ],
    },
    "school": {
        "hero": "https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1577896851231-70ef18881754?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=500&h=500&fit=crop",
        ],
    },
    "default": {
        "hero": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1400&h=800&fit=crop",
        "about": "https://images.unsplash.com/photo-1497215842964-222b430dc094?w=800&h=600&fit=crop",
        "gallery": [
            "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=500&h=500&fit=crop",
        ],
    },
}


def get_images_for_category(category: str) -> dict:
    """Get images for a category. Falls back to default if not found."""
    cat = category.lower().strip()
    # Direct match
    if cat in IMAGES:
        return IMAGES[cat]
    # Partial match
    for key in IMAGES:
        if key in cat or cat in key:
            return IMAGES[key]
    # Keywords mapping
    keyword_map = {
        "food": "restaurant", "pizza": "restaurant", "biryani": "restaurant", "dhaba": "restaurant",
        "hair": "salon", "beauty": "salon", "parlour": "salon", "parlor": "salon",
        "fitness": "gym", "workout": "gym", "crossfit": "gym",
        "hospital": "clinic", "medical": "clinic", "health": "clinic", "nursing": "clinic",
        "dental": "dentist", "teeth": "dentist", "orthodontist": "dentist", "oral": "dentist",
        "shop": "store", "retail": "store", "market": "store", "mall": "store",
        "house": "realestate", "property": "realestate", "flat": "realestate", "apartment": "realestate",
        "pipe": "plumber", "water": "plumber", "sanitary": "plumber",
        "coffee": "cafe", "tea": "cafe", "bakery": "cafe", "juice": "cafe",
        "meditation": "yoga", "pilates": "yoga", "wellness": "spa",
        "massage": "spa", "ayurved": "spa", "therapy": "spa",
        "lodge": "hotel", "resort": "hotel", "hostel": "hotel", "stay": "hotel",
        "advocate": "lawyer", "legal": "lawyer", "attorney": "lawyer",
        "photo": "photographer", "video": "photographer", "studio": "photographer", "wedding": "photographer",
        "energy": "solar", "panel": "solar", "electric": "solar", "power": "solar",
        "tuition": "school", "coaching": "school", "academy": "school", "institute": "school",
        "doctor": "clinic", "physician": "clinic", "surgeon": "clinic",
        "food": "restaurant", "pizza": "restaurant", "biryani": "restaurant",
        "hair": "salon", "beauty": "salon", "spa": "salon",
        "fitness": "gym", "yoga": "gym", "workout": "gym",
        "hospital": "clinic", "medical": "clinic", "health": "clinic",
        "dental": "dentist", "teeth": "dentist", "orthodontist": "dentist",
        "shop": "store", "retail": "store", "market": "store",
        "house": "realestate", "property": "realestate", "flat": "realestate",
        "pipe": "plumber", "water": "plumber",
        "coffee": "cafe", "tea": "cafe", "bakery": "cafe",
    }
    for keyword, mapped_cat in keyword_map.items():
        if keyword in cat:
            return IMAGES[mapped_cat]
    return IMAGES["default"]


CATEGORY_LOGO_ICONS = {
    "salon": '<path d="M20 8c-2 0-3 1-3 3v2c0 1 .5 2 1.5 2.5L17 20h6l-1.5-4.5c1-.5 1.5-1.5 1.5-2.5v-2c0-2-1-3-3-3z" fill="white"/><path d="M14 12c0-1 .5-2 1-2.5" stroke="white" stroke-width="1.5" fill="none"/><path d="M26 12c0-1-.5-2-1-2.5" stroke="white" stroke-width="1.5" fill="none"/>',
    "restaurant": '<path d="M12 10v10M16 10v4c0 2-1 3-2 3v3M24 10c0 3-1 5-2 6v4M28 10v10" stroke="white" stroke-width="2" stroke-linecap="round" fill="none"/>',
    "cafe": '<path d="M12 14h12v8c0 2-2 4-4 4h-4c-2 0-4-2-4-4v-8z" stroke="white" stroke-width="1.5" fill="none"/><path d="M24 16h2c1 0 2 1 2 2s-1 2-2 2h-2" stroke="white" stroke-width="1.5" fill="none"/><path d="M15 11c0-1 1-2 2-2s2 1 2 2" stroke="white" stroke-width="1.5" fill="none"/>',
    "gym": '<rect x="10" y="16" width="4" height="8" rx="1" stroke="white" stroke-width="1.5" fill="none"/><rect x="26" y="16" width="4" height="8" rx="1" stroke="white" stroke-width="1.5" fill="none"/><rect x="14" y="18" width="12" height="4" rx="1" stroke="white" stroke-width="1.5" fill="none"/>',
    "dentist": '<circle cx="20" cy="18" r="6" stroke="white" stroke-width="1.5" fill="none"/><path d="M17 18c0-1.5 1.5-3 3-3s3 1.5 3 3" stroke="white" stroke-width="1.5" fill="none"/><path d="M18 21l1 4M22 21l-1 4" stroke="white" stroke-width="1.5" fill="none"/>',
    "clinic": '<path d="M17 14h6M20 11v6" stroke="white" stroke-width="2" stroke-linecap="round"/><rect x="12" y="18" width="16" height="10" rx="2" stroke="white" stroke-width="1.5" fill="none"/>',
    "hotel": '<rect x="12" y="14" width="16" height="14" rx="2" stroke="white" stroke-width="1.5" fill="none"/><path d="M12 18h16M18 14v-2h4v2" stroke="white" stroke-width="1.5" fill="none"/><rect x="17" y="22" width="6" height="6" rx="1" stroke="white" stroke-width="1.5" fill="none"/>',
    "store": '<path d="M12 16l2-4h12l2 4M12 16v10h16v-10M12 16h16" stroke="white" stroke-width="1.5" fill="none"/><rect x="17" y="20" width="6" height="6" stroke="white" stroke-width="1.5" fill="none"/>',
    "lawyer": '<rect x="14" y="12" width="12" height="16" rx="1" stroke="white" stroke-width="1.5" fill="none"/><path d="M17 16h6M17 19h6M17 22h4" stroke="white" stroke-width="1.5" stroke-linecap="round" fill="none"/>',
    "photographer": '<rect x="12" y="14" width="16" height="12" rx="2" stroke="white" stroke-width="1.5" fill="none"/><circle cx="20" cy="20" r="3" stroke="white" stroke-width="1.5" fill="none"/><rect x="17" y="12" width="6" height="3" rx="1" stroke="white" stroke-width="1.5" fill="none"/>',
    "solar": '<circle cx="20" cy="18" r="4" stroke="white" stroke-width="1.5" fill="none"/><path d="M20 12v-2M20 24v2M14 18h-2M26 18h2M15.5 13.5l-1.5-1.5M24.5 13.5l1.5-1.5M15.5 22.5l-1.5 1.5M24.5 22.5l1.5 1.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>',
    "school": '<path d="M20 12l8 4-8 4-8-4z" stroke="white" stroke-width="1.5" fill="none"/><path d="M14 17v6c0 2 3 3 6 3s6-1 6-3v-6" stroke="white" stroke-width="1.5" fill="none"/><path d="M28 16v6" stroke="white" stroke-width="1.5"/>',
    "bakery": '<path d="M14 22c0-3 2-5 3-6 1 1 2 1 3 1s2 0 3-1c1 1 3 3 3 6" stroke="white" stroke-width="1.5" fill="none"/><path d="M13 22h14v4c0 1-1 2-2 2h-10c-1 0-2-1-2-2v-4z" stroke="white" stroke-width="1.5" fill="none"/>',
}


def _get_logo_icon(category: str) -> str:
    """Generate a category-specific SVG logo icon."""
    cat = category.lower().strip()
    icon_path = CATEGORY_LOGO_ICONS.get(cat, "")
    
    # Try partial match
    if not icon_path:
        for key, path in CATEGORY_LOGO_ICONS.items():
            if key in cat or cat in key:
                icon_path = path
                break
    
    # Keyword fallback
    if not icon_path:
        keyword_map = {
            "food": "restaurant", "pizza": "restaurant", "hair": "salon",
            "beauty": "salon", "spa": "salon", "fitness": "gym",
            "doctor": "clinic", "hospital": "clinic", "medical": "clinic",
            "dental": "dentist", "teeth": "dentist", "shop": "store",
            "retail": "store", "coffee": "cafe", "tea": "cafe",
            "lodge": "hotel", "resort": "hotel", "photo": "photographer",
            "energy": "solar", "panel": "solar", "academy": "school",
            "cake": "bakery", "bread": "bakery", "sweet": "bakery",
        }
        for kw, mapped in keyword_map.items():
            if kw in cat:
                icon_path = CATEGORY_LOGO_ICONS.get(mapped, "")
                break
    
    # Default icon (star/sparkle)
    if not icon_path:
        icon_path = '<path d="M20 12l2 5h5l-4 3 1.5 5-4.5-3-4.5 3 1.5-5-4-3h5z" stroke="white" stroke-width="1.5" fill="none"/>'
    
    return icon_path


def get_maps_embed(address: str, business_name: str = "") -> str:
    if not address:
        return ""
    query = f"{business_name} {address}".strip() if business_name else address
    encoded = urllib.parse.quote(query)
    return f"https://www.google.com/maps?q={encoded}&output=embed"



def _get_design_css(category: str) -> str:
    """Get category-specific CSS for unique visual personality per business type."""
    cat = category.lower().strip()
    
    # Gym / Fitness - bold, dark, energetic, angular
    if any(k in cat for k in ["gym", "fitness", "crossfit", "workout", "sports"]):
        return """body{background:#0a0a0a;color:#fff}.sec,.section{color:#fff}.sec-head h2,.section-header h2{color:#fff}.svc-body h3,.feat-card h3,.about-text h2,.feature-item h3{color:#fff}.svc-body p,.feat-card p,.about-text p,.feature-item p{color:#a0a0a0}.sec-alt,.sec-tint,.section-alt{background:#111!important}.feature-item,.service-card,.testimonial-card,.faq-item,.benefit-item{background:#1a1a1a!important;border-color:#2a2a2a!important;color:#fff}.testimonial-card blockquote,.faq-item summary{color:#fff}.testimonial-card cite,.faq-item p{color:#a0a0a0}.contact-section{background:#000!important}.footer{background:#000!important}.service-card{border-radius:8px!important}.feature-item{border-radius:8px!important}.hero h1{text-transform:uppercase;letter-spacing:.05em}"""
    
    # Salon / Spa / Beauty - soft, elegant, rounded, pastel
    if any(k in cat for k in ["salon", "beauty", "spa", "yoga", "wellness", "parlour"]):
        return """body{background:#fafaff}.section,.sec{background:#fafaff}.sec-alt,.sec-tint,.section-alt{background:rgba(255,255,255,.7)!important}.service-card,.feature-item,.testimonial-card,.faq-item{backdrop-filter:blur(8px);background:rgba(255,255,255,.8)!important;border:1px solid rgba(200,180,255,.2)!important;box-shadow:0 8px 32px rgba(124,58,237,.04)!important;border-radius:24px!important}.hero h1{font-family:'Playfair Display',serif!important;font-style:italic}.service-img{border-radius:20px!important}.stats-section{border-radius:30px;margin:0 16px}"""
    
    # Restaurant / Cafe / Food - warm, inviting, curved
    if any(k in cat for k in ["restaurant", "food", "cafe", "bakery", "pizza", "dhaba"]):
        return """body{background:#fffbf5}.sec-alt,.sec-tint,.section-alt{background:#fff8f0!important}.section-header h2,.sec-head h2,.about-text h2,.hero h1{font-family:'Playfair Display',serif!important}.service-card{border-radius:24px!important;overflow:hidden}.service-img{height:220px!important}.feature-item{background:#fff8f0!important;border-color:#f0e6d8!important}.stats-section::before{background:rgba(15,23,42,.8)!important}"""
    
    # Medical / Dental / Clinic - clean, minimal, trust
    if any(k in cat for k in ["clinic", "dentist", "doctor", "hospital", "medical", "health"]):
        return """body{background:#fff}.sec-alt,.sec-tint,.section-alt{background:#f0f9ff!important}.service-card{border-left:4px solid var(--p)!important;border-radius:4px 16px 16px 4px!important}.feature-item{border-radius:12px!important;border-left:3px solid var(--p)!important}.hero::after{display:none}"""
    
    # Hotel / Resort - luxury, serif headings, wide
    if any(k in cat for k in ["hotel", "resort", "lodge"]):
        return """.hero h1,.section-header h2,.sec-head h2,.about-text h2{font-family:'Playfair Display',serif!important;letter-spacing:-.03em}.service-card{border-radius:4px!important}.service-img{height:240px!important}.feature-item{border-radius:4px!important;border-bottom:2px solid var(--p)!important;border-left:none!important}"""
    
    # Store / Retail / Shopping - product-focused, grid, modern
    if any(k in cat for k in ["store", "shop", "retail", "cloth", "fashion", "boot", "shoe"]):
        return """.service-card{border-radius:16px!important}.service-img{height:200px!important;border-radius:12px 12px 0 0!important}.service-content{padding:16px!important}.feature-item{border-radius:50px!important;padding:16px 24px!important;flex-direction:row!important;text-align:left!important;gap:16px!important}.feature-icon{margin-bottom:0!important}.gallery-item{border-radius:12px!important;aspect-ratio:3/4!important}"""
    
    # School / Education - colorful, friendly, rounded
    if any(k in cat for k in ["school", "coaching", "academy", "institute", "tuition"]):
        return """.service-card,.feature-item,.testimonial-card{border-radius:24px!important}.feature-icon{border-radius:50%!important;width:60px!important;height:60px!important}.hero::after{background:linear-gradient(90deg,#7c3aed,#ec4899,#f59e0b)!important}"""
    
    # Photographer / Creative - minimal, image-focused
    if any(k in cat for k in ["photo", "photographer", "studio", "video", "creative"]):
        return """.service-card{border:none!important;box-shadow:none!important}.service-img{height:280px!important;border-radius:4px!important}.service-content{padding:16px 0!important}.gallery-item{border-radius:2px!important;aspect-ratio:auto!important}.hero h1{font-size:clamp(3rem,7vw,5rem)!important;font-weight:300!important;letter-spacing:-.04em}.feature-item{border:none!important;background:transparent!important}"""
    
    # Solar / Energy - eco, green accents
    if any(k in cat for k in ["solar", "energy", "electric", "power"]):
        return """.feature-item{border-radius:16px!important;border:2px solid #d1fae5!important;background:#f0fdf4!important}.hero::after{background:linear-gradient(90deg,#059669,#10b981,#34d399)!important}"""
    
    # Lawyer / Professional - authoritative, sharp
    if any(k in cat for k in ["lawyer", "advocate", "legal", "consultant", "accountant"]):
        return """.hero h1,.section-header h2{font-family:'Playfair Display',serif!important}.service-card{border-radius:4px!important;border-top:3px solid var(--p)!important}.feature-item{border-radius:4px!important}"""
    
    # Default professional
    return ""



MOBILE_CSS = """
<style>
.lightbox{display:none;position:fixed;inset:0;background:rgba(0,0,0,.9);z-index:9999;align-items:center;justify-content:center;padding:20px}.lightbox.open{display:flex}.lightbox img{max-width:90%;max-height:80vh;border-radius:12px;object-fit:contain}.lightbox .close{position:absolute;top:16px;right:20px;color:#fff;font-size:2rem;cursor:pointer;background:none;border:none}
@media(max-width:768px){
  .nav-links{display:none}
  .nav{padding:12px 16px}
  .nav-cta{display:flex!important;background:transparent!important;box-shadow:none!important;color:#fff!important;font-size:1rem!important;padding:6px 10px!important;border:1.5px solid rgba(255,255,255,.5)!important;border-radius:8px!important;width:auto!important;height:auto!important;align-items:center!important;justify-content:center!important}
  .hero{min-height:auto;padding-top:80px!important;padding-bottom:40px!important}
  .hero-content{padding:60px 16px 24px!important;margin:0!important}
  .hero h1{font-size:1.4rem!important;margin-bottom:8px!important}
  .hero p{font-size:.82rem!important;margin-bottom:10px!important}
  .hero-btns{flex-direction:column!important;gap:10px!important;align-items:stretch!important}
  .hero-btns .btn,.btn-white,.btn-glass{text-align:center;justify-content:center;padding:12px 20px!important;font-size:.9rem!important}
  .stats-section .stats-grid,.stats-grid{grid-template-columns:repeat(2,1fr)!important;gap:12px!important;padding:0 16px}
  .stat-number{font-size:1.5rem!important}
  .section,.sec{padding:36px 16px!important}
  .section-header h2,.sec-head h2{font-size:1.3rem!important}
  .about-grid{grid-template-columns:1fr!important;gap:24px!important}
  .about-img img{height:280px!important;border-radius:14px!important}
  .about-badge{bottom:-14px!important;left:10px!important;padding:12px 16px!important}
  .services-grid{grid-template-columns:1fr!important;gap:10px!important}
  .service-card{display:flex!important;flex-direction:row!important;border-radius:12px!important}
  .service-img{width:90px!important;min-width:90px!important;height:90px!important;min-height:90px!important;border-radius:12px 0 0 12px!important}
  .service-content{padding:12px 14px!important}
  .service-content h3{font-size:.92rem!important;margin-bottom:4px!important}
  .service-content p{font-size:.8rem!important;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .features-grid{grid-template-columns:repeat(2,1fr)!important;gap:10px!important}
  .feature-item{padding:16px 12px!important;border-radius:12px!important}
  .feature-icon{width:40px!important;height:40px!important;font-size:1.2rem!important;margin-bottom:8px!important}
  .feature-item h3{font-size:.82rem!important}
  .feature-item p{font-size:.72rem!important}
  .gallery-grid{grid-template-columns:repeat(2,1fr)!important;gap:8px!important}
  .gallery-item{border-radius:10px!important}
  .testimonials-grid{grid-template-columns:1fr!important;gap:12px!important}
  .testimonial-card{padding:20px!important}
  .contact-container{grid-template-columns:1fr!important;gap:20px!important}
  .contact-section{padding:36px 16px!important}
  .footer{padding:30px 16px 80px!important}
  .bottom-nav{display:block!important}
  .bottom-nav a{padding:8px 14px!important;font-size:.7rem!important}
  .bn-icon{font-size:1.5rem!important}
  .bn-icon svg{width:24px!important;height:24px!important}
  .whatsapp-float{display:none!important}
  .chat-btn{bottom:80px!important}
  body{padding-bottom:60px}
  .faq-item summary{font-size:.9rem!important;padding:14px 16px!important}
  .faq-item p{padding:0 16px 14px!important;font-size:.85rem!important}
  .benefits-grid{grid-template-columns:1fr!important}.benefits-section{display:none!important}
}
.social-sec{padding:40px 24px;text-align:center;background:rgba(248,250,252,.05)}.social-sec h2{font-size:1.5rem;font-weight:800;margin-bottom:16px}.social-btns{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}.social-btns a{display:inline-flex;align-items:center;gap:6px;padding:10px 20px;border-radius:50px;color:#fff;font-weight:700;font-size:.85rem;text-decoration:none;transition:transform .2s}.social-btns a:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.2)}
.claim-banner{background:linear-gradient(135deg,#f8fafc,#ede9fe);padding:16px 24px;text-align:center;border-top:1px solid #e2e8f0}.claim-inner{display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap}.claim-inner span{font-size:.9rem;font-weight:600;color:#1e293b}.claim-inner button{background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff;border:none;padding:10px 20px;border-radius:50px;font-weight:700;font-size:.85rem;cursor:pointer}.claim-modal{position:fixed;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(4px);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px}.claim-box{background:#fff;border-radius:20px;padding:32px;max-width:420px;width:100%;position:relative;max-height:90vh;overflow-y:auto}.claim-close{position:absolute;top:12px;right:16px;background:none;border:none;font-size:1.5rem;cursor:pointer;color:#94a3b8}.claim-box h2{font-size:1.3rem;font-weight:800;margin-bottom:6px}.claim-sub{color:#64748b;font-size:.88rem;margin-bottom:16px}.claim-features{display:flex;flex-direction:column;gap:8px;margin-bottom:20px}.cf{font-size:.85rem;font-weight:500;color:#1e293b}.claim-price{text-align:center;margin-bottom:16px}.price-old{text-decoration:line-through;color:#94a3b8;font-size:.9rem;margin-right:8px}.price-new{font-size:2rem;font-weight:900;color:#7c3aed}.price-new small{font-size:.9rem;font-weight:500}.claim-btn{display:block;text-align:center;background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff;padding:14px;border-radius:12px;font-weight:700;font-size:1rem;text-decoration:none;margin-bottom:10px}.claim-btn:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(124,58,237,.3)}.claim-skip{display:block;width:100%;background:none;border:none;color:#94a3b8;font-size:.8rem;cursor:pointer;padding:8px;text-decoration:underline}
</style>
"""

def generate_html(content: dict, template: str, lead: dict = None, website_id_override: str = "") -> str:
    if "raw_content" in content:
        raw = content["raw_content"]
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        try:
            content = json.loads(raw)
        except json.JSONDecodeError:
            pass

    hero_title = content.get("hero_title", "Welcome")
    hero_subtitle = content.get("hero_subtitle", "")
    about = content.get("about", "")
    services = content.get("services", [])
    testimonials = content.get("testimonials", [])
    cta_text = content.get("cta_text", "Contact Us")
    contact = content.get("contact_info", {})
    colors = content.get("color_scheme", {"primary": "#6366f1", "secondary": "#e0e7ff", "accent": "#10b981"})
    seo_title = content.get("seo_title", hero_title)
    seo_desc = content.get("seo_description", hero_subtitle)
    features = content.get("features", [])
    primary = colors.get("primary", "#6366f1")
    secondary = colors.get("secondary", "#e0e7ff")
    accent = colors.get("accent", "#F59E0B")

    category = (lead.get("category", "") if lead else "") or template
    logo_url = content.get("logo_url", "") if isinstance(content, dict) else ""

    # Try to get real photos from Google Maps
    # Use stored photos from content first (saved during generation)
    real_photos = content.get("real_photos", []) if isinstance(content, dict) else []
    # If no stored photos, try fetching from Google Maps
    if not real_photos and lead:
        real_photos = _get_real_photos(lead.get("business_name", ""), lead.get("address", ""))
        # Store for next time (avoid re-fetching)
        if real_photos and isinstance(content, dict):
            try:
                from app.core.supabase import get_supabase as _gdb
                content["real_photos"] = real_photos
                if website_id:
                    _gdb().table("websites").update({"content": content}).eq("id", website_id).execute()
            except Exception:
                pass
    images = get_images_for_category(category)
    gallery_images = real_photos if real_photos else [
        f"https://image.pollinations.ai/prompt/{category}+business+product+showcase+photo+{i}?width=500&height=500&nologo=true" for i in range(1, 5)
    ]
    hero_img = real_photos[0] if real_photos else f"https://image.pollinations.ai/prompt/professional+{category}+business+interior+modern+high+quality?width=1400&height=800&nologo=true"
    about_img = real_photos[1] if len(real_photos) > 1 else f"https://image.pollinations.ai/prompt/{category}+business+team+professional+indian?width=800&height=600&nologo=true"
    gallery = images["gallery"]

    phone = contact.get("phone", lead.get("phone", "") if lead else "")
    email = contact.get("email", lead.get("email", "") if lead else "")
    address = contact.get("address", lead.get("address", "") if lead else "")
    hours = contact.get("hours", "Mon-Sat: 9 AM - 8 PM")
    business_name = lead.get("business_name", hero_title) if lead else hero_title
    whatsapp_num = phone.replace("-", "").replace(" ", "").replace("+", "") if phone else ""
    short_name = business_name.split()[0] if business_name else "Biz"
    maps_url = get_maps_embed(address, business_name)
    dir_url = "https://www.google.com/maps/dir/?api=1&destination=" + urllib.parse.quote(address) if address else "#"

    # Get website_id for dashboard link
    website_id = website_id_override or ""
    if not website_id and lead and lead.get("id"):
        try:
            from app.core.supabase import get_supabase as _gsb
            _wr = _gsb().table("websites").select("id").eq("lead_id", lead["id"]).limit(1).execute()
            if _wr.data:
                website_id = _wr.data[0]["id"]
        except Exception:
            pass

    svc_cards = []
    for i, svc in enumerate(services[:6]):
        # Use real photos if available, otherwise use gallery images cycling
        if real_photos and i < len(real_photos):
            img = real_photos[i]
        else:
            img = gallery_images[i % len(gallery_images)]
        svc_cards.append(
            '<article class="service-card" data-aos="fade-up">'
            f'<div class="service-img" style="background-image:url({img})"></div>'
            f'<div class="service-content"><h3>{svc.get("name","")}</h3>'
            f'<p>{svc.get("description","")}</p><a href="#contact" style="display:inline-block;margin-top:10px;padding:6px 14px;background:var(--p);color:#fff;border-radius:6px;font-size:.72rem;font-weight:600;text-decoration:none">Explore &rarr;</a></div></article>'
        )
    services_html = "".join(svc_cards)

    test_cards = []
    for t in testimonials[:3]:
        stars = "&#9733;" * t.get("rating", 5)
        test_cards.append(
            '<div class="testimonial-card" data-aos="fade-up">'
            f'<div class="testimonial-avatar">{t.get("name","A")[0]}</div>'
            f'<div class="stars">{stars}</div>'
            f'<blockquote>{t.get("text","")}</blockquote>'
            f'<cite>{t.get("name","")}</cite></div>'
        )
    testimonials_html = "".join(test_cards)

    # Use real Google Maps photos if available, otherwise fallback to stock
    gal_items = []
    # Fetch products for this business
    products_html = ""
    if website_id:
        try:
            from app.core.supabase import get_supabase as _pdb
            _pr = _pdb().table("store_products").select("*").eq("website_id", website_id).eq("in_stock", True).limit(6).execute()
            if _pr.data:
                prod_cards = ""
                for p in _pr.data:
                    p_img = p.get("image_url") or f"https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&h=300&fit=crop"
                    wa_msg = urllib.parse.quote(f"Hi, I want to buy {p.get('name','')} (Rs.{p.get('price','')})")
                    wa_link = f"https://wa.me/{whatsapp_num}?text={wa_msg}" if whatsapp_num else "#"
                    prod_cards += (
                        f'<div class="product-item" data-aos="fade-up">'
                        f'<img src="{p_img}" alt="{p.get("name","")}" style="width:100%;height:110px;object-fit:cover;border-radius:10px">'
                        f'<h3 style="font-size:.9rem;font-weight:700;margin:10px 0 4px">{p.get("name","")}</h3>'
                        f'<p style="font-size:.8rem;color:#64748b;margin-bottom:6px">{p.get("description","")[:50]}</p>'
                        f'<p style="font-size:1rem;font-weight:800;color:var(--p);margin-bottom:8px">Rs. {p.get("price","")}</p>'
                        f'<a href="{wa_link}" target="_blank" style="display:block;text-align:center;background:var(--p);color:#fff;padding:8px;border-radius:8px;font-size:.78rem;font-weight:700;text-decoration:none">Buy Now</a>'
                        f'</div>'
                    )
                products_html = (
                    '<section class="section" style="padding:60px 24px"><div style="max-width:1100px;margin:0 auto">'
                    '<div class="section-header" data-aos="fade-up"><h2>Our Products</h2></div>'
                    f'<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px">{prod_cards}</div>'
                    '</div></section>'
                )
        except Exception:
            pass

    # Custom gallery from owner (Instagram/Facebook photos)
    custom_gallery = content.get("custom_gallery", []) if isinstance(content, dict) else []
    if custom_gallery:
        gallery_images = custom_gallery + gallery_images  # Custom photos first

    for img_url in gallery_images[:6]:
        gal_items.append(f'<figure class="gallery-item" data-aos="zoom-in" onclick="openLb(\'{img_url}\')"><img src="{img_url}" alt="Gallery" loading="lazy" style="cursor:pointer"></figure>')
    gallery_html = "".join(gal_items)

    # Icon to emoji mapping
    ICON_EMOJI = {
        "dumbbell": "\U0001f3cb\ufe0f", "heart-pulse": "\U0001f493", "person-running": "\U0001f3c3",
        "medal": "\U0001f3c5", "utensils": "\U0001f37d\ufe0f", "wine-glass": "\U0001f377",
        "fire": "\U0001f525", "star": "\u2b50", "scissors": "\u2702\ufe0f",
        "spa": "\U0001f486", "paint-brush": "\U0001f3a8", "gem": "\U0001f48e",
        "tooth": "\U0001f9b7", "smile": "\U0001f60a", "shield-halved": "\U0001f6e1\ufe0f",
        "award": "\U0001f3c6", "stethoscope": "\U0001fa7a", "user-doctor": "\U0001f468\u200d\u2695\ufe0f",
        "hospital": "\U0001f3e5", "heart": "\u2764\ufe0f", "bag-shopping": "\U0001f6cd\ufe0f",
        "truck-fast": "\U0001f69a", "tags": "\U0001f3f7\ufe0f", "gift": "\U0001f381",
        "check-circle": "\u2705", "clock": "\u23f0", "thumbs-up": "\U0001f44d",
        "shield-alt": "\U0001f6e1\ufe0f", "bolt": "\u26a1", "handshake": "\U0001f91d",
        "users": "\U0001f465", "tools": "\U0001f527", "home": "\U0001f3e0",
        "phone": "\U0001f4de", "map-marker-alt": "\U0001f4cd", "envelope": "\u2709\ufe0f",
        "solar-panel": "\u2600\ufe0f", "money-bag": "\U0001f4b0", "leaf": "\U0001f33f",
        "support": "\U0001f3a7", "globe": "\U0001f30d", "rocket": "\U0001f680",
        "lightbulb": "\U0001f4a1", "trophy": "\U0001f3c6", "crown": "\U0001f451",
        "user-cog": "\U0001f464", "user": "\U0001f464", "cog": "\u2699\ufe0f",
        "wrench": "\U0001f527", "hammer": "\U0001f528", "brain": "\U0001f9e0",
    }

    def icon_to_emoji(icon_str):
        if not icon_str:
            return "\u2728"
        # Already an emoji (has non-ASCII chars)
        if any(ord(c) > 127 for c in icon_str):
            return icon_str
        # Extract name from "fas fa-xxx" format
        name = icon_str.lower().strip()
        if "fa-" in name:
            name = name.split("fa-")[-1].strip()
        name = name.replace("fas ", "").replace("far ", "").replace("fab ", "").strip()
        return ICON_EMOJI.get(name, "\u2728")

    feat_items = []
    for f in features:
        emoji = icon_to_emoji(f.get("icon", ""))
        feat_items.append(
            '<div class="feature-item" data-aos="fade-up">'
            f'<div class="feature-icon">{emoji}</div>'
            f'<h3>{f.get("title","")}</h3>'
            f'<p>{f.get("description","")}</p></div>'
        )
    features_html = "".join(feat_items)

    # How it works section
    how_it_works = content.get("how_it_works", [])
    hiw_html = ""
    if how_it_works:
        hiw_items = ""
        for step in how_it_works:
            hiw_items += (
                f'<div class="hiw-item"><div class="hiw-number">{step.get("step","")}</div>'
                f'<h3>{step.get("title","")}</h3><p>{step.get("description","")}</p></div>'
            )
        hiw_html = f'<section class="section" style="background:#f8fafc;max-width:100%"><div style="max-width:1100px;margin:0 auto;padding:60px 24px"><div class="section-header"><h2>How It Works</h2></div><div class="hiw-grid">{hiw_items}</div><div style="display:flex;gap:20px;margin-top:32px;flex-wrap:wrap">' + f'<div style="text-align:center"><span style="font-size:1.5rem;font-weight:800;display:block">{lead.get("rating", "4.8") if lead else "4.8"}</span><span style="font-size:.7rem;opacity:.7">Rating</span></div><div style="text-align:center"><span style="font-size:1.5rem;font-weight:800;display:block">{lead.get("review_count", "50") if lead else "50"}+</span><span style="font-size:.7rem;opacity:.7">Reviews</span></div><div style="text-align:center"><span style="font-size:1.5rem;font-weight:800;display:block">5+</span><span style="font-size:.7rem;opacity:.7">Years</span></div>' + '</div></div></section>'

    # Benefits section
    benefits = content.get("benefits", [])
    benefits_html = ""
    if benefits:
        ben_items = "".join([f'<div class="benefit-item">\u2713 {b}</div>' for b in benefits])
        benefits_html = f'<section class="section benefits-section"><div class="section-header"><h2>Benefits</h2></div><div class="benefits-grid">{ben_items}</div></section>'

    # Why choose us
    why_choose = content.get("why_choose_us", [])
    why_html = ""
    if why_choose:
        why_items = ""
        for w in why_choose:
            why_items += f'<div class="why-item"><div class="why-icon">{w.get("icon", chr(10024))}</div><h3>{w.get("title","")}</h3><p>{w.get("description","")}</p></div>'
        why_html = f'<section class="section"><div class="section-header"><h2>Our Strengths</h2></div><div class="why-grid">{why_items}</div></section>'

    # FAQ section
    faq = content.get("faq", [])
    faq_html = ""
    if faq:
        faq_items = ""
        for q in faq:
            faq_items += f'<details class="faq-item"><summary>{q.get("question","")}</summary><p>{q.get("answer","")}</p></details>'
        faq_html = f'<section class="section"><div class="section-header"><h2>Frequently Asked Questions</h2></div><div class="faq-list">{faq_items}</div></section>'

    # Hero offer badge
    hero_offer = content.get("hero_offer", "")
    trust_badges = content.get("trust_badges", [])

    maps_section = ""
    if maps_url:
        maps_section = (
            '<section style="max-width:1200px;margin:0 auto;padding:0 24px 80px">'
            f'<iframe src="{maps_url}" width="100%" height="400" '
            'style="border:0;border-radius:16px" allowfullscreen loading="lazy"></iframe></section>'
        )

    wa_link = ""
    bottom_nav = ""
    if whatsapp_num:
        wa_msg = f"Hi {business_name}, I visited your website and I'm interested in your services. Can we discuss?"
        import urllib.parse as _up
        wa_encoded = _up.quote(wa_msg)
        wa_link = f'<a href="https://wa.me/{whatsapp_num}?text={wa_encoded}" target="_blank" class="whatsapp-float"><svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492l4.625-1.476A11.929 11.929 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75c-2.115 0-4.09-.57-5.793-1.564l-.415-.248-2.74.875.876-2.672-.27-.43A9.71 9.71 0 012.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75z"/></svg></a>'

        # Bottom mobile nav
        bottom_nav = (
            '<div class="bottom-nav"><div class="bottom-nav-grid">'
            f'<a href="tel:{phone}"><span class="bn-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg></span>Call Now</a>'
            f'<a href="https://wa.me/{whatsapp_num}" target="_blank"><span class="bn-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492l4.625-1.476A11.929 11.929 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75c-2.115 0-4.09-.57-5.793-1.564l-.415-.248-2.74.875.876-2.672-.27-.43A9.71 9.71 0 012.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75z"/></svg></span>WhatsApp</a>'
            f'<a href="{dir_url}" target="_blank"><span class="bn-icon">&#128205;</span>Location</a>'
            '<a href="#gallery"><span class="bn-icon">&#128247;</span>Gallery</a>'
            '</div></div>'
        ) if phone else ""


    css = f"""<style>
:root{{--p:{primary};--ps:{secondary};--ac:{accent};--ink:#0f172a;--mute:#64748b;--line:#e2e8f0;--bg:#fff;--soft:#f8fafc}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{font-family:'Plus Jakarta Sans',Inter,system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden}}
h1,h2,h3{{line-height:1.15;letter-spacing:-.02em}}
a{{text-decoration:none;color:inherit}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 24px}}
.tag{{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--p);background:color-mix(in srgb,var(--p) 8%,transparent);padding:6px 14px;border-radius:50px;margin-bottom:14px}}

/* NAV */
.nav{{position:fixed;top:0;left:0;right:0;z-index:1000;padding:18px 32px;display:flex;align-items:center;justify-content:space-between;transition:all .4s}}
.nav.solid{{background:rgba(255,255,255,.92);backdrop-filter:saturate(180%) blur(20px);box-shadow:0 1px 3px rgba(0,0,0,.06);padding:13px 32px}}
.nav.solid .nav-brand,.nav.solid .nav-links a{{color:var(--ink)}}
.nav-brand{{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.15rem;color:#fff;display:flex;align-items:center;gap:10px}}
.nav-brand .logo{{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,var(--p),var(--ps));display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px color-mix(in srgb,var(--p) 40%,transparent)}}
.nav-links{{display:flex;gap:28px}}.nav-links a{{font-size:.88rem;font-weight:600;color:rgba(255,255,255,.85);transition:color .2s}}.nav-links a:hover{{color:#fff}}.nav.solid .nav-links a:hover{{color:var(--p)}}
.nav-cta{{background:transparent;color:#fff!important;padding:8px 16px;border-radius:8px;font-weight:700;font-size:.85rem;display:flex;align-items:center;gap:6px;border:1.5px solid rgba(255,255,255,.6);transition:all .25s}}.nav-cta:hover{{background:rgba(255,255,255,.12);transform:translateY(-1px)}}

/* HERO */
.hero{{position:relative;min-height:100vh;display:flex;align-items:center;overflow:hidden}}
.hero-bg{{position:absolute;inset:0;background:url('{real_photos[0] if real_photos else hero_img}') center/cover no-repeat;transform:scale(1.05);animation:heroZ 20s ease-in-out infinite alternate}}
@keyframes heroZ{{to{{transform:scale(1)}}}}
.hero-overlay{{position:absolute;inset:0;background:linear-gradient(125deg,rgba(5,5,20,.84) 0%,rgba(5,5,20,.5) 50%,rgba(5,5,20,.3) 100%)}}.hero::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:5px;background:linear-gradient(90deg,var(--p),var(--ps),var(--ac));z-index:3}}
.hero-glow{{position:absolute;top:-20%;right:-10%;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,color-mix(in srgb,var(--p) 40%,transparent),transparent 65%);filter:blur(40px);opacity:.6}}
.hero-content{{position:relative;z-index:2;max-width:720px;padding:110px 24px 60px;margin-left:5%}}
.hero-pill{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);backdrop-filter:blur(6px);padding:8px 16px;border-radius:50px;font-size:.82rem;font-weight:600;color:#fff;margin-bottom:20px}}.hero-offer{{display:inline-block;color:#fff;font-weight:600;font-size:.92rem;padding:0;margin-bottom:18px;opacity:.9}}
.hero h1{{font-size:clamp(1.6rem,3.5vw,2.6rem);font-weight:800;color:#fff;margin-bottom:14px;text-shadow:0 2px 20px rgba(0,0,0,.3)}}
.hero p{{font-size:clamp(.88rem,1.5vw,1rem);color:rgba(255,255,255,.88);max-width:560px;margin-bottom:14px}}
.offer-pill{{display:inline-block;background:var(--ac);color:#fff;font-weight:700;font-size:.88rem;padding:9px 18px;border-radius:10px;margin-bottom:22px;box-shadow:0 8px 24px color-mix(in srgb,var(--ac) 40%,transparent)}}
.hero-btns{{display:flex;flex-wrap:wrap;gap:12px;margin-top:6px}}
.btn{{display:inline-flex;align-items:center;gap:8px;padding:11px 22px;border-radius:10px;font-weight:700;font-size:.82rem;transition:transform .25s,box-shadow .25s;border:none;cursor:pointer}}
.btn-main{{background:#fff;color:var(--p);box-shadow:0 10px 30px rgba(0,0,0,.25)}}.btn-main:hover{{transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,.35)}}
.btn-wa{{background:#25D366;color:#fff;box-shadow:0 8px 24px rgba(37,211,102,.4)}}.btn-wa:hover{{transform:translateY(-2px)}}
.btn-outline{{background:rgba(255,255,255,.92);color:var(--p);border:1.5px solid #fff;font-weight:700}}.btn-outline:hover{{background:#fff;transform:translateY(-2px);box-shadow:0 8px 24px rgba(255,255,255,.3)}}
.badges{{display:flex;flex-wrap:wrap;gap:8px;margin-top:28px}}.badge-item{{font-size:.78rem;font-weight:600;color:rgba(255,255,255,.9);background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);padding:6px 13px;border-radius:50px}}
.hero-badge{{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);padding:8px 16px;border-radius:50px;font-size:.85rem;margin-bottom:24px;backdrop-filter:blur(4px)}}

/* STATS */
.stats-section{{background:url('https://images.unsplash.com/photo-1497366216548-37526070297c?w=1200&h=300&fit=crop') center/cover;padding:36px 24px;position:relative;overflow:hidden}}.stats-section::before{{content:'';position:absolute;inset:0;background:rgba(15,23,42,.75);backdrop-filter:blur(2px)}}.stats-section::before{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 70% 20%,rgba(255,255,255,.12),transparent 55%)}}
.stats-grid{{position:relative;display:grid;grid-template-columns:repeat(4,1fr);gap:16px;max-width:1000px;margin:0 auto;text-align:center}}.stat-item{{color:#fff}}.stat-number{{font-size:clamp(1.4rem,2.5vw,2rem);font-weight:800}}.stat-label{{font-size:.82rem;opacity:.75;margin-top:4px;font-weight:500}}

/* SECTIONS */
.section{{padding:60px 24px;max-width:1180px;margin:0 auto}}
.section-alt{{background:var(--soft);max-width:100%;padding:60px 24px}}.section-alt .section-inner{{max-width:1180px;margin:0 auto}}
.section-header{{text-align:center;margin-bottom:32px}}
.section-header h2{{font-size:clamp(1.25rem,2.5vw,1.7rem);font-weight:800}}.section-header p{{color:var(--mute);margin-top:8px;font-size:.85rem}}

/* ABOUT */
.about-grid{{display:grid;grid-template-columns:1.1fr 1fr;gap:36px;align-items:center}}
.about-img{{position:relative}}.about-img img{{width:100%;height:360px;object-fit:cover;border-radius:20px;box-shadow:0 32px 64px rgba(15,23,42,.16);filter:brightness(1.05) contrast(1.05) saturate(1.1)}}
.about-badge{{position:absolute;bottom:-20px;left:-16px;background:#fff;border-radius:16px;padding:18px 22px;box-shadow:0 16px 40px rgba(15,23,42,.12);display:flex;align-items:center;gap:12px}}
.about-badge .big{{font-size:1.7rem;font-weight:800;color:var(--p)}}.about-badge .sm{{font-size:.75rem;color:var(--mute);font-weight:600}}
.about-text h2{{font-size:clamp(1.2rem,2.5vw,1.6rem);font-weight:800;margin-bottom:12px}}.about-text p{{color:var(--mute);font-size:.85rem;line-height:1.7}}

/* SERVICES */
.services-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}}
.service-card{{background:#fff;border-radius:20px;overflow:hidden;border:1px solid var(--line);transition:transform .4s cubic-bezier(.16,1,.3,1),box-shadow .4s}}
.service-card:hover{{transform:translateY(-8px);box-shadow:0 24px 48px rgba(15,23,42,.12)}}.service-card::after{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--p),var(--ps));opacity:0;transition:opacity .3s}}.service-card:hover::after{{opacity:1}}
.service-img{{height:200px;background-size:cover;background-position:center;position:relative}}.service-img::after{{content:'';position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.5),transparent 60%)}}
.service-emoji{{position:absolute;bottom:12px;left:14px;z-index:1;width:44px;height:44px;border-radius:12px;background:rgba(255,255,255,.95);display:flex;align-items:center;justify-content:center;font-size:1.4rem;box-shadow:0 6px 16px rgba(0,0,0,.15)}}
.service-content{{padding:22px 20px}}.service-content h3{{font-size:.95rem;font-weight:700;margin-bottom:8px}}.service-content p{{color:var(--mute);font-size:.82rem}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}}.chip{{font-size:.72rem;font-weight:600;color:var(--p);background:color-mix(in srgb,var(--p) 8%,transparent);padding:4px 10px;border-radius:50px}}

/* FEATURES */
.features-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:22px}}
.feature-item{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:30px 24px;transition:transform .35s,box-shadow .35s}}
.feature-item:hover{{transform:translateY(-6px);box-shadow:0 20px 44px rgba(15,23,42,.09)}}
.feature-icon{{width:44px;height:44px;border-radius:50%;background:color-mix(in srgb,var(--p) 8%,#fff);border:2px solid color-mix(in srgb,var(--p) 25%,transparent);display:flex;align-items:center;justify-content:center;font-size:1.2rem;margin-bottom:12px}}
.feature-item h3{{font-size:.88rem;font-weight:700;margin-bottom:6px}}.feature-item p{{color:var(--mute);font-size:.78rem}}

/* GALLERY */
.gallery-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}}
.gallery-item{{border-radius:16px;overflow:hidden;aspect-ratio:4/3}}.gallery-item img{{width:100%;height:100%;object-fit:cover;transition:transform .5s cubic-bezier(.16,1,.3,1);filter:brightness(1.05) contrast(1.05) saturate(1.1)}}.gallery-item:hover img{{transform:scale(1.06)}}

/* TESTIMONIALS */
.testimonials-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px}}
.testimonial-card{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:30px 26px;transition:transform .35s,box-shadow .35s}}
.testimonial-card:hover{{transform:translateY(-5px);box-shadow:0 20px 44px rgba(15,23,42,.09)}}.testimonial-card::before{{content:'\201C';position:absolute;top:14px;right:18px;font-size:2.5rem;color:color-mix(in srgb,var(--p) 12%,transparent);font-family:serif;line-height:1}}
.testimonial-avatar{{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--ps));color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1rem;margin-bottom:14px}}
.stars{{color:#f59e0b;font-size:1.05rem;margin-bottom:14px;letter-spacing:2px}}
.testimonial-card blockquote{{color:var(--ink);font-size:.88rem;line-height:1.7;margin-bottom:18px;font-style:italic}}
.testimonial-card cite{{font-weight:700;font-style:normal;font-size:.92rem}}

/* HOW IT WORKS */
.hiw-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px}}
.hiw-item{{text-align:center}}.hiw-number{{width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--ps));color:#fff;font-size:1.3rem;font-weight:800;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;box-shadow:0 10px 24px color-mix(in srgb,var(--p) 35%,transparent)}}
.hiw-item h3{{font-size:.88rem;font-weight:700;margin-bottom:6px}}.hiw-item p{{color:var(--mute);font-size:.88rem}}

/* BENEFITS */
.benefits-grid{{list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;max-width:900px;margin:0 auto;padding:0}}
.benefit-item{{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;font-weight:600;font-size:.82rem}}
.benefit-check{{flex-shrink:0;width:26px;height:26px;border-radius:50%;background:color-mix(in srgb,var(--p) 12%,#fff);color:var(--p);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem}}
.benefits-section{{display:none}}

/* FAQ */
.faq-list{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}.faq-item{{background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;transition:box-shadow .3s}}
.faq-item[open]{{box-shadow:0 12px 32px rgba(15,23,42,.07)}}
.faq-item summary{{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;cursor:pointer;font-weight:600;font-size:.78rem;list-style:none}}
.faq-item summary::-webkit-details-marker{{display:none}}.faq-item p{{padding:0 14px 12px;color:var(--mute);font-size:.75rem;line-height:1.7}}

/* CONTACT */
.contact-section{{background:linear-gradient(135deg,#0f172a,#1e293b);color:#fff;padding:60px 24px}}
.contact-container{{max-width:1000px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:44px;align-items:start;overflow-x:hidden}}
.contact-left h2{{font-size:clamp(1.2rem,2.5vw,1.6rem);font-weight:800;margin-bottom:10px}}.contact-left .sub{{color:#94a3b8;font-size:1rem;margin-bottom:28px}}
.contact-cards{{display:flex;flex-direction:column;gap:12px}}
.contact-card{{display:flex;align-items:center;gap:14px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);padding:16px 18px;border-radius:14px;color:#fff;transition:background .25s}}.contact-card:hover{{background:rgba(255,255,255,.08)}}
.contact-card-icon{{width:42px;height:42px;border-radius:11px;background:linear-gradient(135deg,var(--p),var(--ps));display:flex;align-items:center;justify-content:center;font-size:1.15rem;flex-shrink:0}}
.contact-card-label{{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#64748b}}.contact-card-value{{font-size:.92rem;font-weight:600;margin-top:2px;color:#e2e8f0}}
.contact-form{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:28px}}
.contact-form h3{{font-size:1.2rem;margin-bottom:4px}}.contact-form .fsub{{color:#94a3b8;font-size:.85rem;margin-bottom:18px}}
.contact-form input,.contact-form textarea{{width:100%;padding:13px 15px;margin-bottom:12px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:10px;color:#fff;font-size:.92rem;font-family:inherit;outline:none;transition:border .2s}}
.contact-form input:focus,.contact-form textarea:focus{{border-color:var(--p)}}.contact-form input::placeholder,.contact-form textarea::placeholder{{color:#6b7280}}
.contact-form button{{width:100%;background:var(--p);color:#fff;padding:14px;border:none;border-radius:10px;font-weight:700;font-size:.95rem;cursor:pointer;transition:transform .2s,box-shadow .2s}}.contact-form button:hover{{transform:translateY(-2px);box-shadow:0 10px 28px color-mix(in srgb,var(--p) 45%,transparent)}}

/* FOOTER */
.footer{{background:#070a13;color:#94a3b8;padding:48px 24px 28px}}
.footer-inner{{max-width:1000px;margin:0 auto}}
.footer-top{{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:20px;padding-bottom:24px;border-bottom:1px solid rgba(255,255,255,.06)}}
.footer-brand{{display:flex;align-items:center;gap:10px;color:#fff;font-weight:800;font-size:1.1rem}}
.footer-links{{display:flex;gap:22px;flex-wrap:wrap}}.footer-links a{{color:#94a3b8;font-size:.88rem;font-weight:500;transition:color .2s}}.footer-links a:hover{{color:#fff}}
.footer-bottom{{display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;padding-top:20px;font-size:.82rem}}.footer-bottom .kd{{color:#e2e8f0;font-weight:600}}

/* WHATSAPP FLOAT */
.whatsapp-float{{position:fixed;bottom:24px;right:24px;z-index:998;width:58px;height:58px;border-radius:50%;background:#25D366;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 26px rgba(37,211,102,.45);animation:waPulse 2.2s infinite;transition:transform .2s}}.whatsapp-float:hover{{transform:scale(1.08)}}
@keyframes waPulse{{0%,100%{{box-shadow:0 8px 26px rgba(37,211,102,.45)}}50%{{box-shadow:0 8px 36px rgba(37,211,102,.75)}}}}

/* CHAT */
.chat-btn{{position:fixed;bottom:24px;left:24px;z-index:998;width:58px;height:58px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--ps));display:flex;align-items:center;justify-content:center;font-size:1.4rem;cursor:pointer;box-shadow:0 8px 26px color-mix(in srgb,var(--p) 45%,transparent);transition:transform .2s;border:none;color:#fff}}.chat-btn:hover{{transform:scale(1.08)}}
.chat-panel{{position:fixed;bottom:94px;left:24px;z-index:999;width:340px;max-width:calc(100vw - 48px);background:#fff;border-radius:18px;box-shadow:0 24px 60px rgba(15,23,42,.25);overflow:hidden;display:none;flex-direction:column;border:1px solid var(--line)}}
.chat-panel.open{{display:flex;animation:chatIn .3s ease}}
@keyframes chatIn{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
.chat-hd{{background:linear-gradient(135deg,var(--p),var(--ps));color:#fff;padding:16px 18px;font-weight:700;font-size:.95rem;display:flex;align-items:center;gap:9px}}
.chat-hd .dot{{width:8px;height:8px;border-radius:50%;background:#4ade80;animation:dotP 2s infinite}}
@keyframes dotP{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
.chat-msgs{{height:260px;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:var(--soft)}}
.chat-msg{{max-width:82%;padding:10px 14px;border-radius:12px;font-size:.88rem;line-height:1.5}}
.chat-msg.bot{{background:#fff;border:1px solid var(--line);align-self:flex-start;border-bottom-left-radius:3px}}
.chat-msg.user{{background:var(--p);color:#fff;align-self:flex-end;border-bottom-right-radius:3px}}
.chat-input{{display:flex;gap:8px;padding:12px;border-top:1px solid var(--line);background:#fff}}.chat-input input{{flex:1;padding:10px 14px;border:1px solid var(--line);border-radius:50px;outline:none;font-size:.88rem}}.chat-input button{{background:var(--p);color:#fff;border:none;width:38px;height:38px;border-radius:50%;cursor:pointer;font-size:1rem;flex-shrink:0;display:flex;align-items:center;justify-content:center}}

/* AOS */
[data-aos]{{transition-timing-function:cubic-bezier(.16,1,.3,1)}}

.contact-section input,.contact-section textarea{{max-width:100%!important;width:100%!important}}


/* STICKY BOTTOM NAV (Mobile) */
.bottom-nav{{display:none;position:fixed;bottom:0;left:0;right:0;z-index:1000;background:linear-gradient(135deg,var(--p),var(--ps));padding:14px 16px;border-top:none;box-shadow:0 -6px 30px rgba(0,0,0,.25);backdrop-filter:blur(10px);border-radius:20px 20px 0 0}}
.bottom-nav-grid{{display:flex;justify-content:space-around;align-items:center;max-width:400px;margin:0 auto}}
.bottom-nav a{{display:flex;flex-direction:column;align-items:center;gap:4px;text-decoration:none;color:rgba(255,255,255,.9);font-size:.68rem;font-weight:600;padding:8px 16px;border-right:1px solid rgba(255,255,255,.2);transition:all .2s}}.bottom-nav a:last-child{{border-right:none}}.bottom-nav a:hover,.bottom-nav a:active{{background:rgba(255,255,255,.15);border-radius:10px;transform:scale(.92)}}.bottom-nav a{{transition:all .2s cubic-bezier(.4,0,.2,1)}}
.bottom-nav a:nth-child(1){{color:#fff}}.bn-icon{{font-size:1.4rem;line-height:1;display:flex;align-items:center;justify-content:center;width:28px;height:28px}}.bn-icon svg{{width:22px;height:22px}}
.bottom-nav a span.bn-icon{{font-size:1.3rem}}

/* Improved Buttons */
.btn-main,.btn-white{{background:#fff;color:var(--p);border-radius:50px;font-size:.95rem;padding:14px 28px;font-weight:700;box-shadow:0 4px 20px rgba(0,0,0,.25);transition:all .3s}}.btn-white:hover{{transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,0,0,.35)}}.btn-glass{{background:rgba(255,255,255,.92);color:var(--p);border-radius:50px;font-size:.95rem;padding:14px 28px;font-weight:700;border:2px solid #fff;transition:all .3s}}.btn-glass:hover{{background:#fff;transform:translateY(-2px)}}
.btn-wa{{border-radius:50px;padding:14px 28px}}
.btn-outline{{border-radius:50px;padding:12px 24px;font-weight:600}}

/* Features 2x2 grid on mobile */
@media(max-width:860px){{
.bottom-nav{{display:block}}
.whatsapp-float{{bottom:80px}}
.chat-btn{{bottom:80px}}
body{{padding-bottom:70px}}
.hero-content{{padding-bottom:60px!important}}
.features-grid{{grid-template-columns:repeat(2,1fr)!important;gap:12px!important}}
.feature-item{{padding:16px 12px!important;border-radius:12px!important}}
.feature-icon{{width:40px!important;height:40px!important;font-size:1.2rem!important;margin-bottom:10px!important}}
.feature-item h3{{font-size:.85rem!important}}
.feature-item p{{font-size:.75rem!important}}
.services-grid{{grid-template-columns:1fr!important;gap:12px!important}}
.service-card{{display:flex!important;flex-direction:row!important;border-radius:12px!important;overflow:hidden}}
.service-img{{width:80px!important;height:80px!important;min-height:80px!important;flex-shrink:0}}
.service-content{{padding:12px!important}}
.service-content h3{{font-size:.9rem!important;margin-bottom:4px!important}}
.service-content p{{font-size:.78rem!important;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.gallery-grid{{grid-template-columns:repeat(3,1fr)!important;gap:6px!important}}
.gallery-item{{border-radius:8px!important}}
.hero h1{{font-size:1.8rem!important}}
.section-header h2{{font-size:1.5rem!important}}
.testimonials-grid{{grid-template-columns:1fr!important}}
.nav-cta{{padding:8px 14px!important;font-size:.75rem!important}}.hero-btns{{flex-direction:column!important;gap:10px!important;align-items:flex-start!important}}.btn-main,.btn-wa,.btn-outline{{padding:12px 24px!important;font-size:.88rem!important;width:auto}}
}}

</style>"""

    # Social follow section - uses saved links or defaults to search
    biz_search = business_name.replace(" ", "+")
    social_links = content.get("social_links", {}) if isinstance(content, dict) else {}
    insta_url = social_links.get("instagram") or f"https://www.instagram.com/explore/tags/{category}/"
    fb_url = social_links.get("facebook") or f"https://www.facebook.com/search/pages/?q={biz_search}"
    yt_url = social_links.get("youtube", "")
    yt_btn = f'<a href="{yt_url}" target="_blank" style="background:#ff0000">YouTube</a>' if yt_url else f'<a href="https://www.google.com/maps/search/{biz_search}" target="_blank" style="background:#4285f4">Google Maps</a>'
    social_html = (
        '<section class="social-sec">'
        '<p style="font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--p);margin-bottom:8px">Follow Us</p>'
        '<h2>Stay Connected</h2>'
        '<div class="social-btns">'
        f'<a href="{insta_url}" target="_blank" style="background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)">Instagram</a>'
        f'<a href="{fb_url}" target="_blank" style="background:#1877f2">Facebook</a>'
        f'{yt_btn}'
        '</div></section>'
    )

    html = (
        '<!DOCTYPE html><html lang="en"><head>'
        f'<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><meta name="theme-color" content="{primary}">'
        f'<title>{seo_title}</title><meta name="description" content="{seo_desc}">'
        f'<meta property="og:image" content="{hero_img}">'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800;900&display=swap" rel="stylesheet">'
        f'<meta name="theme-color" content="{primary}">'
        '<meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        f'<link rel="apple-touch-icon" href="https://ui-avatars.com/api/?name={short_name}&background={primary[1:]}&color=fff&size=180">'
        f'{css}<style>{_get_design_css(category)}</style>{MOBILE_CSS}</head><body>'
        f'<nav class="nav" id="mainNav"><div class="nav-brand"><svg width="36" height="36" viewBox="0 0 36 36" style="margin-right:8px;vertical-align:middle"><rect width="36" height="36" rx="8" fill="{primary}"/><text x="18" y="24" text-anchor="middle" fill="white" font-size="18" font-weight="bold" font-family="Playfair Display,serif">{business_name[0]}</text></svg>{business_name}</div>'
        '<div class="nav-links"><a href="#about">About</a><a href="#services">Services</a><a href="#gallery">Gallery</a><a href="#contact">Contact</a></div>'
        f'<a href="tel:{phone}" class="nav-cta"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg></a></nav>'
        '<section class="hero"><div class="hero-bg"></div><div class="hero-overlay"></div><div class="hero-glow"></div>'
        f'<div class="hero-content"><div class="hero-pill">&#9733; Trusted by {lead.get("review_count", 100) if lead else 100}+ customers</div><h1>{hero_title}</h1><p>{hero_subtitle}</p>' + (f'<div class="hero-offer">{hero_offer}</div>' if hero_offer else '') +
        f'<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center"><a href="#contact" class="btn btn-white">{cta_text}</a><a href="https://www.google.com/maps/dir/?api=1&destination={address.replace(" ", "+")}" target="_blank" class="btn btn-glass">&#128205; Get Directions</a></div></div></section>'
        '<section class="section" id="about"><div class="about-grid">'
        f'<div class="about-img"><img src="{real_photos[1] if len(real_photos) > 1 else about_img}" alt="About"></div>'
        '<div><div class="section-header" style="text-align:left;margin-bottom:20px"><h2>About Us</h2></div>'
        f'<p class="about-text">{about}</p></div></div></section>'
        '<section class="stats-section"><div class="wrap"><div class="stats-grid">'
        f'<div class="stat-item"><div class="stat-number">{lead.get("review_count", 100) if lead else 100}+</div><div class="stat-label">Happy Customers</div></div>'
        f'<div class="stat-item"><div class="stat-number">{lead.get("rating", 4.8) if lead else 4.8}</div><div class="stat-label">Average Rating</div></div>'
        '<div class="stat-item"><div class="stat-number">5+</div><div class="stat-label">Years Experience</div></div>'
        '<div class="stat-item"><div class="stat-number">100%</div><div class="stat-label">Satisfaction</div></div>'
        '</div></div></section>'
        '<section class="section sec section-alt" id="services"><div class="section-header"><h2>Our Services</h2></div>'
        f'<div class="services-grid">{services_html}</div></section>'
        '<section class="section" id="gallery"><div class="section-header"><h2>Gallery</h2></div>'
        f'<div class="gallery-grid">{gallery_html}</div></section>'
        ''
        f'{products_html}'
        '<section class="section"><div class="section-header"><h2>What People Say</h2></div>'
        f'<div class="testimonials-grid">{testimonials_html}</div></section>'
        f'{hiw_html}{benefits_html}{faq_html}{maps_section}'
        f'<section style="background:linear-gradient(135deg, #0f172a, #1e293b);padding:80px 24px" id="contact">'
        '<div style="max-width:1000px;margin:0 auto">'
        '<div style="text-align:center;margin-bottom:48px"><h2 style="font-family:Playfair Display,serif;font-size:2rem;font-weight:800;margin-bottom:8px;color:#fff">Get In Touch</h2><p style="color:#94a3b8;font-size:.95rem">Interested? Have questions? Reach out to us anytime.</p></div>'
        '<div class="contact-container">'
        '<div style="display:flex;flex-direction:column;gap:16px">'
        f'<div style="display:flex;align-items:center;gap:16px;background:rgba(255,255,255,0.05);padding:20px;border-radius:12px;border:1px solid rgba(255,255,255,0.1)"><div style="width:44px;height:44px;background:rgba(255,255,255,0.1);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:1.2rem">&#128205;</div><div><div style="font-size:.75rem;color:#64748b;text-transform:uppercase;letter-spacing:1px">Address</div><div style="font-size:.9rem;color:#e2e8f0;font-weight:500;margin-top:2px">{address}</div></div></div>'
        f'<a href="tel:{phone}" style="display:flex;align-items:center;gap:16px;background:rgba(255,255,255,0.05);padding:20px;border-radius:12px;border:1px solid rgba(255,255,255,0.1);text-decoration:none"><div style="width:44px;height:44px;background:rgba(255,255,255,0.1);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:1.2rem">&#128222;</div><div><div style="font-size:.75rem;color:#64748b;text-transform:uppercase;letter-spacing:1px">Phone</div><div style="font-size:.9rem;color:#e2e8f0;font-weight:500;margin-top:2px">{phone}</div></div></a>'
        f'<a href="mailto:{email}" style="display:flex;align-items:center;gap:16px;background:rgba(255,255,255,0.05);padding:20px;border-radius:12px;border:1px solid rgba(255,255,255,0.1);text-decoration:none"><div style="width:44px;height:44px;background:rgba(255,255,255,0.1);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:1.2rem">&#9993;&#65039;</div><div><div style="font-size:.75rem;color:#64748b;text-transform:uppercase;letter-spacing:1px">Email</div><div style="font-size:.9rem;color:#e2e8f0;font-weight:500;margin-top:2px">{email}</div></div></a>'
        '</div>'
        '<div style="background:rgba(255,255,255,0.05);padding:28px;border-radius:12px;border:1px solid rgba(255,255,255,0.1)">'
        '<h3 style="font-size:1rem;font-weight:600;margin-bottom:16px;color:#fff">Send a Message</h3>'
        '<form style="display:flex;flex-direction:column;gap:12px" onsubmit="event.preventDefault();alert(\'Message sent! We will contact you soon.\')">'
        '<input type="text" placeholder="Your Name" style="padding:10px 14px;border:1px solid rgba(255,255,255,0.15);border-radius:8px;font-size:.85rem;outline:none;background:rgba(255,255,255,0.05);color:#fff" required>'
        f'<input type="tel" placeholder="Your Phone" style="padding:10px 14px;border:1px solid rgba(255,255,255,0.15);border-radius:8px;font-size:.85rem;outline:none;background:rgba(255,255,255,0.05);color:#fff" required>'
        '<textarea placeholder="Your Message" rows="3" style="padding:10px 14px;border:1px solid rgba(255,255,255,0.15);border-radius:8px;font-size:.85rem;outline:none;background:rgba(255,255,255,0.05);color:#fff;resize:none" required></textarea>'
        f'<button type="submit" style="background:var(--primary);color:#fff;padding:12px;border:none;border-radius:8px;font-size:.9rem;font-weight:600;cursor:pointer">Send Message</button>'
        '</form></div>'
        '</div></div></section>'
        f'{wa_link}'
        ''
        ''
        f'<div style="text-align:center;padding:20px 24px;display:flex;justify-content:center;gap:12px"><a href="{insta_url}" target="_blank" style="width:40px;height:40px;border-radius:12px;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#bc1888);display:flex;align-items:center;justify-content:center"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="5"/><circle cx="17.5" cy="6.5" r="1.5" fill="#fff" stroke="none"/></svg></a><a href="{fb_url}" target="_blank" style="width:40px;height:40px;border-radius:12px;background:#1877f2;display:flex;align-items:center;justify-content:center"><svg width="20" height="20" viewBox="0 0 24 24" fill="#fff"><path d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z"/></svg></a></div>'
        '<div class="claim-banner"><div class="claim-inner"><span>\U0001f4bc Is this your business?</span><button onclick="document.getElementById(\'claimModal\').style.display=\'flex\'">Claim This Business</button></div></div>'
        '<div class="claim-modal" id="claimModal" style="display:none"><div class="claim-box"><button class="claim-close" onclick="document.getElementById(\'claimModal\').style.display=\'none\'">&times;</button><h2>\U0001f680 Claim Your Business</h2><p class="claim-sub">Get full control of your website + premium growth tools</p><div class="claim-features"><div class="cf">\u2705 Edit website content anytime</div><div class="cf">\u2705 Add products to your store</div><div class="cf">\u2705 View analytics (visitors, calls, leads)</div><div class="cf">\u2705 AI-powered social media posts</div><div class="cf">\u2705 Daily WhatsApp content ready to share</div><div class="cf">\u2705 QR code for visiting cards</div><div class="cf">\u2705 Google Business Profile setup guide</div><div class="cf">\u2705 Festival campaign generator</div><div class="cf">\u2705 AI chatbot for your customers</div></div><div class="claim-price"><span class="price-old">\u20b9199/month</span><span class="price-new">\u20b969<small>/month</small></span></div><a href="https://city-maps.online/api/panel/{website_id}" class="claim-btn">Claim Now \u2192</a><button class="claim-skip" onclick="document.getElementById(\'claimModal\').style.display=\'none\';window.open(\'/api/panel/{website_id}\',\'_blank\')">Skip (Testing)</button></div></div>'
        
        f'<footer class="footer"><div style="max-width:900px;margin:0 auto;display:flex;flex-direction:column;align-items:center;gap:16px"><div style="font-weight:700;font-size:1rem;color:#fff">{business_name}</div><div style="font-size:.8rem;color:#64748b">Made with &#10084;&#65039; by Kalpdev Digitals</div><div style="display:flex;gap:16px;margin-top:4px"><a href="https://wa.me/{whatsapp_num}" target="_blank" style="color:#25D366;text-decoration:none;font-size:.85rem">WhatsApp</a><a href="#contact" style="color:#94a3b8;text-decoration:none;font-size:.85rem">Contact</a><a href="https://city-maps.online/api/panel/{website_id}" target="_blank" style="color:#94a3b8;text-decoration:none;font-size:.85rem">Dashboard</a><a href="#services" style="color:#94a3b8;text-decoration:none;font-size:.85rem">Services</a></div></div></footer>'
        '<script>(function(){var wid=document.querySelector("[data-wid]");var id=wid?wid.dataset.wid:"";if(!id){var m=location.pathname.match(/preview\/([^/]+)/);if(m)id=m[1];}if(!id)return;fetch("/api/analytics/track",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({website_id:id,event_type:"page_view",page:location.pathname,referrer:document.referrer})}).catch(function(){});document.querySelectorAll("a[href^=\'tel:\']").forEach(function(a){a.addEventListener("click",function(){fetch("/api/analytics/track",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({website_id:id,event_type:"call_click"})}).catch(function(){});});});document.querySelectorAll("a[href*=\'wa.me\']").forEach(function(a){a.addEventListener("click",function(){fetch("/api/analytics/track",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({website_id:id,event_type:"whatsapp_click"})}).catch(function(){});});});var form=document.querySelector("form");if(form)form.addEventListener("submit",function(){fetch("/api/analytics/track",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({website_id:id,event_type:"lead_form"})}).catch(function(){});});})()</script>'
        f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"LocalBusiness","name":"{business_name}","telephone":"{phone}","email":"{email}","address":{{"@type":"PostalAddress","streetAddress":"{address}"}},"aggregateRating":{{"@type":"AggregateRating","ratingValue":"{lead.get("rating", 4.5) if lead else 4.5}","reviewCount":"{lead.get("review_count", 50) if lead else 50}"}}}}</script>'
        '<script src="https://unpkg.com/aos@2.3.4/dist/aos.js"></script>'
        '<script>document.body.insertAdjacentHTML("beforeend","<div class=lightbox id=lb onclick=this.classList.remove(String.fromCharCode(111,112,101,110))><button class=close onclick=document.getElementById(String.fromCharCode(108,98)).classList.remove(String.fromCharCode(111,112,101,110))>&times;</button><img id=lbImg></div>");function openLb(s){document.getElementById("lbImg").src=s;document.getElementById("lb").classList.add("open")};AOS.init({duration:650,once:true,offset:60});const nav=document.getElementById("mainNav");window.addEventListener("scroll",()=>{nav.classList.toggle("solid",scrollY>60)});if("serviceWorker"in navigator){navigator.serviceWorker.register("data:text/javascript,self.addEventListener(\'fetch\',e=>e.respondWith(fetch(e.request)))").catch(()=>{});}let deferredPrompt;window.addEventListener("beforeinstallprompt",e=>{e.preventDefault();deferredPrompt=e;const b=document.createElement("div");b.innerHTML=\'<div style="position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#fff;color:#333;padding:12px 20px;border-radius:50px;box-shadow:0 4px 20px rgba(0,0,0,.15);font-size:.85rem;font-weight:600;z-index:9999;cursor:pointer;display:flex;align-items:center;gap:8px" onclick="this.remove()">\\u2b07\\ufe0f Install App<\\/div>\';document.body.appendChild(b.firstChild);setTimeout(()=>{const el=document.querySelector("[onclick]");if(el)el.addEventListener("click",()=>{deferredPrompt.prompt();})},100)});</script>'
        f'{bottom_nav}'
        '</body></html>'
    )
    return html



def _generate_slug(business_name: str) -> str:
    """Generate a URL-friendly slug from business name."""
    slug = business_name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug[:60] if slug else 'business'


@router.get("/by-slug/{slug}", response_class=HTMLResponse)
def preview_by_slug(slug: str, lang: str = ""):
    """Preview a website by its slug (for city-maps.online/slug)."""
    from app.core.config import get_settings
    from supabase import create_client
    settings = get_settings()
    sb = create_client(settings.supabase_url, settings.supabase_service_key)

    result = sb.table("websites").select("*").eq("slug", slug).limit(1).execute()
    if not result.data:
        raise HTTPException(404, "Website not found")

    website = result.data[0]
    content_data = website.get("content", {})
    if not content_data:
        raise HTTPException(404, "No content generated")

    lead_service = LeadService()
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    # Apply translation if requested
    if lang and lang != "en":
        try:
            from app.core.supabase import get_supabase
            _db = get_supabase()
            cached = _db.table("translations").select("translated_content").eq("website_id", website["id"]).eq("language", lang).limit(1).execute()
            if cached.data and cached.data[0].get("translated_content"):
                content_data = cached.data[0]["translated_content"]
        except Exception:
            pass
    html = generate_html(content_data, website.get("template", "store"), lead)
    return HTMLResponse(content=html)


@router.get("/{website_id}", response_class=HTMLResponse)
def preview_website(website_id: str):
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")
    content = website.get("content", {})
    if not content:
        raise HTTPException(404, "No content generated")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    html = generate_html(content, website.get("template", "store"), lead, website_id_override=website_id)
    if not website.get("preview_url"):
        from app.core.config import get_settings
        settings = get_settings()
        preview_url = f"{settings.backend_url}/api/preview/{website_id}"
        service.update_status(website_id, website["status"], preview_url=preview_url)
    return HTMLResponse(content=html)