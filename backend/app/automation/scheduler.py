"""
Automation Scheduler - Replaces n8n workflows
Runs background pipelines on schedule:
1. Lead Processing Pipeline (every 6 hours)
2. Follow-up Automation (every 24 hours)
"""
from __future__ import annotations
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.logging import get_logger

logger = get_logger("automation")

scheduler = AsyncIOScheduler()


async def lead_processing_pipeline():
    """
    Pipeline: Fetch new leads -> Analyze -> Generate website -> Send outreach
    Runs every 6 hours.
    """
    from app.services.lead_service import LeadService
    from app.agents.website_analysis.agent import analyze_website
    from app.agents.website_generation.agent import generate_website
    from app.agents.outreach.agent import send_outreach

    logger.info("Starting lead processing pipeline")
    service = LeadService()

    # Step 1: Get new leads
    new_leads = service.list_leads(status="new", limit=20)
    logger.info("Found new leads", count=len(new_leads))

    for lead in new_leads:
        try:
            # Step 2: Analyze
            result = await analyze_website(lead["id"])
            score = result.get("score", 0)
            logger.info("Analyzed lead", lead=lead["business_name"], score=score)

            # Step 3: If high score, generate website and send outreach
            if score >= 70:
                await generate_website(lead["id"], lead.get("category", "store"))
                logger.info("Generated website", lead=lead["business_name"])

                # Step 4: Send outreach
                channel = "email" if lead.get("email") else "whatsapp"
                await send_outreach(lead["id"], channel)
                logger.info("Sent outreach", lead=lead["business_name"], channel=channel)

        except Exception as e:
            logger.error("Pipeline error for lead", lead=lead["business_name"], error=str(e))
            continue

    logger.info("Lead processing pipeline complete", processed=len(new_leads))


async def followup_automation():
    """
    Pipeline: Check outreach leads -> Send follow-ups
    Runs every 24 hours.
    """
    from app.services.lead_service import LeadService
    from app.agents.followup.agent import check_and_followup

    logger.info("Starting follow-up automation")
    service = LeadService()

    # Get leads that have been sent outreach
    outreach_leads = service.list_leads(status="outreach_sent", limit=50)
    logger.info("Checking leads for follow-up", count=len(outreach_leads))

    followups_sent = 0
    for lead in outreach_leads:
        try:
            result = await check_and_followup(lead["id"])
            if result.get("action") in ("followup_sent", "reminder_sent"):
                followups_sent += 1
                logger.info("Follow-up sent", lead=lead["business_name"], action=result["action"])
        except Exception as e:
            logger.error("Follow-up error", lead=lead["business_name"], error=str(e))
            continue

    logger.info("Follow-up automation complete", followups_sent=followups_sent)



def cleanup_old_media():
    """Delete static video/audio files older than 7 days to free disk + reduce bloat."""
    import os, time
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static")
    cutoff = time.time() - 7 * 86400
    removed = 0
    for sub in ("videos", "audio"):
        d = os.path.join(base, sub)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            fp = os.path.join(d, fn)
            try:
                if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
                    os.remove(fp)
                    removed += 1
            except Exception:
                continue
    logger.info("Cleaned old media files", removed=removed)


def keep_alive_ping():
    """Ping self to prevent Render free tier from sleeping."""
    import httpx
    try:
        httpx.get("https://ai-agency-platform.onrender.com/health", timeout=10)
    except Exception:
        pass

def start_scheduler():
    """Start the automation scheduler."""
    # Lead Processing Pipeline - every 6 hours
    scheduler.add_job(
        lead_processing_pipeline,
        trigger=IntervalTrigger(hours=6),
        id="lead_processing_pipeline",
        name="Lead Processing Pipeline",
        replace_existing=True,
    )

    # Follow-up Automation - every 24 hours
    scheduler.add_job(
        followup_automation,
        trigger=IntervalTrigger(hours=24),
        id="followup_automation",
        name="Follow-up Automation",
        replace_existing=True,
    )

    scheduler.add_job(keep_alive_ping, "interval", minutes=10, id="keep_alive", replace_existing=True)

    # Process due scheduled follow-up calls - every 1 minute
    async def _process_due_calls_job():
        try:
            from app.modules.voice_calling.voice_blast import process_due_calls
            await process_due_calls()
        except Exception as e:
            logger.warning("scheduled calls job error", error=str(e))
    scheduler.add_job(_process_due_calls_job, "interval", minutes=1, id="process_due_calls", replace_existing=True)

    # Media cleanup - every 12 hours (removes video/audio older than 7 days)
    scheduler.add_job(cleanup_old_media, "interval", hours=12, id="cleanup_media", replace_existing=True)

    scheduler.start()
    logger.info("Automation scheduler started", jobs=["lead_processing (6h)", "followup (24h)"])


def stop_scheduler():
    """Stop the automation scheduler."""
    scheduler.shutdown()
    logger.info("Automation scheduler stopped")
