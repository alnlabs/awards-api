from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date, datetime
from datetime import date as date_type

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response
from app.models.user import User, UserRole
from app.models.cycle import Cycle, CycleStatus
from app.schemas.cycles import CycleCreate, CycleUpdate, CycleResponse

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_cycle(
    payload: CycleCreate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    if payload.end_date < payload.start_date:
        failure_response(
            message="Cycle creation failed",
            error="End date must be after start date",
            status_code=400
        )

    try:
        status_enum = CycleStatus(payload.status) if payload.status else CycleStatus.DRAFT
    except ValueError:
        failure_response(
            message="Cycle creation failed",
            error="Invalid status",
            status_code=400
        )

    # Validate award_type_id if provided
    award_type_id = None
    if payload.award_type_id:
        from app.models.award_type import AwardType
        award_type = db.get(AwardType, payload.award_type_id)
        if not award_type or not award_type.is_active:
            return failure_response(
                message="Cycle creation failed",
                error="Invalid or inactive award type",
                status_code=400
            )
        award_type_id = payload.award_type_id

    cycle = Cycle(
        name=payload.name,
        description=payload.description,
        quarter=payload.quarter,
        year=payload.year,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=status_enum,
        award_type_id=award_type_id
    )

    db.add(cycle)
    db.commit()
    db.refresh(cycle)

    return success_response(
        message="Cycle created successfully",
        data={
            "id": str(cycle.id),
            "name": cycle.name,
            "quarter": cycle.quarter,
            "year": cycle.year,
            "status": cycle.status.value,
            "award_type_id": str(cycle.award_type_id) if cycle.award_type_id else None
        }
    )


@router.get("", response_model=dict)
def list_cycles(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    query = db.query(Cycle).filter(Cycle.is_active == True)

    if status:
        try:
            status_enum = CycleStatus(status)
            query = query.filter(Cycle.status == status_enum)
        except ValueError:
            failure_response(
                message="Invalid status",
                error=f"Status must be one of: {[s.value for s in CycleStatus]}",
                status_code=400
            )

    cycles = query.order_by(Cycle.created_at.desc()).offset(skip).limit(limit).all()

    return success_response(
        message="Cycles fetched successfully",
        data=[
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "quarter": c.quarter,
                "year": c.year,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat(),
                "status": c.status.value,
                "award_type_id": str(c.award_type_id) if c.award_type_id else None,
                "created_at": c.created_at.isoformat()
            }
            for c in cycles
        ]
    )


@router.get("/{cycle_id}", response_model=dict)
def get_cycle(
    cycle_id: UUID,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    cycle = db.get(Cycle, cycle_id)

    if not cycle:
        failure_response(
            message="Cycle not found",
            error="Cycle does not exist",
            status_code=404
        )

    return success_response(
        message="Cycle fetched successfully",
        data={
            "id": str(cycle.id),
            "name": cycle.name,
            "description": cycle.description,
            "quarter": cycle.quarter,
            "year": cycle.year,
            "start_date": cycle.start_date.isoformat(),
            "end_date": cycle.end_date.isoformat(),
            "status": cycle.status.value,
            "award_type_id": str(cycle.award_type_id) if cycle.award_type_id else None,
            "is_active": cycle.is_active,
            "created_at": cycle.created_at.isoformat(),
            "updated_at": cycle.updated_at.isoformat() if cycle.updated_at else None
        }
    )


@router.patch("/{cycle_id}", response_model=dict)
def update_cycle(
    cycle_id: UUID,
    payload: CycleUpdate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    cycle = db.get(Cycle, cycle_id)

    if not cycle:
        failure_response(
            message="Cycle not found",
            error="Cycle does not exist",
            status_code=404
        )

    if payload.name is not None:
        cycle.name = payload.name
    if payload.description is not None:
        cycle.description = payload.description
    if payload.start_date is not None:
        cycle.start_date = payload.start_date
    if payload.end_date is not None:
        cycle.end_date = payload.end_date
        if cycle.end_date < cycle.start_date:
            failure_response(
                message="Update failed",
                error="End date must be after start date",
                status_code=400
            )
    if payload.status is not None:
        try:
            new_status = CycleStatus(payload.status)
            
            # Check if closing cycle before end_date
            if new_status == CycleStatus.CLOSED and cycle.status != CycleStatus.CLOSED:
                from datetime import date as date_type
                today = date_type.today()
                
                if today < cycle.end_date:
                    # Early closure - require explicit confirmation
                    # drop_cycle=False (or None) means "End Cycle" (normal closure, keep data)
                    # drop_cycle=True means "Drop Cycle" (clear all nominations and awards)
                    
                    # If drop_cycle is explicitly True, clear all nominations and awards
                    if payload.drop_cycle is True:
                        from app.models.nomination import Nomination
                        from app.models.award import Award
                        from app.models.form_answer import FormAnswer
                        from app.models.panel_assignment import PanelAssignment
                        from app.models.panel_review import PanelReview
                        
                        # Delete all awards for this cycle
                        db.query(Award).filter(Award.cycle_id == cycle_id).delete()
                        
                        # Get all nominations for this cycle
                        nominations = db.query(Nomination).filter(
                            Nomination.cycle_id == cycle_id
                        ).all()
                        
                        nomination_ids = [n.id for n in nominations]
                        
                        if nomination_ids:
                            # Delete panel reviews (cascade should handle this, but being explicit)
                            db.query(PanelReview).filter(
                                PanelReview.panel_assignment_id.in_(
                                    db.query(PanelAssignment.id).filter(
                                        PanelAssignment.nomination_id.in_(nomination_ids)
                                    )
                                )
                            ).delete(synchronize_session=False)
                            
                            # Delete panel assignments
                            db.query(PanelAssignment).filter(
                                PanelAssignment.nomination_id.in_(nomination_ids)
                            ).delete(synchronize_session=False)
                            
                            # Delete form answers (cascade should handle this)
                            db.query(FormAnswer).filter(
                                FormAnswer.nomination_id.in_(nomination_ids)
                            ).delete(synchronize_session=False)
                            
                            # Delete nominations
                            db.query(Nomination).filter(
                                Nomination.cycle_id == cycle_id
                            ).delete()
                        
                        # Commit deletions before updating cycle status
                        db.flush()
            
            cycle.status = new_status
        except ValueError:
            return failure_response(
                message="Update failed",
                error="Invalid status",
                status_code=400
            )
    
    if payload.award_type_id is not None:
        if payload.award_type_id:
            from app.models.award_type import AwardType
            award_type = db.get(AwardType, payload.award_type_id)
            if not award_type or not award_type.is_active:
                return failure_response(
                    message="Update failed",
                    error="Invalid or inactive award type",
                    status_code=400
                )
            cycle.award_type_id = payload.award_type_id
        else:
            cycle.award_type_id = None

    cycle.updated_at = datetime.utcnow()
    db.commit()

    return success_response(
        message="Cycle updated successfully",
        data={
            "id": str(cycle.id),
            "name": cycle.name,
            "status": cycle.status.value,
            "award_type_id": str(cycle.award_type_id) if cycle.award_type_id else None,
            "updated_at": cycle.updated_at.isoformat()
        }
    )
