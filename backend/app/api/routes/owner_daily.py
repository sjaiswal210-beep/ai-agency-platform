from __future__ import annotations
import json
import random
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.llm import chat_completion
from app.core.logging import get_logger

router = APIRouter(prefix="/daily", tags=["daily-dashboard"])
logger = get_logger(__name__)


@router.get("/{website_id}", response_class=HTMLResponse)
async def daily_dashboard(website_id: str):
    """Daily business dashboard - gives owners reasons to visit every day. Includes ad slots."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    phone = lead.get("phone", "") if lead else ""

    today = datetime.now().strftime("%A, %B %d")

    # Generate daily content using AI
    daily_prompt = f"""Generate daily business content pack for:
Business: {business_name}
Category: {category}
Date: {today}

Return JSON with ALL these fields:
{{
    "greeting": "Motivating good morning message (1 line)",
    "tip_of_day": "One actionable tip specific to {category} (2 sentences)",
    "daily_goal": "One specific measurable goal for today",
    "social_post_1": "Instagram/Facebook post caption with emojis (promotional, about a service)",
    "social_post_2": "Educational/tip post for social media with emojis (teach something to followers)",
    "social_post_3": "Behind-the-scenes or team appreciation post with emojis",
    "story_idea": "Instagram/WhatsApp story idea with what to show (1 sentence)",
    "reel_idea": "Short video/reel concept for today (1-2 sentences, trending format)",
    "whatsapp_morning": "Good morning message to broadcast to all customers (warm, short, includes business value)",
    "whatsapp_offer": "Special offer message to send to customers today (creates urgency, under 50 words)",
    "whatsapp_followup": "Follow-up message for customers who visited last week (friendly check-in, under 40 words)",
    "whatsapp_review_ask": "Message asking happy customer for a Google review (polite, easy, includes review link placeholder)",
    "google_post": "Google Business Profile post (announcement or offer, under 100 words)",
    "fun_fact": "Interesting industry fact about {category}",
    "hashtags": ["8 trending and relevant hashtags"],
    "content_idea": "One creative content idea they can shoot today (photo or video)",
    "engagement_question": "A question to post that gets customer comments/engagement"
}}
Return ONLY valid JSON."""

    try:
        result = await chat_completion([{"role": "user", "content": daily_prompt}])
        cleaned = result.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        data = json.loads(cleaned)
    except Exception:
        data = {
            "greeting": f"Good day, {business_name}! Ready to grow today?",
            "tip_of_day": "Focus on asking every happy customer for a Google review today. Reviews are the #1 factor for local SEO.",
            "social_post": f"Another great day at {business_name}! We love serving our community. Visit us today! #local #business",
            "customer_message": f"Hi! Hope you're doing well. We have something special for you at {business_name}. Visit us this week!",
            "fun_fact": f"Did you know? Businesses with 50+ Google reviews get 3x more clicks than those with less.",
            "daily_goal": "Get 2 new Google reviews today",
            "hashtags": [f"#{category}", "#localbusiness", "#growthmindset", "#customerfirst", "#trending"],
        }

    greeting = data.get("greeting", "Welcome back!")
    tip = data.get("tip_of_day", "")
    social_post = data.get("social_post", "")
    customer_msg = data.get("customer_message", "")
    fun_fact = data.get("fun_fact", "")
    daily_goal = data.get("daily_goal", "")
    hashtags = data.get("hashtags", [])

    # Ad slots (you can replace these with real ad network code later)
    ad_banner_top = '<div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:12px;padding:16px 20px;margin-bottom:20px;text-align:center"><a href="https://kalpdevpg.online" target="_blank" style="color:#fff;text-decoration:none;font-size:.85rem;font-weight:500">&#x2728; Upgrade to Premium - Get custom domain + advanced features | <u>Learn More</u></a></div>'

    ad_sidebar = '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;text-align:center;margin-top:16px"><p style="font-size:.7rem;color:#94a3b8;margin-bottom:8px">SPONSORED</p><div style="background:linear-gradient(135deg,#f59e0b,#ef4444);border-radius:8px;padding:20px;color:#fff"><p style="font-weight:700;font-size:.9rem">Grow Your Business 10x</p><p style="font-size:.75rem;opacity:.9;margin-top:4px">Get professional marketing tools</p><a href="#" style="display:inline-block;margin-top:8px;background:#fff;color:#f59e0b;padding:6px 14px;border-radius:6px;font-size:.75rem;font-weight:600;text-decoration:none">Try Free</a></div></div>'

    ad_bottom = '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;text-align:center;margin-top:20px"><p style="font-size:.65rem;color:#94a3b8;margin-bottom:6px">AD</p><p style="font-size:.85rem;color:#374151">Want more customers? <a href="#" style="color:#6366f1;font-weight:600">Boost your listing on Google &rarr;</a></p></div>'

    # Extract all fields
    social_1 = data.get("social_post_1", data.get("social_post", ""))
    social_2 = data.get("social_post_2", "")
    social_3 = data.get("social_post_3", "")
    story_idea = data.get("story_idea", "")
    reel_idea = data.get("reel_idea", "")
    wa_morning = data.get("whatsapp_morning", "")
    wa_offer = data.get("whatsapp_offer", data.get("customer_message", ""))
    wa_followup = data.get("whatsapp_followup", "")
    wa_review = data.get("whatsapp_review_ask", "")
    google_post = data.get("google_post", "")
    content_idea = data.get("content_idea", "")
    engagement_q = data.get("engagement_question", "")
    hashtags_str = " ".join([h if h.startswith("#") else "#"+h for h in hashtags[:8]])

    # Ad slots
    ad_top = '<div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:12px;padding:14px 20px;margin-bottom:20px;text-align:center"><a href="#" style="color:#fff;text-decoration:none;font-size:.8rem">&#x2728; Want more customers? Upgrade to Premium Plan &rarr;</a></div>'
    ad_mid = '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;text-align:center;margin:16px 0"><p style="font-size:.6rem;color:#94a3b8;margin-bottom:4px">SPONSORED</p><p style="font-size:.8rem;color:#374151">Boost your Google ranking &#x2192; <a href="#" style="color:#6366f1">Learn how</a></p></div>'
    ad_side = '<div style="background:linear-gradient(135deg,#f59e0b,#ef4444);border-radius:10px;padding:16px;color:#fff;text-align:center;margin-top:12px"><p style="font-weight:700;font-size:.85rem">Get 5x More Calls</p><p style="font-size:.7rem;opacity:.9;margin-top:4px">Professional Google Ads management</p><a href="#" style="display:inline-block;margin-top:8px;background:#fff;color:#f59e0b;padding:5px 12px;border-radius:6px;font-size:.7rem;font-weight:600;text-decoration:none">Start Free</a></div>'

    def copy_btn(target_id):
        return f'<button onclick="navigator.clipboard.writeText(document.getElementById(\'{target_id}\').textContent);this.textContent=\'Copied!\';setTimeout(()=>this.textContent=\'Copy\',1500)" style="background:#f1f5f9;border:none;padding:4px 10px;border-radius:4px;font-size:.7rem;color:#6366f1;cursor:pointer;font-weight:600">Copy</button>'

    def wa_send_btn(msg_id):
        return f'<a href="https://wa.me/?text=" onclick="this.href=\'https://wa.me/?text=\'+encodeURIComponent(document.getElementById(\'{msg_id}\').textContent)" target="_blank" style="background:#25D366;color:#fff;padding:4px 10px;border-radius:4px;font-size:.7rem;text-decoration:none;font-weight:600">Send</a>'

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{business_name} - Daily Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,sans-serif;background:#f8fafc;color:#1e293b;min-height:100vh}}
.header{{background:#fff;border-bottom:1px solid #e2e8f0;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}}
.header h1{{font-size:1rem;font-weight:700}}
.container{{max-width:1000px;margin:0 auto;padding:20px}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}}
.card{{background:#fff;border:1px solid #f1f5f9;border-radius:10px;padding:16px}}
.card-label{{font-size:.65rem;text-transform:uppercase;letter-spacing:1.5px;color:#94a3b8;margin-bottom:8px;font-weight:600;display:flex;align-items:center;justify-content:space-between}}
.card-text{{font-size:.82rem;color:#374151;line-height:1.6}}
.section-title{{font-size:.75rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin:20px 0 10px;padding-left:4px}}
.goal{{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border-radius:10px;padding:16px;margin-bottom:16px}}
.goal .label{{font-size:.65rem;text-transform:uppercase;opacity:.8;letter-spacing:1px}}
.goal .text{{font-size:.9rem;font-weight:700;margin-top:4px}}
.tags{{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}}
.tags span{{background:#eff6ff;color:#3b82f6;padding:2px 8px;border-radius:12px;font-size:.65rem}}
.links{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}}
.links a{{background:#fff;border:1px solid #e2e8f0;padding:6px 12px;border-radius:6px;font-size:.75rem;text-decoration:none;color:#475569}}
.links a:hover{{border-color:#6366f1;color:#6366f1}}
@media(max-width:768px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body>
<div class="header"><div><h1>{business_name}</h1><span style="font-size:.75rem;color:#64748b">{today}</span></div><a href="/api/preview/{website_id}" target="_blank" style="font-size:.75rem;color:#6366f1;text-decoration:none">My Website &rarr;</a></div>
<div class="container">
{ad_top}
<p style="font-size:.95rem;font-weight:600;margin-bottom:16px">{greeting}</p>
<div class="links">
<a href="/api/panel/{website_id}" target="_blank">&#128296; Tools</a>
<a href="/api/preview/{website_id}" target="_blank">&#127760; Website</a>
<a href="/api/logo-gen/{website_id}/preview" target="_blank">&#127912; Logo</a>
<a href="https://wa.me/{phone.replace('-','').replace(' ','').replace('+','')}" target="_blank">&#128172; WhatsApp</a>
</div>
<div class="goal"><div class="label">&#127919; Today's Goal</div><div class="text">{daily_goal}</div></div>

<div class="section-title">&#128172; WhatsApp Messages (Send directly)</div>
<div class="grid">
<div class="card"><div class="card-label">Good Morning Broadcast {copy_btn('wa1')} {wa_send_btn('wa1')}</div><div class="card-text" id="wa1">{wa_morning}</div></div>
<div class="card"><div class="card-label">Special Offer {copy_btn('wa2')} {wa_send_btn('wa2')}</div><div class="card-text" id="wa2">{wa_offer}</div></div>
<div class="card"><div class="card-label">Follow-up Message {copy_btn('wa3')} {wa_send_btn('wa3')}</div><div class="card-text" id="wa3">{wa_followup}</div></div>
</div>
<div class="grid" style="grid-template-columns:1fr 1fr;margin-top:12px">
<div class="card"><div class="card-label">Ask for Review {copy_btn('wa4')} {wa_send_btn('wa4')}</div><div class="card-text" id="wa4">{wa_review}</div></div>
<div class="card"><div class="card-label">Google Business Post {copy_btn('gp')}</div><div class="card-text" id="gp">{google_post}</div></div>
</div>

{ad_mid}

<div class="section-title">&#128247; Social Media Posts (Copy & Upload)</div>
<div class="grid">
<div class="card"><div class="card-label">Promotional Post {copy_btn('s1')}</div><div class="card-text" id="s1">{social_1}</div><div class="tags">{''.join([f'<span>{h if h.startswith("#") else "#"+h}</span>' for h in hashtags[:4]])}</div></div>
<div class="card"><div class="card-label">Educational Post {copy_btn('s2')}</div><div class="card-text" id="s2">{social_2}</div><div class="tags">{''.join([f'<span>{h if h.startswith("#") else "#"+h}</span>' for h in hashtags[4:8]])}</div></div>
<div class="card"><div class="card-label">Team/BTS Post {copy_btn('s3')}</div><div class="card-text" id="s3">{social_3}</div></div>
</div>

<div class="section-title">&#127916; Content Ideas for Today</div>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr">
<div class="card"><div class="card-label">&#128248; Story Idea</div><div class="card-text">{story_idea}</div></div>
<div class="card"><div class="card-label">&#127909; Reel/Video Idea</div><div class="card-text">{reel_idea}</div></div>
<div class="card"><div class="card-label">&#128161; Content to Shoot</div><div class="card-text">{content_idea}</div></div>
</div>

<div class="grid" style="grid-template-columns:2fr 1fr;margin-top:12px">
<div class="card"><div class="card-label">&#128172; Engagement Question (post to get comments)</div><div class="card-text" id="eq">{engagement_q}</div><button onclick="navigator.clipboard.writeText(document.getElementById('eq').textContent)" style="background:#f1f5f9;border:none;padding:4px 10px;border-radius:4px;font-size:.7rem;color:#6366f1;cursor:pointer;margin-top:8px;font-weight:600">Copy</button></div>
<div class="card"><div class="card-label">&#129300; Fun Fact</div><div class="card-text">{fun_fact}</div></div>
</div>

<div class="section-title">&#128161; Daily Tip</div>
<div class="card"><div class="card-text" style="font-size:.9rem">{tip}</div></div>

{ad_mid}
</div>
</body></html>"""
    return HTMLResponse(content=html)
