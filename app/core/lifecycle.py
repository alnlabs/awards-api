from sqlalchemy.orm import Session
from app.models.cycle import Cycle, CycleStatus
from datetime import date, datetime

def auto_open_active_cycles(db: Session):
    """
    Check for ACTIVE cycles whose start_date has arrived and update status to OPEN.
    This ensures cycles automatically open when the nomination window starts.
    """
    today = date.today()
    cycles_to_open = (
        db.query(Cycle)
        .filter(Cycle.status == CycleStatus.ACTIVE)
        .filter(Cycle.start_date <= today)
        .filter(Cycle.end_date >= today)
        .all()
    )
    
    if cycles_to_open:
        for cycle in cycles_to_open:
            cycle.status = CycleStatus.OPEN
            cycle.updated_at = datetime.utcnow()
        db.commit()
        print(f"🔄 Auto-opened {len(cycles_to_open)} cycle(s) whose nomination window started.")
        return len(cycles_to_open)
    return 0

def auto_close_expired_cycles(db: Session):
    """
    Check for OPEN cycles whose end_date is in the past and update status to CLOSED.
    This ensures that the system state matches the business dates.
    """
    today = date.today()
    expired_cycles = (
        db.query(Cycle)
        .filter(Cycle.status == CycleStatus.OPEN)
        .filter(Cycle.end_date < today)
        .all()
    )
    
    if expired_cycles:
        for cycle in expired_cycles:
            cycle.status = CycleStatus.CLOSED
            cycle.updated_at = datetime.utcnow()
        db.commit()
        print(f"🔄 Auto-closed {len(expired_cycles)} expired cycle(s).")
        return len(expired_cycles)
    return 0
