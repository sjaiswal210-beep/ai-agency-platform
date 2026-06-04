from __future__ import annotations
from fastapi import APIRouter
from app.automation.scheduler import scheduler, lead_processing_pipeline, followup_automation

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/status")
def get_status():
    """Get automation scheduler status."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return {
        "running": scheduler.running,
        "jobs": jobs,
    }


@router.post("/trigger/pipeline")
async def trigger_pipeline():
    """Manually trigger the lead processing pipeline now."""
    await lead_processing_pipeline()
    return {"status": "completed", "pipeline": "lead_processing"}


@router.post("/trigger/followup")
async def trigger_followup():
    """Manually trigger the follow-up automation now."""
    await followup_automation()
    return {"status": "completed", "pipeline": "followup"}
