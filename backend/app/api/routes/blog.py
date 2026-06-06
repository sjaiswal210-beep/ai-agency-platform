from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.website_service import WebsiteService
from app.services.lead_service import LeadService
from app.core.supabase import get_supabase
from app.core.llm import chat_completion
from datetime import datetime

router = APIRouter(prefix="/blog", tags=["blog"])


@router.post("/{website_id}/generate")
async def generate_blog_post(website_id: str, topic: str = ""):
    """Generate an SEO-optimized blog post for a business website."""
    service = WebsiteService()
    lead_service = LeadService()
    db = get_supabase()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")

    business_name = lead.get("business_name", "Business")
    category = lead.get("category", "business")
    address = lead.get("address", "")
    city = address.split(",")[-2].strip() if "," in address else address.split()[-1] if address else "your city"

    # Generate topic if not provided
    if not topic:
        topic_prompt = f"""Suggest 1 blog post topic for a {category} business named "{business_name}" in {city}.
The topic should target a local SEO keyword that people search on Google.
Examples: "Best {category} in {city}", "How to choose a {category}", "Top tips for..."
Return ONLY the topic title, nothing else."""
        topic = await chat_completion([{"role": "user", "content": topic_prompt}])
        topic = topic.strip().strip('"')

    # Generate blog post
    prompt = f"""Write a 600-word SEO-optimized blog post for a {category} business.

Business: {business_name}
Location: {city}
Topic: {topic}

RULES:
- Start with an engaging hook (first 2 sentences must grab attention)
- Include the primary keyword in the first paragraph
- Mention {city} and {business_name} naturally 3-4 times each
- Use H2 and H3 subheadings (format as ## and ###)
- Include a numbered list or bullet points
- End with a strong CTA mentioning the business phone/WhatsApp
- Tone: helpful, expert, local, human (not robotic)
- Include FAQ section at the end (2-3 questions)
- Target "People Also Ask" queries for this topic
- Make it genuinely useful for readers in {city}

Return the blog post in Markdown format."""

    content = await chat_completion([{"role": "user", "content": prompt}])

    # Store in database
    slug_base = topic.lower()[:50].replace(" ", "-")
    import re
    slug = re.sub(r'[^a-z0-9-]', '', slug_base).strip('-')

    # Store blog post
    blog_data = {
        "website_id": website_id,
        "title": topic,
        "slug": slug,
        "content_md": content.strip(),
        "status": "published",
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        db.table("blog_posts").insert(blog_data).execute()
    except Exception:
        # Table might not exist yet - return the content anyway
        pass

    return {
        "title": topic,
        "slug": slug,
        "content": content.strip(),
        "website_id": website_id,
        "business": business_name,
        "city": city,
    }


@router.get("/{website_id}/posts")
def list_blog_posts(website_id: str):
    """List all blog posts for a website."""
    db = get_supabase()
    try:
        result = db.table("blog_posts").select("*").eq("website_id", website_id).order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        return []


@router.get("/{website_id}/post/{slug}", response_class=HTMLResponse)
def view_blog_post(website_id: str, slug: str):
    """Render a blog post as a beautiful HTML page."""
    service = WebsiteService()
    lead_service = LeadService()
    db = get_supabase()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    business_name = lead.get("business_name", "Business") if lead else "Business"
    phone = lead.get("phone", "") if lead else ""
    website_slug = website.get("slug", "")

    try:
        result = db.table("blog_posts").select("*").eq("website_id", website_id).eq("slug", slug).limit(1).execute()
        if not result.data:
            raise HTTPException(404, "Post not found")
        post = result.data[0]
    except Exception:
        raise HTTPException(404, "Post not found")

    title = post.get("title", "Blog Post")
    content_md = post.get("content_md", "")

    # Simple markdown to HTML conversion
    import re
    html_content = content_md
    html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^\* (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^- (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
    html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)
    # Wrap loose text in paragraphs
    lines = html_content.split('\n')
    processed = []
    for line in lines:
        line = line.strip()
        if not line:
            processed.append('')
        elif line.startswith('<h') or line.startswith('<li'):
            processed.append(line)
        else:
            processed.append(f'<p>{line}</p>')
    html_content = '\n'.join(processed)
    # Wrap <li> groups in <ul>
    html_content = re.sub(r'((?:<li>.*?</li>\n?)+)', r'<ul>\1</ul>', html_content)

    site_url = f"https://city-maps.online/{website_slug}" if website_slug else ""

    page = (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>{title} | {business_name}</title>'
        f'<meta name="description" content="{title} - {business_name}">'
        '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
        '<style>'
        '*{margin:0;padding:0;box-sizing:border-box}'
        "body{font-family:'Plus Jakarta Sans',sans-serif;color:#1e293b;line-height:1.8;background:#fff}"
        '.header{background:linear-gradient(135deg,#0f172a,#1e293b);color:#fff;padding:60px 24px;text-align:center}'
        '.header h1{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:800;max-width:700px;margin:0 auto 12px}'
        '.header p{color:#94a3b8;font-size:.9rem}'
        '.header a{color:#a78bfa;text-decoration:none}'
        '.content{max-width:720px;margin:0 auto;padding:48px 24px}'
        '.content h2{font-size:1.5rem;font-weight:800;margin:32px 0 12px;color:#0f172a}'
        '.content h3{font-size:1.2rem;font-weight:700;margin:24px 0 8px;color:#1e293b}'
        '.content p{margin-bottom:16px;font-size:1.05rem;color:#475569}'
        '.content ul{margin:16px 0;padding-left:24px}'
        '.content li{margin-bottom:8px;color:#475569}'
        '.content strong{color:#0f172a}'
        '.cta{background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff;padding:24px;border-radius:16px;text-align:center;margin:40px 0}'
        '.cta h3{font-size:1.1rem;margin-bottom:8px}'
        '.cta a{color:#fff;text-decoration:underline}'
        '.footer{text-align:center;padding:24px;font-size:.8rem;color:#94a3b8;border-top:1px solid #e2e8f0}'
        '</style></head><body>'
        f'<div class="header"><h1>{title}</h1><p>By <a href="{site_url}">{business_name}</a></p></div>'
        f'<article class="content">{html_content}'
        f'<div class="cta"><h3>Ready to get started?</h3><p>Contact {business_name} today!</p>'
        f'<p><a href="tel:{phone}">Call Now</a> | <a href="{site_url}">Visit Website</a></p></div>'
        '</article>'
        f'<div class="footer">\u00a9 {business_name} | Powered by <a href="https://city-maps.online" style="color:#a78bfa">City Maps</a></div>'
        '</body></html>'
    )
    return HTMLResponse(content=page)


@router.post("/{website_id}/generate-batch")
async def generate_batch(website_id: str, count: int = 3):
    """Generate multiple blog posts for a website."""
    service = WebsiteService()
    lead_service = LeadService()

    website = service.get(website_id)
    if not website:
        raise HTTPException(404, "Website not found")

    lead = lead_service.get(website["lead_id"]) if website.get("lead_id") else None
    if not lead:
        raise HTTPException(404, "Lead not found")

    business_name = lead.get("business_name", "Business")
    category = lead.get("category", "business")
    address = lead.get("address", "")
    city = address.split(",")[-2].strip() if "," in address else "your city"

    # Generate topics
    topics_prompt = f"""Suggest {count} blog post topics for a {category} business named "{business_name}" in {city}.
Each topic should target a different local SEO keyword.
Focus on "People Also Ask" queries and long-tail keywords.
Return ONLY the topics, one per line, no numbers or bullets."""

    topics_text = await chat_completion([{"role": "user", "content": topics_prompt}])
    topics = [t.strip().strip('"').strip('-').strip() for t in topics_text.strip().split('\n') if t.strip()][:count]

    results = []
    for topic in topics:
        try:
            result = await generate_blog_post(website_id, topic)
            results.append({"title": result["title"], "slug": result["slug"], "status": "generated"})
        except Exception as e:
            results.append({"title": topic, "error": str(e), "status": "failed"})

    return {"generated": len([r for r in results if r["status"] == "generated"]), "posts": results}
