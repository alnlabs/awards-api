import csv
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.bulk_job import BulkJob
from app.models.user import User
from app.services.user_service import create_user_internal

ERROR_DIR = "storage/bulk_errors"
os.makedirs(ERROR_DIR, exist_ok=True)


# =========================================================
# BULK UPLOAD WORKER
# =========================================================
def process_bulk_job(job_id: str):
    db: Session = SessionLocal()
    job = None

    try:
        job = db.get(BulkJob, job_id)
        if not job or job.status == "cancelled":
            return

        job.status = "processing"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        rows = job.payload.get("rows", [])
        errors = []

        for idx, row in enumerate(rows, start=1):
            # 🔴 STOP if cancelled
            db.refresh(job)
            if job.status == "cancelled":
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
                return

            try:
                create_user_internal(db, row)
                job.success_count += 1

            except Exception as e:
                db.rollback()
                job.failure_count += 1
                errors.append({
                    "row": idx,
                    "email": row.get("email"),
                    "error": str(e),
                })

            job.processed += 1
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

        # ---------- ERROR CSV ----------
        if errors:
            file_path = f"{ERROR_DIR}/{job.id}.csv"
            with open(file_path, "w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["row", "email", "error"]
                )
                writer.writeheader()
                writer.writerows(errors)

            job.error_file = file_path

        # ✅ COMPLETE only if not cancelled
        db.refresh(job)
        if job.status != "cancelled":
            job.status = "completed"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

    except Exception as e:
        if job:
            db.rollback()
            job.status = "failed"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

    finally:
        db.close()


# =========================================================
# BULK DELETE WORKER
# =========================================================
def process_bulk_delete_job(job_id: str):
    db: Session = SessionLocal()
    job = None

    try:
        job = db.get(BulkJob, job_id)
        if not job or job.status == "cancelled":
            return

        job.status = "processing"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        rows = job.payload.get("rows", [])
        errors = []

        for idx, row in enumerate(rows, start=1):
            # 🔴 STOP if cancelled
            db.refresh(job)
            if job.status == "cancelled":
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
                return

            try:
                user = (
                    db.query(User)
                    .filter(User.email == row.get("email"))
                    .first()
                )

                if not user:
                    raise ValueError("User not found")

                user.is_active = False
                job.success_count += 1

            except Exception as e:
                db.rollback()
                job.failure_count += 1
                errors.append({
                    "row": idx,
                    "email": row.get("email"),
                    "error": str(e),
                })

            job.processed += 1
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

        # ---------- ERROR CSV ----------
        if errors:
            file_path = f"{ERROR_DIR}/{job.id}.csv"
            with open(file_path, "w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["row", "email", "error"]
                )
                writer.writeheader()
                writer.writerows(errors)

            job.error_file = file_path

        db.refresh(job)
        if job.status != "cancelled":
            job.status = "completed"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

    except Exception:
        if job:
            db.rollback()
            job.status = "failed"
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

    finally:
        db.close()