from __future__ import annotations
import json
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
    """Daily business dashboard - AI-powered content & growth toolkit for business owners."""
    service = WebsiteService()
    lead_service = LeadService()
    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    category = lead.get("category", "business") if lead else "business"
    phone = lead.get("phone", "") if lead else ""
    slug = website.get("slug", "")

    today = datetime.now().strftime("%A, %B %d")
    hour = datetime.now().hour
    time_greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"

    # Generate daily content using AI
    daily_prompt = f"""Generate daily business content pack for:
Business: {business_name}
Category: {category}
Date: {today}

Return JSON with ALL these fields:
{{
    "greeting": "Short motivational greeting (1 line)",
    "tip_of_day": "One actionable tip specific to {category} business (2 sentences max)",
    "daily_goal": "One specific measurable goal for today",
    "social_post_1": "Instagram/Facebook promotional post caption with emojis (about a service/product)",
    "social_post_2": "Educational/tip post for social media with emojis",
    "social_post_3": "Behind-the-scenes or customer appreciation post with emojis",
    "story_idea": "Instagram/WhatsApp story idea (1 sentence, what to show)",
    "reel_idea": "Short video/reel concept (trending format, 1-2 sentences)",
    "whatsapp_morning": "Good morning broadcast to customers (warm, short, includes business value)",
    "whatsapp_offer": "Special offer message with urgency (under 50 words)",
    "whatsapp_followup": "Follow-up for recent visitors (friendly, under 40 words)",
    "whatsapp_review_ask": "Ask happy customer for Google review (polite, easy)",
    "google_post": "Google Business Profile post (offer or announcement, under 80 words)",
    "fun_fact": "Interesting industry fact about {category}",
    "hashtags": ["8 relevant hashtags without # symbol"],
    "content_idea": "Creative photo/video idea to shoot today",
    "engagement_question": "Question to post that gets customer comments"
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
    except Exception as e:
        logger.error(f"Daily AI error: {e}")
        data = {
            "greeting": f"Let's make today count, {business_name}!",
            "tip_of_day": "Ask every happy customer for a Google review today. Businesses with 50+ reviews get 3x more clicks.",
            "daily_goal": "Get 2 new Google reviews today",
            "social_post_1": f"Another great day at {business_name}! We love serving our community. Visit us today! #local",
            "social_post_2": f"Did you know? Here's a quick tip from our experts at {business_name}...",
            "social_post_3": f"Meet our amazing team at {business_name}! We're here to serve you better every day.",
            "story_idea": "Show your workspace setup for the day",
            "reel_idea": "Quick before/after transformation of your work",
            "whatsapp_morning": f"Good morning! {business_name} wishes you a wonderful day. Visit us for something special today!",
            "whatsapp_offer": f"Special today only at {business_name}! Get 10% off. Limited time. Visit now!",
            "whatsapp_followup": "Hi! Hope you enjoyed your last visit. We'd love to see you again soon!",
            "whatsapp_review_ask": "Hi! We loved serving you. Could you share a quick Google review? It helps us a lot!",
            "google_post": f"Visit {business_name} today for great service and value. We're open and ready to serve you!",
            "fun_fact": f"Businesses that post daily on social media grow 2x faster than those that don't.",
            "hashtags": [category, "localbusiness", "smallbusiness", "growthmindset", "business", "trending", "viral", "support"],
            "content_idea": "Take a photo of your best product/service and share a customer testimonial",
            "engagement_question": "What's the one thing you love most about our service? Tell us below!"
        }

    # Extract all content
    greeting = data.get("greeting", "Welcome back!")
    tip = data.get("tip_of_day", "")
    daily_goal = data.get("daily_goal", "")
    social_1 = data.get("social_post_1", "")
    social_2 = data.get("social_post_2", "")
    social_3 = data.get("social_post_3", "")
    story_idea = data.get("story_idea", "")
    reel_idea = data.get("reel_idea", "")
    wa_morning = data.get("whatsapp_morning", "")
    wa_offer = data.get("whatsapp_offer", "")
    wa_followup = data.get("whatsapp_followup", "")
    wa_review = data.get("whatsapp_review_ask", "")
    google_post = data.get("google_post", "")
    fun_fact = data.get("fun_fact", "")
    content_idea = data.get("content_idea", "")
    engagement_q = data.get("engagement_question", "")
    hashtags = data.get("hashtags", [])
    hashtags_display = " ".join([f"#{h}" if not h.startswith("#") else h for h in hashtags[:8]])

    # Clean phone for WhatsApp link
    wa_phone = phone.replace("-", "").replace(" ", "").replace("+", "")
    if wa_phone and not wa_phone.startswith("91") and len(wa_phone) == 10:
        wa_phone = "91" + wa_phone

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{business_name} - Daily Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{ --primary: #6366f1; --primary-light: #e0e7ff; --green: #10b981; --orange: #f59e0b; --red: #ef4444; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: Inter, -apple-system, sans-serif; background: #f1f5f9; color: #1e293b; min-height: 100vh; padding-bottom: 80px; }}

/* Header */
.header {{ background: #fff; border-bottom: 1px solid #e2e8f0; padding: 12px 16px; position: sticky; top: 0; z-index: 50; }}
.header-inner {{ max-width: 800px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; }}
.header h1 {{ font-size: .95rem; font-weight: 700; }}
.header .date {{ font-size: .7rem; color: #64748b; }}
.header .links {{ display: flex; gap: 8px; }}
.header .links a {{ font-size: .7rem; color: var(--primary); text-decoration: none; padding: 4px 8px; border: 1px solid #e2e8f0; border-radius: 6px; }}

/* Main */
.main {{ max-width: 800px; margin: 0 auto; padding: 16px; }}

/* Greeting */
.greeting {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; border-radius: 14px; padding: 18px 20px; margin-bottom: 16px; }}
.greeting .time {{ font-size: .7rem; opacity: .8; }}
.greeting .msg {{ font-size: .95rem; font-weight: 600; margin-top: 4px; }}
.greeting .goal {{ margin-top: 10px; background: rgba(255,255,255,.15); border-radius: 8px; padding: 10px 12px; }}
.greeting .goal-label {{ font-size: .6rem; text-transform: uppercase; letter-spacing: 1px; opacity: .8; }}
.greeting .goal-text {{ font-size: .85rem; font-weight: 600; margin-top: 2px; }}

/* Tabs */
.tabs {{ display: flex; gap: 4px; background: #fff; border-radius: 10px; padding: 4px; margin-bottom: 16px; border: 1px solid #e2e8f0; overflow-x: auto; }}
.tab {{ padding: 8px 14px; border-radius: 8px; font-size: .75rem; font-weight: 600; cursor: pointer; white-space: nowrap; color: #64748b; transition: all .2s; }}
.tab.active {{ background: var(--primary); color: #fff; }}

/* Section */
.section {{ display: none; }}
.section.active {{ display: block; }}

/* Cards */
.card {{ background: #fff; border: 1px solid #f1f5f9; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }}
.card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }}
.card-label {{ font-size: .65rem; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 600; }}
.card-actions {{ display: flex; gap: 6px; }}
.btn-copy {{ background: #f1f5f9; border: none; padding: 4px 10px; border-radius: 6px; font-size: .65rem; color: var(--primary); cursor: pointer; font-weight: 600; }}
.btn-copy:active {{ background: #e2e8f0; }}
.btn-send {{ background: #25D366; color: #fff; border: none; padding: 4px 10px; border-radius: 6px; font-size: .65rem; cursor: pointer; font-weight: 600; text-decoration: none; }}
.card-text {{ font-size: .8rem; color: #374151; line-height: 1.6; }}

/* Tags */
.tags {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }}
.tags span {{ background: #eff6ff; color: #3b82f6; padding: 2px 8px; border-radius: 10px; font-size: .6rem; font-weight: 500; }}

/* Grid */
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
@media(max-width:600px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

/* Tip */
.tip-card {{ background: linear-gradient(135deg, #fef3c7, #fde68a); border: 1px solid #fbbf24; border-radius: 12px; padding: 14px 16px; margin-bottom: 16px; }}
.tip-card .label {{ font-size: .65rem; color: #92400e; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
.tip-card .text {{ font-size: .8rem; color: #78350f; margin-top: 4px; line-height: 1.5; }}

/* Ad */
.ad {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; text-align: center; margin: 16px 0; }}
.ad .label {{ font-size: .55rem; color: #cbd5e1; text-transform: uppercase; letter-spacing: 1px; }}
.ad .text {{ font-size: .8rem; color: #475569; margin-top: 4px; }}
.ad a {{ color: var(--primary); font-weight: 600; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <div>
      <h1>{business_name}</h1>
      <span class="date">{today}</span>
    </div>
    <div class="links">
      <a href="/api/panel/{website_id}" target="_blank">&#9881; Panel</a>
      <a href="/api/preview/{website_id}" target="_blank">&#127760; Website</a>
    </div>
  </div>
</div>

<div class="main">
  <!-- Greeting + Goal -->
  <div class="greeting">
    <div class="time">{time_greeting}</div>
    <div class="msg">{greeting}</div>
    <div class="goal">
      <div class="goal-label">&#127919; Today's Goal</div>
      <div class="goal-text">{daily_goal}</div>
    </div>
  </div>

  <!-- Tabs Navigation -->
  <div class="tabs">
    <div class="tab active" onclick="showTab('whatsapp')">&#128172; WhatsApp</div>
    <div class="tab" onclick="showTab('social')">&#128247; Social Media</div>
    <div class="tab" onclick="showTab('content')">&#127916; Content</div>
    <div class="tab" onclick="showTab('growth')">&#128161; Growth</div>
  </div>

  <!-- WhatsApp Section -->
  <div class="section active" id="sec-whatsapp">
    <div class="card">
      <div class="card-header">
        <span class="card-label">&#9728;&#65039; Morning Broadcast</span>
        <div class="card-actions">
          <button class="btn-copy" onclick="copyText('wa1',this)">Copy</button>
          <a class="btn-send" href="https://wa.me/?text=" onclick="this.href='https://wa.me/?text='+encodeURIComponent(document.getElementById('wa1').textContent)" target="_blank">Send</a>
        </div>
      </div>
      <div class="card-text" id="wa1">{wa_morning}</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label">&#128293; Special Offer</span>
        <div class="card-actions">
          <button class="btn-copy" onclick="copyText('wa2',this)">Copy</button>
          <a class="btn-send" href="https://wa.me/?text=" onclick="this.href='https://wa.me/?text='+encodeURIComponent(document.getElementById('wa2').textContent)" target="_blank">Send</a>
        </div>
      </div>
      <div class="card-text" id="wa2">{wa_offer}</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label">&#128075; Follow-Up</span>
        <div class="card-actions">
          <button class="btn-copy" onclick="copyText('wa3',this)">Copy</button>
          <a class="btn-send" href="https://wa.me/?text=" onclick="this.href='https://wa.me/?text='+encodeURIComponent(document.getElementById('wa3').textContent)" target="_blank">Send</a>
        </div>
      </div>
      <div class="card-text" id="wa3">{wa_followup}</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label">&#11088; Ask for Review</span>
        <div class="card-actions">
          <button class="btn-copy" onclick="copyText('wa4',this)">Copy</button>
          <a class="btn-send" href="https://wa.me/?text=" onclick="this.href='https://wa.me/?text='+encodeURIComponent(document.getElementById('wa4').textContent)" target="_blank">Send</a>
        </div>
      </div>
      <div class="card-text" id="wa4">{wa_review}</div>
    </div>
  </div>

  <!-- Social Media Section -->
  <div class="section" id="sec-social">
    <div class="card">
      <div class="card-header">
        <span class="card-label">&#128226; Promotional Post</span>
        <button class="btn-copy" onclick="copyText('s1',this)">Copy</button>
      </div>
      <div class="card-text" id="s1">{social_1}</div>
      <div class="tags">{''.join([f'<span>#{h}</span>' if not h.startswith('#') else f'<span>{h}</span>' for h in hashtags[:4]])}</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label">&#128218; Educational Post</span>
        <button class="btn-copy" onclick="copyText('s2',this)">Copy</button>
      </div>
      <div class="card-text" id="s2">{social_2}</div>
      <div class="tags">{''.join([f'<span>#{h}</span>' if not h.startswith('#') else f'<span>{h}</span>' for h in hashtags[4:8]])}</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label">&#128248; Team / Behind the Scenes</span>
        <button class="btn-copy" onclick="copyText('s3',this)">Copy</button>
      </div>
      <div class="card-text" id="s3">{social_3}</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label">&#127759; Google Business Post</span>
        <button class="btn-copy" onclick="copyText('gp',this)">Copy</button>
      </div>
      <div class="card-text" id="gp">{google_post}</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label">&#128172; Engagement Question</span>
        <button class="btn-copy" onclick="copyText('eq',this)">Copy</button>
      </div>
      <div class="card-text" id="eq">{engagement_q}</div>
    </div>

    <!-- All hashtags -->
    <div class="card">
      <div class="card-header">
        <span class="card-label"># Hashtags</span>
        <button class="btn-copy" onclick="copyText('htags',this)">Copy All</button>
      </div>
      <div class="card-text" id="htags">{hashtags_display}</div>
    </div>
  </div>

  <!-- Content Ideas Section -->
  <div class="section" id="sec-content">
    <div class="card">
      <div class="card-header"><span class="card-label">&#128248; Story Idea</span></div>
      <div class="card-text">{story_idea}</div>
    </div>

    <div class="card">
      <div class="card-header"><span class="card-label">&#127909; Reel / Video Idea</span></div>
      <div class="card-text">{reel_idea}</div>
    </div>

    <div class="card">
      <div class="card-header"><span class="card-label">&#128247; What to Shoot Today</span></div>
      <div class="card-text">{content_idea}</div>
    </div>
  </div>

  <!-- Growth Section -->
  <div class="section" id="sec-growth">
    <div class="tip-card">
      <div class="label">&#128161; Tip of the Day</div>
      <div class="text">{tip}</div>
    </div>

    <div class="card">
      <div class="card-header"><span class="card-label">&#129300; Did You Know?</span></div>
      <div class="card-text">{fun_fact}</div>
    </div>

    <div class="ad">
      <div class="label">Grow Faster</div>
      <div class="text">Want more customers? <a href="/api/panel/{website_id}">Manage your business tools &rarr;</a></div>
    </div>
  </div>
</div>

<script>
function showTab(name) {{
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('sec-' + name).classList.add('active');
  event.target.classList.add('active');
}}

function copyText(id, btn) {{
  var text = document.getElementById(id).textContent;
  navigator.clipboard.writeText(text).then(function() {{
    btn.textContent = '\\u2713 Copied';
    setTimeout(function() {{ btn.textContent = 'Copy'; }}, 1500);
  }});
}}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)
