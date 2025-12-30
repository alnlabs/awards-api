from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import failure_response, success_response
from app.models.bulk_job import BulkJob
from app.models.user import User, UserRole

router = APIRouter()

# =========================================================
# LIST BULK JOBS
# GET /bulk-jobs
# =========================================================
@router.get("")
def list_bulk_jobs(
    hr: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(BulkJob)
        .order_by(BulkJob.created_at.desc())
        .all()
    )

    return success_response(
        "Jobs fetched",
        [
            {
                "id": str(j.id),
                "type": j.type,
                "status": j.status,
                "total": j.total,
                "processed": j.processed,
                "success_count": j.success_count,
                "failure_count": j.failure_count,
                "error_file": j.error_file,
                "created_at": j.created_at,
            }
            for j in jobs
        ],
    )


# =========================================================
# GET SINGLE BULK JOB
# GET /bulk-jobs/{job_id}
# =========================================================
@router.get("/{job_id}")
def get_bulk_job(
    job_id: str,
    hr: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    job = db.get(BulkJob, job_id)

    if not job:
        return failure_response("Job not found", "", 404)

    progress = (
        int((job.processed / job.total) * 100)
        if job.total > 0
        else 0
    )

    return success_response(
        "Job fetched",
        {
            "id": str(job.id),
            "type": job.type,
            "status": job.status,
            "total": job.total,
            "processed": job.processed,
            "progress": progress,
            "success_count": job.success_count,
            "failure_count": job.failure_count,
            "error_file": job.error_file,
            "created_at": job.created_at,
        },
    )

# =========================================================
# CANCEL BULK JOB
# POST /bulk-jobs/{job_id}/cancel
# =========================================================
@router.post("/{job_id}/cancel")
def cancel_bulk_job(
    job_id: str,
    hr: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    job = db.get(BulkJob, job_id)

    if not job:
        return failure_response("Job not found", "", 404)

    if job.status in ("completed", "failed", "cancelled"):
        return failure_response(
            "Cannot cancel job",
            f"Job already {job.status}",
            400,
        )

    job.status = "cancelled"
    job.cancelled_at = datetime.now(timezone.utc)

    db.commit()

    return success_response(
        "Job cancelled",
        {
            "job_id": str(job.id),
            "status": job.status,
        },
    )