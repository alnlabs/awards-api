from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date, datetime

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

    cycle = Cycle(
        name=payload.name,
        description=payload.description,
        quarter=payload.quarter,
        year=payload.year,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=status_enum
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
            "status": cycle.status.value
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
            cycle.status = CycleStatus(payload.status)
        except ValueError:
            failure_response(
                message="Update failed",
                error="Invalid status",
                status_code=400
            )

    cycle.updated_at = datetime.utcnow()
    db.commit()

    return success_response(
        message="Cycle updated successfully",
        data={
            "id": str(cycle.id),
            "name": cycle.name,
            "status": cycle.status.value,
            "updated_at": cycle.updated_at.isoformat()
        }
    )
