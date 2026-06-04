import asyncio
from app.workers.celery_app import celery_app
from app.agents.lead_discovery.agent import run_discovery
from app.agents.website_analysis.agent import analyze_website
from app.agents.website_generation.agent import generate_website
from app.agents.outreach.agent import send_outreach
from app.agents.followup.agent import check_and_followup
from app.agents.deployment.agent import deploy_website


@celery_app.task(name="tasks.discover_leads", bind=True, max_retries=3)
def task_discover_leads(self, location: str, category: str):
    """Background task: discover leads for a location."""
    try:
        return asyncio.run(run_discovery(location, category))
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.analyze_lead", bind=True, max_retries=3)
def task_analyze_lead(self, lead_id: str):
    """Background task: analyze a lead website."""
    try:
        return asyncio.run(analyze_website(lead_id))
    except Exception as exc:
        self.retry(exc=exc, countdown=30)


@celery_app.task(name="tasks.generate_website", bind=True, max_retries=3)
def task_generate_website(self, lead_id: str, template: str = "store"):
    """Background task: generate website for a lead."""
    try:
        return asyncio.run(generate_website(lead_id, template))
    except Exception as exc:
        self.retry(exc=exc, countdown=30)


@celery_app.task(name="tasks.send_outreach", bind=True, max_retries=3)
def task_send_outreach(self, lead_id: str, channel: str = "email"):
    """Background task: send outreach to a lead."""
    try:
        return asyncio.run(send_outreach(lead_id, channel))
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.followup", bind=True, max_retries=2)
def task_followup(self, lead_id: str):
    """Background task: check and send follow-up."""
    try:
        return asyncio.run(check_and_followup(lead_id))
    except Exception as exc:
        self.retry(exc=exc, countdown=120)


@celery_app.task(name="tasks.deploy_website", bind=True, max_retries=2)
def task_deploy_website(self, website_id: str):
    """Background task: deploy a website."""
    try:
        return asyncio.run(deploy_website(website_id))
    except Exception as exc:
        self.retry(exc=exc, countdown=30)
