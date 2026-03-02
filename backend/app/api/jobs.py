import asyncio
import os

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models.user import User
from app.models.verification_job import VerificationJob, JobStatus
from app.schemas.job import JobResponse
from app.api.job_store import job_store

router = APIRouter(tags=["jobs"])


@router.post("/users/{user_id}/verify", response_model=JobResponse, status_code=201)
def start_verification(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create job record
    job = VerificationJob(user_id=user_id, status=JobStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Initialize in-memory state for SSE
    job_store.init_job(job.id)

    # Run pipeline in background
    from app.services.pipeline import run_verification_pipeline

    background_tasks.add_task(run_verification_pipeline, job.id, user_id)

    return job


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(VerificationJob).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: int):
    async def event_generator():
        while True:
            state = job_store.get_job(job_id)
            if state is None:
                yield {"event": "error", "data": '{"error": "Job not found"}'}
                return

            yield {"event": "progress", "data": job_store.serialize_job(job_id)}

            if state["status"] in ("completed", "failed"):
                return

            await job_store.wait_for_update(job_id, timeout=30.0)

    return EventSourceResponse(event_generator())


@router.get("/ocr-output/{job_id}")
def get_ocr_output(job_id: int, db: Session = Depends(get_db)):
    job = db.query(VerificationJob).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.result or "ocr_output_file" not in job.result:
        raise HTTPException(status_code=404, detail="OCR output not available for this job")

    filepath = job.result["ocr_output_file"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="OCR output file not found on disk")

    return FileResponse(filepath, media_type="application/json", filename=os.path.basename(filepath))
