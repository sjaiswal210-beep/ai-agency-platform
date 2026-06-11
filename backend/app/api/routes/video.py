from __future__ import annotations
import os
import os
import tempfile
try:
    import replicate
except ImportError:
    replicate = None
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
from app.core.logging import get_logger

router = APIRouter(prefix="/video", tags=["video"])
logger = get_logger(__name__)

REPLICATE_TOKEN = os.environ.get("REPLICATE_TOKEN", "")


class VideoRequest(BaseModel):
    prompt: str = ""
    duration: int = 10  # seconds (6, 8, or 10)


class MultiClipRequest(BaseModel):
    prompt: str = ""
    clips: int = 3  # number of 10-sec clips (total = clips * 10 seconds)


@router.post("/{website_id}/generate-long")
async def generate_long_video(website_id: str, req: MultiClipRequest):
    """Generate a longer video by creating multiple 10-sec clips with different scenes."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    # Generate scene-by-scene prompts from the main prompt
    scene_prompt = f"""Split this video concept into {req.clips} separate scenes (each 10 seconds).
Each scene should be a different angle/moment that flows together as one video.

Main concept: {req.prompt}
Business: {business_name} ({category})

Return ONLY a JSON array of scene descriptions. Example:
["Scene 1 description...", "Scene 2 description...", "Scene 3 description..."]"""

    scenes_raw = await chat_completion([{"role": "user", "content": scene_prompt}])
    
    import json as _json
    cleaned = scenes_raw.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
    
    try:
        scenes = _json.loads(cleaned)
    except _json.JSONDecodeError:
        scenes = [req.prompt] * req.clips

    # Generate each clip
    client = replicate.Client(api_token=REPLICATE_TOKEN)
    video_urls = []

    for i, scene in enumerate(scenes[:req.clips]):
        try:
            output = client.run(
                "lightricks/ltx-2-distilled",
                input={
                    "prompt": scene,
                    "duration": 10,
                }
            )
            if hasattr(output, "url"):
                video_urls.append({"scene": i + 1, "url": output.url, "prompt": scene})
            elif isinstance(output, list) and len(output) > 0:
                video_urls.append({"scene": i + 1, "url": str(output[0]), "prompt": scene})
            else:
                video_urls.append({"scene": i + 1, "url": str(output), "prompt": scene})
        except Exception as e:
            video_urls.append({"scene": i + 1, "url": None, "error": str(e), "prompt": scene})

    # Stitch clips together
    combined_url = None
    if len([v for v in video_urls if v.get("url")]) > 1:
        try:
            combined_url = await stitch_videos(video_urls, website_id)
        except Exception as e:
            logger.warning("Stitching failed, returning individual clips", error=str(e))

    return {
        "status": "completed",
        "total_duration": f"{len(video_urls) * 10} seconds",
        "combined_url": combined_url,
        "clips": video_urls,
        "business": business_name,
    }


async def stitch_videos(clips: list, website_id: str) -> str:
    """Download clips and stitch them into one video."""
    import httpx as _httpx
    from moviepy import VideoFileClip, concatenate_videoclips

    temp_dir = tempfile.mkdtemp()
    clip_files = []

    # Download each clip
    async with _httpx.AsyncClient() as client:
        for i, clip in enumerate(clips):
            if not clip.get("url"):
                continue
            resp = await client.get(clip["url"], timeout=60)
            if resp.status_code == 200:
                path = os.path.join(temp_dir, f"clip_{i}.mp4")
                with open(path, "wb") as f:
                    f.write(resp.content)
                clip_files.append(path)

    if len(clip_files) < 2:
        return None

    # Stitch with moviepy
    video_clips = [VideoFileClip(f) for f in clip_files]
    final = concatenate_videoclips(video_clips, method="compose")

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "static", "videos")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{website_id}_combined.mp4")
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)

    # Cleanup
    final.close()
    for vc in video_clips:
        vc.close()
    for f in clip_files:
        os.remove(f)

    from app.core.config import get_settings
    settings = get_settings()
    return f"{settings.backend_url}/static/videos/{website_id}_combined.mp4"


@router.post("/{website_id}/generate")
async def generate_video(website_id: str, req: VideoRequest):
    """Generate a promotional video for a business using LTX-Video."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    # If no prompt provided, generate one using AI
    if not req.prompt:
        prompt_gen = f"""Write a short, vivid video description for a promotional video for:
Business: {business_name}
Category: {category}

The description should be 1-2 sentences describing what the video should show.
Think: cinematic, professional, appealing to customers.
Examples:
- "A modern dental clinic with bright lighting, a dentist smiling at a patient, clean white interior, professional equipment"
- "A busy restaurant kitchen with chefs cooking, flames on a pan, beautiful plated food, warm ambient lighting"
- "A fitness gym with people working out, modern equipment, energetic atmosphere, motivational"

Return ONLY the video description, nothing else."""

        video_prompt = await chat_completion([{"role": "user", "content": prompt_gen}])
        video_prompt = video_prompt.strip().strip('"')
    else:
        video_prompt = req.prompt

    logger.info("Generating video", business=business_name, prompt=video_prompt[:50])

    # Call Replicate LTX-Video API
    try:
        client = replicate.Client(api_token=REPLICATE_TOKEN)
        output = client.run(
            "lightricks/ltx-2-distilled",
            input={
                "prompt": video_prompt,
                
            }
        )

        # Output could be a URL, FileOutput, or list
        if hasattr(output, "url"):
            video_url = output.url
        elif isinstance(output, list) and len(output) > 0:
            video_url = str(output[0])
        else:
            video_url = str(output) if output else None

        return {
            "status": "completed",
            "video_url": video_url,
            "prompt": video_prompt,
            "business": business_name,
        }

    except Exception as e:
        error_msg = str(e)
        logger.error("Video generation failed", error=error_msg)

        # If model not found, try alternative model
        if "not found" in error_msg or "does not exist" in error_msg:
            try:
                client = replicate.Client(api_token=REPLICATE_TOKEN)
                output = client.run(
                    "lightricks/ltx-2-distilled",
                    input={
                        "prompt": video_prompt,
                        
                    }
                )
                if hasattr(output, "url"):
                    video_url = output.url
                elif isinstance(output, list) and len(output) > 0:
                    video_url = str(output[0])
                else:
                    video_url = str(output) if output else None
                return {
                    "status": "completed",
                    "video_url": video_url,
                    "prompt": video_prompt,
                    "business": business_name,
                }
            except Exception as e2:
                raise HTTPException(500, f"Video generation failed: {str(e2)}")

        raise HTTPException(500, f"Video generation failed: {error_msg}")


class IdeaRequest(BaseModel):
    idea: str


@router.post("/{website_id}/detailed-prompt")
async def generate_detailed_prompt(website_id: str, req: IdeaRequest):
    """Take a brief idea and generate a detailed cinematic video prompt."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    address = lead.get("address", "") if lead else ""

    prompt = f"""You are a professional video director creating a promotional video for a business.

BUSINESS:
- Name: {business_name}
- Category: {category}
- Location: {address}

USER'S IDEA: "{req.idea}"

Create a DETAILED cinematic video prompt that a text-to-video AI model can use. Include:
1. Scene description (what we see)
2. Camera movement (pan, zoom, tracking shot, aerial, close-up)
3. Lighting (golden hour, bright, moody, natural)
4. Mood/atmosphere (energetic, calm, luxurious, warm)
5. People/action (what people are doing)
6. Colors and visual style
7. Transitions between scenes if multiple

Make it vivid, specific, and cinematic. Think like a commercial director.
The prompt should be 3-5 sentences, highly descriptive.

Example output:
"Cinematic tracking shot through a modern dental clinic, bright natural lighting streaming through floor-to-ceiling windows. A friendly dentist in a white coat smiles while explaining a procedure to a relaxed patient in a state-of-the-art chair. Close-up of gleaming dental equipment, then a wide shot of the welcoming reception area with warm wood accents and green plants. The camera slowly pulls back to reveal the clinic's modern exterior with the logo prominently displayed. Warm color grading with teal and orange tones."

Return ONLY the video prompt, nothing else."""

    result = await chat_completion([{"role": "user", "content": prompt}])
    detailed_prompt = result.strip().strip('"')

    return {
        "prompt": detailed_prompt,
        "idea": req.idea,
        "business": business_name,
    }


@router.post("/{website_id}/prompt")
async def generate_video_prompt(website_id: str):
    """Generate a video prompt suggestion for a business (without generating the video)."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"

    prompt = f"""Suggest 3 different video prompts for a promotional video for:
Business: {business_name}
Category: {category}

Each should be 1-2 sentences, cinematic and professional.
Format as a numbered list. Return ONLY the list."""

    suggestions = await chat_completion([{"role": "user", "content": prompt}])

    return {
        "business": business_name,
        "category": category,
        "suggestions": suggestions,
    }





