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
            combined_url = await stitch_videos(video_urls, website_id, business_name, phone if lead else "")
        except Exception as e:
            logger.warning("Stitching failed, returning individual clips", error=str(e))

    return {
        "status": "completed",
        "total_duration": f"{len(video_urls) * 10} seconds",
        "combined_url": combined_url,
        "clips": video_urls,
        "business": business_name,
    }


async def stitch_videos(clips: list, website_id: str, business_name: str = "", phone: str = "") -> str:
    """Download clips, stitch into one video with business branding using ffmpeg."""
    import httpx as _httpx
    import subprocess
    import shutil

    temp_dir = tempfile.mkdtemp()
    clip_files = []

    # Download each clip
    async with _httpx.AsyncClient() as client:
        for i, clip in enumerate(clips):
            if not clip.get("url"):
                continue
            try:
                resp = await client.get(clip["url"], timeout=60)
                if resp.status_code == 200:
                    path = os.path.join(temp_dir, f"clip_{i}.mp4")
                    with open(path, "wb") as f:
                        f.write(resp.content)
                    clip_files.append(path)
            except Exception:
                continue

    logger.info("Stitch: downloaded clips", count=len(clip_files))
    if len(clip_files) < 1:
        logger.warning("Stitch: no clips downloaded")
        return None

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "static", "videos")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{website_id}_combined.mp4")
    concat_path = os.path.join(output_dir, f"{website_id}_concat.mp4")

    if len(clip_files) == 1:
        shutil.copy2(clip_files[0], concat_path)
    else:
        # Create concat list for ffmpeg
        list_file = os.path.join(temp_dir, "concat.txt")
        with open(list_file, "w") as f:
            for cf in clip_files:
                f.write(f"file '{cf}'\n")
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", concat_path],
                capture_output=True, text=True, timeout=120
            )
            if not os.path.exists(concat_path) or os.path.getsize(concat_path) < 1000:
                # Fallback: re-encode
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c:v", "libx264", "-preset", "fast", "-crf", "23", concat_path],
                    capture_output=True, text=True, timeout=180
                )
        except Exception as e:
            logger.warning("ffmpeg concat failed", error=str(e))
            for f in clip_files:
                try: os.remove(f)
                except: pass
            return None

    # Add text overlay with business name, phone, and branding
    brand_text = business_name or "Business"
    phone_text = phone or ""
    branding = "Powered by City-Maps.online"
    
    # Build drawtext filter
    drawtext_filters = []
    # Business name - top left
    drawtext_filters.append(f"drawtext=text='{brand_text}':fontsize=24:fontcolor=white:x=20:y=20:shadowcolor=black:shadowx=2:shadowy=2")
    # Phone - top right
    if phone_text:
        drawtext_filters.append(f"drawtext=text='{phone_text}':fontsize=18:fontcolor=white:x=w-tw-20:y=20:shadowcolor=black:shadowx=2:shadowy=2")
    # Branding - bottom center
    drawtext_filters.append(f"drawtext=text='{branding}':fontsize=16:fontcolor=white:x=(w-tw)/2:y=h-40:shadowcolor=black:shadowx=2:shadowy=2")
    
    filter_str = ",".join(drawtext_filters)
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", concat_path, "-vf", filter_str, "-c:a", "copy", "-preset", "fast", output_path],
            capture_output=True, text=True, timeout=180
        )
        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
            # If drawtext fails (font not available), just use the concat without text
            logger.warning("drawtext failed, using concat without branding")
            shutil.copy2(concat_path, output_path)
    except Exception as e:
        logger.warning("ffmpeg drawtext failed, using concat", error=str(e))
        shutil.copy2(concat_path, output_path)

    # Verify output exists
    if not os.path.exists(output_path):
        logger.warning("Stitch: output file not created", path=output_path)
        for f in clip_files:
            try: os.remove(f)
            except: pass
        return None

    logger.info("Stitch: combined video created", path=output_path, size=os.path.getsize(output_path))

    # Cleanup
    for f in clip_files:
        try: os.remove(f)
        except: pass
    try: os.remove(concat_path)
    except: pass

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







class HFVideoRequest(BaseModel):
    prompt: str = ""
    website_id: str = ""
    custom_text: str = ""



class ScriptRequest(BaseModel):
    blurb: str = ""
    business_name: str = "Business"
    category: str = "business"


@router.post("/{website_id}/generate-script")
async def generate_video_script(website_id: str, req: ScriptRequest):
    """Generate a 4-scene video script from a blurb/keywords."""
    import json as _json
    
    prompt = f"""Create a 4-scene video script for a 20-second promotional video.
Business: {req.business_name}, Category: {req.category}
Theme/Keywords: {req.blurb if req.blurb else req.category + ' business promotional'}

Each scene is 5 seconds. Write vivid, cinematic visual descriptions.
Focus on what the CAMERA sees - colors, movement, angles, people, products.

Return ONLY a JSON array of 4 scene descriptions:
["Scene 1 visual description", "Scene 2...", "Scene 3...", "Scene 4..."]"""

    try:
        result = await chat_completion([{"role": "user", "content": prompt}])
        cleaned = result.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        scenes = _json.loads(cleaned)
        return {"script": scenes[:4]}
    except Exception:
        # Fallback script
        return {"script": [
            f"Wide shot of {req.business_name} exterior, welcoming entrance, golden hour lighting",
            f"Interior of {req.business_name}, modern setup, customers browsing, warm atmosphere",
            f"Close-up of key products/services, professional quality, vibrant colors",
            f"Happy customers at {req.business_name}, smiles, satisfaction",
        ]}


@router.post("/{website_id}/generate-free")
async def generate_free_video(website_id: str, req: HFVideoRequest):
    """Generate 30-sec video (6 clips), stitch with ffmpeg, add text overlay."""
    import json as _json
    import httpx as _hx
    import subprocess
    import tempfile
    import shutil

    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")
    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    slug = website.get("slug", "")
    site_url = f"{slug}.city-maps.online" if slug else "city-maps.online"
    custom_text = req.custom_text if hasattr(req, "custom_text") and req.custom_text else ""

    # Parse scenes
    prompt_text = req.prompt or ""
    scenes = [s.strip() for s in prompt_text.split("\n") if s.strip() and len(s.strip()) > 10]
    scenes = [s.split(":", 1)[1].strip() if ":" in s and s.split(":")[0].strip().startswith("Scene") else s for s in scenes]

    if len(scenes) < 3:
        try:
            sp = f"Create 4 short scene descriptions for a {category} business video. Business: {business_name}. Return ONLY JSON array."
            raw = await chat_completion([{"role": "user", "content": sp}])
            cleaned = raw.strip()
            if "```json" in cleaned: cleaned = cleaned.split("```json")[1].split("```")[0]
            elif "```" in cleaned: cleaned = cleaned.split("```")[1].split("```")[0]
            scenes = _json.loads(cleaned.strip())[:6]
        except Exception:
            scenes = [f"{business_name} exterior", f"Interior with customers", f"Products close-up", f"Happy customers"]

    if not REPLICATE_TOKEN:
        raise HTTPException(500, "Video service not configured")

    # Generate 6 clips via Replicate
    rep_client = replicate.Client(api_token=REPLICATE_TOKEN)
    clip_urls = []
    for scene in scenes[:4]:
        try:
            output = rep_client.run("lightricks/ltx-2-distilled", input={"prompt": scene})
            url = output.url if hasattr(output, "url") else str(output[0]) if isinstance(output, list) else str(output)
            if url and url.startswith("http"):
                clip_urls.append(url)
        except Exception:
            continue

    if not clip_urls:
        return {"status": "failed", "message": "Video generation failed. Try again."}

    # Download and stitch with ffmpeg
    temp_dir = tempfile.mkdtemp()
    clip_files = []
    async with _hx.AsyncClient(timeout=60) as client:
        for i, url in enumerate(clip_urls):
            try:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.content) > 5000:
                    path = os.path.join(temp_dir, f"clip_{i}.mp4")
                    with open(path, "wb") as fout:
                        fout.write(resp.content)
                    clip_files.append(path)
            except Exception:
                continue

    if not clip_files:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {"status": "completed", "video_url": clip_urls[0], "clips": clip_urls, "total_duration": f"{len(clip_urls)*5} seconds", "business_name": business_name}

    # Stitch
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "static", "videos")
    os.makedirs(output_dir, exist_ok=True)
    concat_path = os.path.join(temp_dir, "concat.mp4")
    final_path = os.path.join(output_dir, f"{website_id}_promo.mp4")

    list_file = os.path.join(temp_dir, "list.txt")
    with open(list_file, "w") as lf:
        for cf in clip_files:
            lf.write(f"file \'{cf}\'\n")

    # Concat clips
    try:
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", concat_path], capture_output=True, timeout=120)
    except Exception:
        pass
    if not os.path.exists(concat_path) or os.path.getsize(concat_path) < 5000:
        try:
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", concat_path], capture_output=True, timeout=180)
        except Exception:
            # If ffmpeg fails completely, return first clip
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"status": "completed", "video_url": clip_urls[0], "clips": clip_urls, "total_duration": f"{len(clip_urls)*5} seconds", "business_name": business_name}

    # Add text overlay
    # Sanitize text for ffmpeg
    biz_clean = business_name.replace("'", "").replace('"', '').replace(":", " ").replace(",", " ")
    offer_clean = (custom_text or "").replace("'", "").replace('"', '').replace(":", " ").replace(",", " ")
    site_clean = site_url.replace("'", "")
    
    # Build complex filter with:
    # - Semi-transparent dark bar at top and bottom
    # - Large business name at top (always visible)
    # - Offer text animated (pulses mid-video)  
    # - Website URL at bottom
    filters = []
    # Dark gradient bars for text readability
    filters.append("drawbox=x=0:y=0:w=iw:h=60:color=black@0.5:t=fill")
    filters.append("drawbox=x=0:y=ih-45:w=iw:h=45:color=black@0.5:t=fill")
    # Business name - large, bold, top center
    filters.append(f"drawtext=text=\'{biz_clean}\':fontsize=28:fontcolor=white:x=(w-tw)/2:y=18:shadowcolor=black:shadowx=2:shadowy=2")
    # Offer/custom text - animated fade in at 2sec, stays visible
    if offer_clean:
        filters.append(f"drawtext=text=\'{offer_clean}\':fontsize=24:fontcolor=yellow:x=(w-tw)/2:y=(h-th)/2:shadowcolor=black:shadowx=3:shadowy=3:enable=\'gte(t,1.5)\'")
    # Website URL at bottom center
    filters.append(f"drawtext=text=\'{site_clean}\':fontsize=18:fontcolor=white:x=(w-tw)/2:y=h-32:shadowcolor=black:shadowx=2:shadowy=2")
    drawtext = ",".join(filters)
    try:
        subprocess.run(["ffmpeg", "-y", "-i", concat_path, "-vf", drawtext, "-c:a", "copy", "-preset", "ultrafast", final_path], capture_output=True, timeout=180)
        if not os.path.exists(final_path) or os.path.getsize(final_path) < 5000:
            shutil.copy2(concat_path, final_path)
    except Exception:
        shutil.copy2(concat_path, final_path)

    shutil.rmtree(temp_dir, ignore_errors=True)

    if os.path.exists(final_path) and os.path.getsize(final_path) > 5000:
        video_url = f"/static/videos/{website_id}_promo.mp4"
    else:
        video_url = clip_urls[0]

    return {"status": "completed", "video_url": video_url, "clips": clip_urls, "total_duration": f"{len(clip_files)*5} seconds", "business_name": business_name}

