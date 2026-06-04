from __future__ import annotations
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.core.llm import chat_completion
from app.core.logging import get_logger

router = APIRouter(prefix="/editor", tags=["editor"])
logger = get_logger(__name__)


class EditRequest(BaseModel):
    prompt: str


@router.post("/{website_id}/edit")
async def edit_website(website_id: str, req: EditRequest):
    """Edit a website based on a natural language prompt."""
    service = WebsiteService()
    website = service.get(website_id)

    if not website:
        raise HTTPException(404, "Website not found")

    current_content = website.get("content", {})

    # Handle raw_content
    if "raw_content" in current_content:
        raw = current_content["raw_content"]
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        try:
            current_content = json.loads(raw)
        except json.JSONDecodeError:
            pass

    prompt = f"""You are editing an existing website. Here is the current website content as JSON:

{json.dumps(current_content, indent=2)}

USER'S EDIT REQUEST: "{req.prompt}"

Apply the user's requested changes to the website content. Return the COMPLETE updated JSON with all fields preserved. Only modify what the user asked for. Keep everything else the same.

RULES:
- Return ONLY valid JSON (no markdown, no explanation)
- Preserve all existing fields that weren't mentioned
- If user asks to change colors, update color_scheme
- If user asks to change text, update the relevant text fields
- If user asks to add/remove sections, modify the relevant arrays
- Use emoji characters for icons (not font awesome names)
- Keep the same JSON structure"""

    result = await chat_completion([{"role": "user", "content": prompt}])

    # Parse the updated content
    cleaned = result.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        updated_content = json.loads(cleaned)
    except json.JSONDecodeError:
        raise HTTPException(400, "AI could not generate valid JSON. Try rephrasing your edit request.")

    # Update in database
    service.db.table("websites").update({"content": updated_content}).eq("id", website_id).execute()

    logger.info("Website edited", website_id=website_id, prompt=req.prompt[:50])
    return {"status": "updated", "website_id": website_id, "preview_url": f"/api/preview/{website_id}"}


@router.get("/{website_id}/content")
def get_website_content(website_id: str):
    """Get the raw JSON content of a website for editing."""
    service = WebsiteService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")
    return website.get("content", {})
