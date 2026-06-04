from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
import json
import urllib.parse
import asyncio

def _get_real_photos(business_name: str, address: str) -> list:
    """Sync wrapper to get real Google Maps photos."""
    try:
        from app.services.photos_service import get_business_photos
        loop = asyncio.new_event_loop()
        photos = loop.run_until_complete(get_business_photos(business_name, address, max_photos=6))
        loop.close()
        return photos
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


def get_maps_embed(address: str) -> str:
    if not address:
        return ""
    encoded = urllib.parse.quote(address)
    return f"https://www.google.com/maps?q={encoded}&output=embed"


def generate_html(content: dict, template: str, lead: dict = None) -> str:
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

    category = (lead.get("category", "") if lead else "") or template
    logo_url = content.get("logo_url", "") if isinstance(content, dict) else ""

    # Try to get real photos from Google Maps
    real_photos = []
    if lead:
        real_photos = _get_real_photos(lead.get("business_name", ""), lead.get("address", ""))
    images = get_images_for_category(category)
    hero_img = images["hero"]
    about_img = images["about"]
    gallery = images["gallery"]

    phone = contact.get("phone", lead.get("phone", "") if lead else "")
    email = contact.get("email", lead.get("email", "") if lead else "")
    address = contact.get("address", lead.get("address", "") if lead else "")
    hours = contact.get("hours", "Mon-Sat: 9 AM - 8 PM")
    business_name = lead.get("business_name", hero_title) if lead else hero_title
    whatsapp_num = phone.replace("-", "").replace(" ", "").replace("+", "") if phone else ""
    maps_url = get_maps_embed(address)

    svc_cards = []
    for i, svc in enumerate(services):
        img = gallery[i % len(gallery)]
        svc_cards.append(
            '<div class="service-card">'
            f'<div class="service-img" style="background-image:url({img})"></div>'
            f'<div class="service-content"><h3>{svc.get("name","")}</h3>'
            f'<p>{svc.get("description","")}</p></div></div>'
        )
    services_html = "".join(svc_cards)

    test_cards = []
    for t in testimonials:
        stars = "&#9733;" * t.get("rating", 5)
        test_cards.append(
            '<div class="testimonial-card">'
            f'<div class="testimonial-avatar">{t.get("name","A")[0]}</div>'
            f'<div class="stars">{stars}</div>'
            f'<blockquote>{t.get("text","")}</blockquote>'
            f'<cite>{t.get("name","")}</cite></div>'
        )
    testimonials_html = "".join(test_cards)

    # Use real Google Maps photos if available, otherwise fallback to stock
    gallery_images = real_photos if real_photos else gallery
    gal_items = []
    for img_url in gallery_images:
        gal_items.append(f'<div class="gallery-item"><img src="{img_url}" alt="Gallery" loading="lazy"></div>')
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
            '<div class="feature-item">'
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
        benefits_html = f'<section class="section"><div class="section-header"><h2>Benefits</h2></div><div class="benefits-grid">{ben_items}</div></section>'

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
    if whatsapp_num:
        wa_msg = f"Hi {business_name}, I visited your website and I'm interested in your services. Can we discuss?"
        import urllib.parse as _up
        wa_encoded = _up.quote(wa_msg)
        wa_link = f'<a href="https://wa.me/{whatsapp_num}?text={wa_encoded}" target="_blank" class="whatsapp-float"><svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492l4.625-1.476A11.929 11.929 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75c-2.115 0-4.09-.57-5.793-1.564l-.415-.248-2.74.875.876-2.672-.27-.43A9.71 9.71 0 012.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75z"/></svg></a>'

    css = f"""<style>
:root{{--primary:{primary};--secondary:{secondary}}}
*{{margin:0;padding:0;box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{font-family:Inter,sans-serif;color:#1e293b;line-height:1.7;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}}
.nav{{position:fixed;top:0;left:0;right:0;z-index:1000;background:rgba(255,255,255,.95);backdrop-filter:blur(20px);border-bottom:1px solid rgba(0,0,0,.05);padding:16px 40px;display:flex;justify-content:space-between;align-items:center}}
.nav-brand{{font-family:Playfair Display,serif;font-weight:800;font-size:1.4rem;color:var(--primary);display:flex;align-items:center}}
.nav-links{{display:flex;gap:32px}}.nav-links a{{text-decoration:none;color:#64748b;font-weight:500;font-size:.9rem}}.nav-links a:hover{{color:var(--primary)}}
.nav-cta{{background:linear-gradient(135deg,var(--primary),#000);color:#fff;padding:10px 20px;border-radius:50px;text-decoration:none;font-weight:600;font-size:.8rem;transition:all .3s;box-shadow:0 4px 15px rgba(0,0,0,.2);display:flex;align-items:center;gap:6px}}.nav-cta:hover{{transform:translateY(-2px);box-shadow:0 6px 25px rgba(0,0,0,.3)}}
.hero{{min-height:85vh;display:flex;align-items:center;position:relative;overflow:hidden}}
.hero-bg{{position:absolute;inset:0;background:url('{real_photos[0] if real_photos else hero_img}') center/cover no-repeat}}
.hero-overlay{{position:absolute;inset:0;background:linear-gradient(135deg,rgba(0,0,0,.7) 0%,rgba(0,0,0,.3) 50%,rgba(0,0,0,.5) 100%)}}.hero-bg{{filter:brightness(1.05) contrast(1.1) saturate(1.2);animation:slowZoom 20s ease-in-out infinite alternate}}@keyframes slowZoom{{0%{{transform:scale(1)}}100%{{transform:scale(1.05)}}}}
.hero-content{{position:relative;z-index:1;max-width:700px;padding:120px 60px;color:#fff}}
.hero h1{{font-family:Playfair Display,serif;font-size:clamp(2.8rem,5vw,4.5rem);font-weight:900;margin-bottom:20px;line-height:1.1;text-shadow:0 2px 20px rgba(0,0,0,.3)}}
.hero p{{font-size:1.2rem;opacity:.9;margin-bottom:36px}}
.btn{{display:inline-flex;padding:16px 32px;border-radius:12px;text-decoration:none;font-weight:700;font-size:1rem;transition:all .3s;letter-spacing:.5px}}
.btn-white{{background:#fff;color:var(--primary);box-shadow:0 4px 20px rgba(0,0,0,.3);font-size:1.05rem;padding:18px 36px}}.btn-white:hover{{transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,0,0,.4)}}.btn-glass{{background:rgba(255,255,255,.2);color:#fff;border:2px solid rgba(255,255,255,.5);backdrop-filter:blur(4px);padding:16px 32px;font-size:1rem}}.btn-glass:hover{{background:rgba(255,255,255,.35);border-color:#fff}}.hero-badge{{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);padding:8px 16px;border-radius:50px;font-size:.85rem;margin-bottom:24px;backdrop-filter:blur(4px)}}
.section{{padding:60px 24px;max-width:1100px;margin:0 auto}}
.section-header{{text-align:center;margin-bottom:48px}}
.section-header h2{{font-family:Playfair Display,serif;font-size:2.2rem;font-weight:800;margin-bottom:12px}}
.section-header p{{color:#64748b;font-size:1.05rem}}
.about-grid{{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center}}
.about-img img{{width:100%;height:400px;object-fit:cover;border-radius:16px;box-shadow:0 20px 40px rgba(0,0,0,.1);filter:brightness(1.05) contrast(1.08) saturate(1.15)}}
.about-text{{font-size:1.1rem;color:#64748b;line-height:1.9}}
.services-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px}}
.service-card{{background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.06);transition:all .4s cubic-bezier(.4,0,.2,1)}}
.service-card:hover{{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.12)}}.service-card::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--primary),var(--secondary));transform:scaleX(0);transition:transform .3s}}.service-card:hover::after{{transform:scaleX(1)}}.service-card{{position:relative}}
.service-img{{height:180px;background-size:cover;background-position:center;filter:brightness(1.05) contrast(1.1) saturate(1.15)}}
.service-content{{padding:24px}}.service-content h3{{font-size:1.1rem;font-weight:700;margin-bottom:8px}}.service-content p{{color:#64748b;font-size:.9rem}}
.gallery-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}}
.gallery-item{{border-radius:12px;overflow:hidden;aspect-ratio:1}}.gallery-item img{{width:100%;height:100%;object-fit:cover;transition:transform .4s;filter:brightness(1.05) contrast(1.08) saturate(1.15)}}.gallery-item:hover img{{transform:scale(1.05);filter:brightness(1.1) contrast(1.1) saturate(1.2)}}
.features-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:32px}}
.feature-item{{text-align:center;padding:28px 16px;border-radius:16px;background:#f8fafc;transition:all .3s}}.feature-item:hover{{background:#fff;box-shadow:0 8px 24px rgba(0,0,0,.06)}}
.feature-icon{{font-size:2.5rem;margin-bottom:12px}}.feature-item h3{{font-size:1rem;font-weight:700;margin-bottom:6px}}.feature-item p{{color:#64748b;font-size:.9rem}}
.testimonials-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}}
.testimonial-card{{background:#fff;border-radius:16px;padding:32px;box-shadow:0 4px 16px rgba(0,0,0,.05)}}
.testimonial-avatar{{width:44px;height:44px;border-radius:50%;background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;margin-bottom:12px}}
.stars{{color:#f59e0b;font-size:1.1rem;margin-bottom:10px}}.testimonial-card blockquote{{color:#64748b;font-style:italic;margin-bottom:12px;font-size:.95rem}}.testimonial-card cite{{font-weight:600;font-style:normal;font-size:.9rem}}
.contact-section{{background:#111827;color:#fff;padding:60px 24px}}
.contact-container{{max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center}}
.contact-left h2{{font-size:1.5rem;margin-bottom:16px}}
.contact-subtitle{{color:#9ca3af;font-size:.9rem;margin-bottom:0}}
.contact-cards{{display:flex;flex-direction:column;gap:12px}}
.contact-card{{display:flex;align-items:center;gap:12px;text-decoration:none;color:#fff;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.06)}}
.contact-card:last-child{{border:none}}
.contact-card-icon{{font-size:1.2rem;width:32px}}
.contact-card-label{{display:none}}
.contact-card-value{{font-size:.9rem;color:#d1d5db}}
.contact-right{{text-align:center}}
.contact-cta-box{{background:var(--primary);border-radius:12px;padding:28px}}
.contact-cta-box h3{{font-size:1.1rem;margin-bottom:6px}}
.contact-cta-box p{{opacity:.8;margin-bottom:16px;font-size:.85rem}}
.contact-cta-btn{{display:inline-block;background:#fff;color:var(--primary);padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.9rem}}
.whatsapp-float{{position:fixed;bottom:24px;right:24px;z-index:999;background:#25D366;color:#fff;width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;text-decoration:none;box-shadow:0 4px 16px rgba(37,211,102,.4);transition:all .3s;animation:pulse-wa 2s infinite}}.whatsapp-float:hover{{transform:scale(1.1);box-shadow:0 6px 24px rgba(37,211,102,.6)}}@keyframes pulse-wa{{0%,100%{{box-shadow:0 4px 16px rgba(37,211,102,.4)}}50%{{box-shadow:0 4px 24px rgba(37,211,102,.7)}}}}
.stats-section{{background:var(--primary);padding:40px 24px;position:relative;overflow:hidden}}.stats-section::before{{content:'';position:absolute;top:-50%;right:-20%;width:60%;height:200%;background:radial-gradient(circle,rgba(255,255,255,.1),transparent);border-radius:50%}}.stats-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;max-width:800px;margin:0 auto;text-align:center}}.stat-item{{color:#fff}}.stat-number{{font-size:1.8rem;font-weight:800}}.stat-label{{font-size:.75rem;opacity:.7;margin-top:2px}}.footer{{background:#030712;color:#6b7280;padding:24px;text-align:center;font-size:.8rem}}
.footer-inner{{max-width:900px;margin:0 auto;display:flex;align-items:center;justify-content:space-between}}
.footer-brand{{font-weight:600;font-size:.85rem;color:#9ca3af;display:flex;align-items:center}}
.footer-links{{display:flex;gap:16px}}.footer-links a{{color:#6b7280;text-decoration:none;font-size:.8rem}}.footer-links a:hover{{color:#fff}}
.footer-copy{{font-size:.75rem;color:#4b5563}}
.hiw-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px;counter-reset:step}}
.hiw-item{{text-align:center;padding:24px 16px}}
.hiw-number{{width:40px;height:40px;border-radius:50%;background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;margin:0 auto 12px;font-size:1.1rem}}
.hiw-item h3{{font-size:1rem;font-weight:700;margin-bottom:6px}}.hiw-item p{{color:#64748b;font-size:.85rem}}
.benefits-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}}
.benefit-item{{padding:12px 16px;background:#f0fdf4;border-radius:8px;font-size:.9rem;color:#166534;font-weight:500}}
.why-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px}}
.why-item{{text-align:center;padding:24px 16px}}.why-icon{{font-size:2rem;margin-bottom:8px}}.why-item h3{{font-size:1rem;font-weight:700;margin-bottom:4px}}.why-item p{{color:#64748b;font-size:.85rem}}
.faq-list{{max-width:800px;margin:0 auto}}
.faq-item{{border-bottom:1px solid #e5e7eb;padding:16px 0}}
.faq-item summary{{font-weight:600;cursor:pointer;font-size:.95rem;padding:4px 0}}
.faq-item p{{color:#64748b;font-size:.9rem;margin-top:8px;line-height:1.7}}
.hero-offer{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);display:inline-block;padding:8px 16px;border-radius:8px;font-size:.9rem;margin-bottom:20px}}

/* Premium 3D Effects */
.service-card{{perspective:1000px}}
.service-card:hover .service-img{{transform:scale(1.05)}}
.service-card:hover{{transform:translateY(-8px) rotateX(2deg);box-shadow:0 20px 60px rgba(0,0,0,.15)}}

/* Floating animation */
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
.hero-badge{{animation:float 3s ease-in-out infinite}}

/* Gradient mesh background */
@keyframes gradientMove{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}

/* 3D tilt on gallery items */
.gallery-item{{transition:all .4s cubic-bezier(.4,0,.2,1);transform-style:preserve-3d}}
.gallery-item:hover{{transform:scale(1.05) rotateY(3deg) rotateX(2deg);box-shadow:0 20px 40px rgba(0,0,0,.2);z-index:2}}

/* Testimonial card 3D */
.testimonial-card{{transition:all .4s cubic-bezier(.4,0,.2,1);transform-style:preserve-3d}}
.testimonial-card:hover{{transform:translateY(-4px) rotateX(2deg);box-shadow:0 16px 40px rgba(0,0,0,.1)}}

/* Feature items float on hover */
.feature-item{{transition:all .4s cubic-bezier(.4,0,.2,1)}}
.feature-item:hover{{transform:translateY(-6px) scale(1.02);box-shadow:0 16px 40px rgba(0,0,0,.08)}}

/* Smooth gradient border on nav */
.nav{{background:rgba(255,255,255,.92);box-shadow:0 1px 20px rgba(0,0,0,.06)}}

/* Hero parallax depth */
.hero-bg{{transition:transform .3s}}
.hero::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:120px;background:linear-gradient(to top,var(--bg,#fff),transparent);z-index:1}}

/* Glowing CTA button */
.btn-white{{position:relative;overflow:hidden}}
.btn-white::after{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle,rgba(255,255,255,.3),transparent 60%);opacity:0;transition:opacity .3s}}
.btn-white:hover::after{{opacity:1}}

/* Section divider wave */
.section::before{{content:'';display:block;height:1px;background:linear-gradient(90deg,transparent,rgba(0,0,0,.06),transparent);margin-bottom:40px}}

/* Smooth reveal on scroll (works with AOS) */
[data-aos]{{transition-timing-function:cubic-bezier(.4,0,.2,1)}}

@media(max-width:768px){{.nav-links{{display:none}}.hero-content{{padding:80px 20px}}.about-grid{{grid-template-columns:1fr}}.gallery-grid{{grid-template-columns:repeat(2,1fr)}}.stats-grid{{grid-template-columns:repeat(2,1fr)}}.stat-number{{font-size:1.8rem}}.contact-container{{grid-template-columns:1fr}}.footer-inner{{flex-direction:column;text-align:center}}.footer-links{{justify-content:center}}}}
</style>"""

    html = (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>{seo_title}</title><meta name="description" content="{seo_desc}">'
        f'<meta property="og:image" content="{hero_img}">'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@700;800;900&display=swap" rel="stylesheet">'
        f'{css}</head><body>'
        f'<nav class="nav"><div class="nav-brand"><svg width="36" height="36" viewBox="0 0 36 36" style="margin-right:8px;vertical-align:middle"><rect width="36" height="36" rx="8" fill="{primary}"/><text x="18" y="24" text-anchor="middle" fill="white" font-size="18" font-weight="bold" font-family="Playfair Display,serif">{business_name[0]}</text></svg>{business_name}</div>'
        '<div class="nav-links"><a href="#about">About</a><a href="#services">Services</a><a href="#gallery">Gallery</a><a href="#contact">Contact</a></div>'
        f'<a href="tel:{phone}" class="nav-cta">&#128222; Call</a></nav>'
        '<section class="hero"><div class="hero-bg"></div><div class="hero-overlay"></div>'
        f'<div class="hero-content"><div class="hero-badge">&#9733; Trusted by {lead.get("review_count", 100) if lead else 100}+ customers</div><h1>{hero_title}</h1><p>{hero_subtitle}</p>' + (f'<div class="hero-offer">{hero_offer}</div>' if hero_offer else '') +
        f'<div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center"><a href="#contact" class="btn btn-white">{cta_text}</a><a href="https://www.google.com/maps/dir/?api=1&destination={address.replace(" ", "+")}" target="_blank" class="btn btn-glass">&#128205; Get Directions</a></div></div></section>'
        '<section class="section" id="about"><div class="about-grid">'
        f'<div class="about-img"><img src="{real_photos[1] if len(real_photos) > 1 else about_img}" alt="About"></div>'
        '<div><div class="section-header" style="text-align:left;margin-bottom:20px"><h2>About Us</h2></div>'
        f'<p class="about-text">{about}</p></div></div></section>'
        '<section class="stats-section"><div class="stats-grid">'
        f'<div class="stat-item"><div class="stat-number">{lead.get("review_count", 100) if lead else 100}+</div><div class="stat-label">Happy Customers</div></div>'
        f'<div class="stat-item"><div class="stat-number">{lead.get("rating", 4.8) if lead else 4.8}</div><div class="stat-label">Average Rating</div></div>'
        '<div class="stat-item"><div class="stat-number">5+</div><div class="stat-label">Years Experience</div></div>'
        '<div class="stat-item"><div class="stat-number">100%</div><div class="stat-label">Satisfaction</div></div>'
        '</div></section>'
        '<section class="section" id="services"><div class="section-header"><h2>Our Services</h2></div>'
        f'<div class="services-grid">{services_html}</div></section>'
        '<section class="section" id="gallery"><div class="section-header"><h2>Gallery</h2></div>'
        f'<div class="gallery-grid">{gallery_html}</div></section>'
        '<section class="section" style="background:#f8fafc;max-width:100%"><div style="max-width:1200px;margin:0 auto;padding:80px 24px">'
        f'<div class="section-header"><h2>Our Strengths</h2></div><div class="features-grid">{features_html}</div></div></section>'
        '<section class="section"><div class="section-header"><h2>What People Say</h2></div>'
        f'<div class="testimonials-grid">{testimonials_html}</div></section>'
        f'{hiw_html}{benefits_html}{faq_html}{maps_section}'
        f'<section style="background:linear-gradient(135deg, #0f172a, #1e293b);padding:80px 24px" id="contact">'
        '<div style="max-width:1000px;margin:0 auto">'
        '<div style="text-align:center;margin-bottom:48px"><h2 style="font-family:Playfair Display,serif;font-size:2rem;font-weight:800;margin-bottom:8px;color:#fff">Get In Touch</h2><p style="color:#94a3b8;font-size:.95rem">Interested? Have questions? Reach out to us anytime.</p></div>'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:32px">'
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
        f'<footer class="footer"><div style="max-width:900px;margin:0 auto;display:flex;flex-direction:column;align-items:center;gap:16px"><div style="font-weight:700;font-size:1rem;color:#fff">{business_name}</div><div style="font-size:.8rem;color:#64748b">Made with &#10084;&#65039; by Kalpdev Digitals</div><div style="display:flex;gap:16px;margin-top:4px"><a href="https://wa.me/{whatsapp_num}" target="_blank" style="color:#25D366;text-decoration:none;font-size:.85rem">WhatsApp</a><a href="#contact" style="color:#94a3b8;text-decoration:none;font-size:.85rem">Contact</a><a href="#dashboard" target="_blank" style="color:#94a3b8;text-decoration:none;font-size:.85rem">Dashboard</a><a href="#services" style="color:#94a3b8;text-decoration:none;font-size:.85rem">Services</a></div></div></footer>'
        f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"LocalBusiness","name":"{business_name}","telephone":"{phone}","email":"{email}","address":{{"@type":"PostalAddress","streetAddress":"{address}"}},"aggregateRating":{{"@type":"AggregateRating","ratingValue":"{lead.get("rating", 4.5) if lead else 4.5}","reviewCount":"{lead.get("review_count", 50) if lead else 50}"}}}}</script>'
        '<script src="https://unpkg.com/aos@2.3.4/dist/aos.js"></script>'
        '<script>AOS.init({duration:800,once:true,offset:100});</script>'
        '</body></html>'
    )
    return html


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
    html = generate_html(content, website.get("template", "store"), lead)
    if not website.get("preview_url"):
        from app.core.config import get_settings
        settings = get_settings()
        preview_url = f"{settings.backend_url}/api/preview/{website_id}"
        service.update_status(website_id, website["status"], preview_url=preview_url)
    return HTMLResponse(content=html)

