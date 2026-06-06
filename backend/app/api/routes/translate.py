from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.core.supabase import get_supabase
from app.core.llm import chat_completion
from app.services.website_service import WebsiteService
import json

router = APIRouter(prefix="/translate", tags=["translate"])

SUPPORTED_LANGUAGES = {
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "kn": "Kannada",
    "pa": "Punjabi",
    "ml": "Malayalam",
}


@router.post("/{website_id}")
async def translate_website(website_id: str, lang: str = "hi"):
    """Translate website content to a target language. Caches result."""
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"Unsupported language. Supported: {list(SUPPORTED_LANGUAGES.keys())}")

    db = get_supabase()
    service = WebsiteService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    content = website.get("content", {})
    if not content:
        raise HTTPException(404, "No content to translate")

    # Check if translation already cached
    try:
        cached = db.table("translations").select("*").eq("website_id", website_id).eq("language", lang).limit(1).execute()
        if cached.data:
            return {"language": lang, "language_name": SUPPORTED_LANGUAGES[lang], "content": cached.data[0].get("translated_content", {}), "cached": True}
    except Exception:
        pass

    # Fields to translate
    fields_to_translate = {
        "hero_title": content.get("hero_title", ""),
        "hero_subtitle": content.get("hero_subtitle", ""),
        "hero_offer": content.get("hero_offer", ""),
        "about": content.get("about", ""),
        "cta_text": content.get("cta_text", "Contact Us"),
    }

    # Translate services
    services = content.get("services", [])
    services_text = " | ".join([s.get("name","") + ": " + s.get("description","") for s in services])

    # Translate testimonials
    testimonials = content.get("testimonials", [])
    testimonials_text = " | ".join([t.get("text","") for t in testimonials])

    # Translate FAQ
    faq = content.get("faq", [])
    faq_text = " | ".join(["Q: " + q.get("question","") + " A: " + q.get("answer","") for q in faq])

    # Translate benefits
    benefits = content.get("benefits", [])
    benefits_text = " | ".join(benefits)

    # Translate how_it_works
    hiw = content.get("how_it_works", [])
    hiw_text = " | ".join([s.get("title","") + " - " + s.get("description","") for s in hiw])

    lang_name = SUPPORTED_LANGUAGES[lang]

    prompt = f"""Translate ALL the following business website content to {lang_name}.
Keep business name, phone numbers, and addresses in English.
Keep the translation natural and conversational (not formal/textbook).
Return a JSON object with the exact same structure.

CONTENT TO TRANSLATE:
{{
  "hero_title": "{fields_to_translate['hero_title']}",
  "hero_subtitle": "{fields_to_translate['hero_subtitle']}",
  "hero_offer": "{fields_to_translate['hero_offer']}",
  "about": "{fields_to_translate['about']}",
  "cta_text": "{fields_to_translate['cta_text']}",
  "services": [
    {services_text}
  ],
  "testimonials": [
    {testimonials_text}
  ],
  "faq": [
    {faq_text}
  ],
  "benefits": [
    {benefits_text}
  ],
  "how_it_works": [
    {hiw_text}
  ]
}}

RULES:
- Translate to {lang_name} script (Devanagari for Hindi/Marathi, etc.)
- Keep proper nouns (business names, person names, locations) in English
- Sound natural and friendly, not like Google Translate
- Return ONLY valid JSON

Return format:
{{
  "hero_title": "translated...",
  "hero_subtitle": "translated...",
  "hero_offer": "translated...",
  "about": "translated...",
  "cta_text": "translated...",
  "services": [{{"name": "...", "description": "..."}}],
  "testimonials": [{{"name": "original name", "text": "translated..."}}],
  "faq": [{{"question": "translated...", "answer": "translated..."}}],
  "benefits": ["translated..."],
  "how_it_works": [{{"step": "1", "title": "translated...", "description": "translated..."}}]
}}"""

    result = await chat_completion([{"role": "user", "content": prompt}])

    # Parse response
    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        translated = json.loads(cleaned)
    except json.JSONDecodeError:
        translated = {"raw": cleaned}

    # Merge translated fields with original content (keep colors, contact, etc.)
    merged = dict(content)
    merged.update(translated)
    # Keep original contact info, colors, seo
    merged["contact_info"] = content.get("contact_info", {})
    merged["color_scheme"] = content.get("color_scheme", {})

    # Cache translation
    try:
        db.table("translations").insert({
            "website_id": website_id,
            "language": lang,
            "translated_content": merged,
        }).execute()
    except Exception:
        pass

    return {"language": lang, "language_name": lang_name, "content": merged, "cached": False}


@router.get("/languages")
def list_languages():
    """List supported translation languages."""
    return {"languages": [{"code": k, "name": v} for k, v in SUPPORTED_LANGUAGES.items()]}
