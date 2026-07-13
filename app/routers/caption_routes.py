import logging
from datetime import datetime
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
from app.services.caption_engine import generate_captions

logger = logging.getLogger("caption_routes")
router = APIRouter(prefix="/api/captions", tags=["captions"])


# Base directory where uploaded files are stored (absolute, works in Docker and locally)
_UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))


def _run_captioning(job_id: str, video_url: str, db_factory):
    # Resolve relative URL path if it is an uploaded file
    video_path = video_url
    if video_url.startswith("/uploads/"):
        # Prevent path traversal by extracting only the basename
        filename = os.path.basename(video_url.lstrip("/"))
        video_path = os.path.join(_UPLOADS_DIR, filename)

    db: Session = db_factory()
    job = db.query(models.CaptionJob).filter(models.CaptionJob.id == job_id).first()
    if not job:
        db.close()
        return

    # Check if user cancelled it before processing started
    if job.status == "cancelled":
        db.close()
        return

    job.status = "processing"
    db.commit()
    db.close()

    try:
        # Check cancellation before generation
        db = db_factory()
        job = db.query(models.CaptionJob).filter(models.CaptionJob.id == job_id).first()
        if not job or job.status == "cancelled":
            db.close()
            return
        db.close()

        captions = generate_captions(video_path)

        # Check cancellation after generation (before saving)
        db = db_factory()
        job = db.query(models.CaptionJob).filter(models.CaptionJob.id == job_id).first()
        if not job or job.status == "cancelled":
            db.close()
            return

        for style, text in captions.items():
            db.add(models.Caption(job_id=job.id, style=style, text=text))
        job.status = "done"
        job.completed_at = datetime.utcnow()
        db.commit()
        db.close()
    except Exception as exc:
        db = db_factory()
        job = db.query(models.CaptionJob).filter(models.CaptionJob.id == job_id).first()
        if job and job.status != "cancelled":
            job.status = "failed"
            job.error = str(exc)[:500]
            db.commit()
        db.close()
        logger.exception("Captioning failed for job %s", job_id)


@router.post("", response_model=schemas.JobOut, status_code=202)
def submit_video(
    payload: schemas.CaptionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.video_url.startswith("/uploads/"):
        raise HTTPException(status_code=400, detail="Cannot manually submit internal upload URLs")

    job = models.CaptionJob(owner_id=current_user.id, video_url=payload.video_url, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.database import SessionLocal
    background_tasks.add_task(_run_captioning, job.id, payload.video_url, SessionLocal)

    return _to_job_out(job)


@router.post("/upload", response_model=schemas.JobOut, status_code=202)
def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a video")

    # Create uploads directory on the fly
    os.makedirs("uploads", exist_ok=True)

    # Save the uploaded file
    file_id = uuid.uuid4().hex
    file_ext = os.path.splitext(file.filename)[1] or ".mp4"
    file_path = f"uploads/{file_id}{file_ext}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(exc)}")

    # We store the /uploads/ path in the database
    video_url = f"/uploads/{file_id}{file_ext}"
    job = models.CaptionJob(
        owner_id=current_user.id,
        video_url=video_url,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.database import SessionLocal
    background_tasks.add_task(_run_captioning, job.id, video_url, SessionLocal)

    return _to_job_out(job)


@router.post("/{job_id}/cancel", response_model=schemas.JobOut)
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = (
        db.query(models.CaptionJob)
        .filter(models.CaptionJob.id == job_id, models.CaptionJob.owner_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ["done", "failed"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job in '{job.status}' status")

    job.status = "cancelled"
    db.commit()
    db.refresh(job)
    return _to_job_out(job)


@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = (
        db.query(models.CaptionJob)
        .filter(models.CaptionJob.id == job_id, models.CaptionJob.owner_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # If it is a local uploaded file, delete it from disk
    if job.video_url and job.video_url.startswith("/uploads/"):
        filename = os.path.basename(job.video_url.lstrip("/"))
        local_path = os.path.join(_UPLOADS_DIR, filename)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception as exc:
                logger.error("Could not remove local file %s: %s", local_path, exc)

    db.delete(job)
    db.commit()
    return {"detail": "Job deleted"}


@router.get("", response_model=list[schemas.JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    jobs = (
        db.query(models.CaptionJob)
        .filter(models.CaptionJob.owner_id == current_user.id)
        .order_by(models.CaptionJob.created_at.desc())
        .all()
    )
    return [_to_job_out(j) for j in jobs]


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = (
        db.query(models.CaptionJob)
        .filter(models.CaptionJob.id == job_id, models.CaptionJob.owner_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _to_job_out(job)


def _to_job_out(job: models.CaptionJob) -> schemas.JobOut:
    captions = {c.style: c.text for c in job.captions} if job.captions else None
    return schemas.JobOut(
        id=job.id,
        video_url=job.video_url,
        status=job.status,
        error=job.error,
        created_at=job.created_at,
        completed_at=job.completed_at,
        captions=captions,
    )
