# app/api/v1/system.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response
from app.models.user import User, UserRole
from app.models.system_config import SystemConfig
from app.models.nomination import Nomination
from app.models.cycle import Cycle
from app.models.bulk_job import BulkJob

router = APIRouter()

@router.get("/status")
def get_system_status(
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Get high-level status of all system features."""
    
    # 1. User Stats
    try:
        user_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
        user_stats = {}
        for role, count in user_counts:
            role_name = role.value if hasattr(role, "value") else str(role) if role else "UNKNOWN"
            user_stats[role_name] = count
    except Exception as e:
        print(f"Error querying users: {e}")
        db.rollback()
        user_stats = {}
    
    # 2. Cycle Stats
    try:
        active_cycles = db.query(Cycle).filter(Cycle.status == "ACTIVE").count()
        total_cycles = db.query(Cycle).count()
    except Exception as e:
        print(f"Error querying cycles: {e}")
        db.rollback()
        active_cycles = 0
        total_cycles = 0
    
    # 3. Nomination Stats
    try:
        total_nominations = db.query(Nomination).count()
        nomination_status_counts = db.query(Nomination.status, func.count(Nomination.id)).group_by(Nomination.status).all()
        nomination_stats = {str(s) if s else "UNKNOWN": count for s, count in nomination_status_counts}
    except Exception as e:
        print(f"Error querying nominations: {e}")
        db.rollback()
        total_nominations = 0
        nomination_stats = {}
        
    # 4. Bulk Job Stats
    try:
        pending_jobs = db.query(BulkJob).filter(BulkJob.status.in_(["queued", "processing"])).count()
    except Exception as e:
        print(f"Error querying bulk jobs: {e}")
        db.rollback()
        pending_jobs = 0
    
    # 5. Setup Status
    try:
        config = db.query(SystemConfig).first()
        setup_complete = config.setup_complete if config else False
    except Exception as e:
        print(f"Error querying system config: {e}")
        db.rollback()
        setup_complete = False
    
    # 6. Database Connectivity Check
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Error querying DB status: {e}")
        db.rollback()
        db_status = "disconnected"

    return success_response(
        message="System status fetched successfully",
        data={
            "users": {
                "total": sum(user_stats.values()),
                "by_role": user_stats
            },
            "cycles": {
                "total": total_cycles,
                "active": active_cycles
            },
            "nominations": {
                "total": total_nominations,
                "by_status": nomination_stats
            },
            "bulk_jobs": {
                "pending": pending_jobs
            },
            "database": {
                "status": db_status
            },
            "setup_complete": setup_complete,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@router.get("/config")
def get_config(
    user: User = Depends(require_role(UserRole.SUPER_ADMIN, UserRole.HR)),
    db: Session = Depends(get_db)
):
    """Get the current system configuration."""
    config = db.query(SystemConfig).first()
    if not config:
        # Return defaults if not set
        return success_response(
            message="Default configuration returned",
            data={
                "company_name": "My Company",
                "company_logo": None,
                "settings": {}
            }
        )
    
    return success_response(
        message="Config fetched successfully",
        data={
            "company_name": config.company_name,
            "company_logo": config.company_logo,
            "setup_complete": config.setup_complete,
            "settings": config.settings
        }
    )

@router.patch("/config")
def update_config(
    payload: dict,
    user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Update system configuration (SUPER_ADMIN only)."""
    config = db.query(SystemConfig).first()
    if not config:
        config = SystemConfig()
        db.add(config)
    
    if "company_name" in payload:
        config.company_name = payload["company_name"]
    if "company_logo" in payload:
        config.company_logo = payload["company_logo"]
    if "setup_complete" in payload:
        config.setup_complete = payload["setup_complete"]
    if "settings" in payload:
        # Merge settings or replace? Let's merge for flexibility
        if isinstance(payload["settings"], dict):
            current_settings = config.settings or {}
            current_settings.update(payload["settings"])
            config.settings = current_settings
    
    db.commit()
    db.refresh(config)
    
    return success_response(
        message="Config updated successfully",
        data={
            "company_name": config.company_name,
            "company_logo": config.company_logo,
            "setup_complete": config.setup_complete,
            "settings": config.settings
        }
    )
