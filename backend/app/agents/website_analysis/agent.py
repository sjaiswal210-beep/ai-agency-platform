import json
try:
    from crewai import Agent, Task, Crew
except ImportError:
    Agent = Task = Crew = None
from app.core.llm import chat_completion
from app.services.lead_service import LeadService
from app.schemas.leads import LeadUpdate
from app.core.logging import get_logger
from app.services.usage_tracker import track_usage

logger = get_logger(__name__)


def create_analysis_agent() -> Agent:
    """Create the website analysis AI agent."""
    return Agent(
        role="Website Analysis Expert",
        goal="Analyze business websites and identify improvement opportunities",
        backstory="""You are a web development expert who can quickly assess website quality,
        identify missing features, and score business opportunity for website redesign services.""",
        verbose=True,
        allow_delegation=False,
    )


async def analyze_website(lead_id: str) -> dict:
    """Analyze a lead's website and generate opportunity score."""
    logger.info("Analyzing website", lead_id=lead_id)

    service = LeadService()
    lead = service.get(lead_id)

    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    website_url = lead.get("website")

    prompt = f"""Analyze this business for website improvement opportunity:
Business: {lead['business_name']}
Category: {lead.get('category', 'unknown')}
Website: {website_url or 'NO WEBSITE'}
Rating: {lead.get('rating', 'unknown')}
Reviews: {lead.get('review_count', 0)}

Evaluate and score from 0-100 how much this business would benefit from a new/improved website.
Consider:
- No website = 90+
- Outdated design = 70-90
- Decent but improvable = 40-70
- Already good = 0-40

Also check for:
- Mobile responsiveness
- Missing CTA buttons
- Missing SEO meta tags
- No online booking system
- No WhatsApp integration
- No contact forms
- Slow performance indicators

Return JSON:
{{
    "score": <number 0-100>,
    "mobile_friendly": <boolean>,
    "has_cta": <boolean>,
    "has_seo": <boolean>,
    "has_contact_form": <boolean>,
    "has_whatsapp": <boolean>,
    "issues": ["issue1", "issue2", ...],
    "recommendation": "<brief recommendation text>"
}}"""

    result = await chat_completion([{"role": "user", "content": prompt}])

    # Parse result and update lead
    try:
        data = json.loads(result)
        score = data.get("score", 50)
    except json.JSONDecodeError:
        score = 90 if not website_url else 60
        data = {"score": score, "issues": ["Could not fully analyze"], "recommendation": result}

    service.update(
        lead_id,
        LeadUpdate(
            status="analyzed",
            opportunity_score=score,
            notes=json.dumps(data) if isinstance(data, dict) else result,
        ),
    )

    track_usage("gemini_analysis", 1)
    logger.info("Analysis complete", lead_id=lead_id, score=score)
    return {"lead_id": lead_id, "score": score, "analysis": data}
