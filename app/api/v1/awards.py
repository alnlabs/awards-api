from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from sqlalchemy import func, case

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response
from app.models.user import User, UserRole
from app.models.award import Award
from app.models.nomination import Nomination
from app.models.cycle import Cycle, CycleStatus
from app.models.panel_review import PanelReview
from app.schemas.awards import AwardCreate, AwardResponse

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_award(
    payload: AwardCreate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    # Verify cycle exists
    cycle = db.get(Cycle, payload.cycle_id)
    if not cycle:
        failure_response(
            message="Award creation failed",
            error="Cycle not found",
            status_code=404
        )

    # Verify nomination exists and belongs to cycle
    nomination = db.get(Nomination, payload.nomination_id)
    if not nomination:
        failure_response(
            message="Award creation failed",
            error="Nomination not found",
            status_code=404
        )

    if nomination.cycle_id != payload.cycle_id:
        failure_response(
            message="Award creation failed",
            error="Nomination does not belong to this cycle",
            status_code=400
        )

    if nomination.status != "FINALIZED":
        failure_response(
            message="Award creation failed",
            error="Nomination must be FINALIZED before creating an award",
            status_code=400
        )

    # Verify winner exists
    winner = db.get(User, payload.winner_id)
    if not winner or not winner.is_active:
        failure_response(
            message="Award creation failed",
            error="Winner not found or inactive",
            status_code=404
        )

    if nomination.nominee_id != payload.winner_id:
        failure_response(
            message="Award creation failed",
            error="Winner ID must match the nominee ID",
            status_code=400
        )

    # Check for existing award for this nomination
    existing = db.query(Award).filter(
        Award.nomination_id == payload.nomination_id,
        Award.is_active == True
    ).first()

    if existing:
        failure_response(
            message="Award creation failed",
            error="An award already exists for this nomination",
            status_code=400
        )

    award = Award(
        cycle_id=payload.cycle_id,
        nomination_id=payload.nomination_id,
        winner_id=payload.winner_id,
        award_type=payload.award_type,
        rank=payload.rank
    )

    db.add(award)
    db.commit()
    db.refresh(award)

    return success_response(
        message="Award created successfully",
        data={
            "id": str(award.id),
            "cycle_id": str(award.cycle_id),
            "winner_id": str(award.winner_id),
            "award_type": award.award_type,
            "rank": award.rank
        }
    )


@router.post("/cycle/{cycle_id}/finalize", response_model=dict)
def finalize_awards(
    cycle_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    # Verify cycle exists
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        failure_response(
            message="Finalization failed",
            error="Cycle not found",
            status_code=404
        )

    # Get finalized nominations for this cycle
    nominations = db.query(Nomination).filter(
        Nomination.cycle_id == cycle_id,
        Nomination.status == "FINALIZED"
    ).all()

    if not nominations:
        failure_response(
            message="Finalization failed",
            error="No finalized nominations found for this cycle",
            status_code=400
        )

    # Mark all awards as finalized
    awards = db.query(Award).filter(
        Award.cycle_id == cycle_id,
        Award.is_active == True
    ).all()

    finalized_at = datetime.utcnow()
    for award in awards:
        award.finalized_at = finalized_at

    # Update cycle status
    cycle.status = CycleStatus.FINALIZED

    db.commit()

    return success_response(
        message="Awards finalized successfully",
        data={
            "cycle_id": str(cycle_id),
            "awards_count": len(awards),
            "finalized_at": finalized_at.isoformat()
        }
    )


@router.get("/history", response_model=dict)
def awards_history(
    skip: int = 0,
    limit: int = 100,
    cycle_id: UUID = None,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    query = db.query(Award).filter(
        Award.is_active == True,
        Award.finalized_at.isnot(None)
    )

    if cycle_id:
        query = query.filter(Award.cycle_id == cycle_id)

    awards = query.order_by(Award.finalized_at.desc()).offset(skip).limit(limit).all()

    # Load related data
    result_data = []
    for award in awards:
        cycle = db.get(Cycle, award.cycle_id)
        winner = db.get(User, award.winner_id)

        result_data.append({
            "id": str(award.id),
            "cycle_id": str(award.cycle_id),
            "cycle_name": cycle.name if cycle else None,
            "nomination_id": str(award.nomination_id),
            "winner_id": str(award.winner_id),
            "winner_name": winner.name if winner else None,
            "winner_email": winner.email if winner else None,
            "award_type": award.award_type,
            "rank": award.rank,
            "finalized_at": award.finalized_at.isoformat() if award.finalized_at else None,
            "created_at": award.created_at.isoformat()
        })

    return success_response(
        message="Awards history fetched successfully",
        data=result_data
    )


@router.get("/current", response_model=dict)
def current_awards(
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    # Get current finalized cycle
    current_cycle = db.query(Cycle).filter(
        Cycle.status == CycleStatus.FINALIZED,
        Cycle.is_active == True
    ).order_by(Cycle.created_at.desc()).first()

    if not current_cycle:
        return success_response(
            message="No current awards found",
            data=[]
        )

    # Get awards for current cycle
    awards_query = db.query(Award).filter(
        Award.cycle_id == current_cycle.id,
        Award.is_active == True
    )
    awards = awards_query.order_by(
        case((Award.rank.isnot(None), Award.rank), else_=999).asc(),
        Award.created_at.desc()
    ).all()

    # Load related data
    result_data = []
    for award in awards:
        winner = db.get(User, award.winner_id)

        result_data.append({
            "id": str(award.id),
            "cycle_id": str(award.cycle_id),
            "cycle_name": current_cycle.name,
            "cycle_quarter": current_cycle.quarter,
            "cycle_year": current_cycle.year,
            "nomination_id": str(award.nomination_id),
            "winner_id": str(award.winner_id),
            "winner_name": winner.name if winner else None,
            "winner_email": winner.email if winner else None,
            "award_type": award.award_type,
            "rank": award.rank,
            "finalized_at": award.finalized_at.isoformat() if award.finalized_at else None
        })

    return success_response(
        message="Current awards fetched successfully",
        data=result_data
    )


@router.get("/{award_id}", response_model=dict)
def get_award(
    award_id: UUID,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    award = db.get(Award, award_id)

    if not award or not award.is_active:
        failure_response(
            message="Award not found",
            error="Award does not exist",
            status_code=404
        )

    cycle = db.get(Cycle, award.cycle_id)
    winner = db.get(User, award.winner_id)
    nomination = db.get(Nomination, award.nomination_id)

    return success_response(
        message="Award fetched successfully",
        data={
            "id": str(award.id),
            "cycle_id": str(award.cycle_id),
            "cycle_name": cycle.name if cycle else None,
            "cycle_quarter": cycle.quarter if cycle else None,
            "cycle_year": cycle.year if cycle else None,
            "nomination_id": str(award.nomination_id),
            "winner_id": str(award.winner_id),
            "winner_name": winner.name if winner else None,
            "winner_email": winner.email if winner else None,
            "winner_employee_code": winner.employee_code if winner else None,
            "award_type": award.award_type,
            "rank": award.rank,
            "finalized_at": award.finalized_at.isoformat() if award.finalized_at else None,
            "created_at": award.created_at.isoformat()
        }
    )


@router.get("/cycle/{cycle_id}/nominations-with-scores", response_model=dict)
def get_nominations_with_scores(
    cycle_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    # Verify cycle exists
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        failure_response(
            message="Cycle not found",
            error="Cycle does not exist",
            status_code=404
        )

    # Get nominations with average scores
    nominations = db.query(Nomination).filter(
        Nomination.cycle_id == cycle_id,
        Nomination.status.in_(["HR_REVIEW", "PANEL_REVIEW", "FINALIZED"])
    ).all()

    result_data = []
    for nomination in nominations:
        # Get average score
        avg_score_result = db.query(func.avg(PanelReview.score)).filter(
            PanelReview.nomination_id == nomination.id
        ).scalar()

        # Get review count
        review_count = db.query(PanelReview).filter(
            PanelReview.nomination_id == nomination.id
        ).count()

        nominee = db.get(User, nomination.nominee_id)
        nominated_by = db.get(User, nomination.nominated_by_id)

        result_data.append({
            "nomination_id": str(nomination.id),
            "nominee_id": str(nomination.nominee_id),
            "nominee_name": nominee.name if nominee else None,
            "nominee_email": nominee.email if nominee else None,
            "nominated_by_id": str(nomination.nominated_by_id),
            "nominated_by_name": nominated_by.name if nominated_by else None,
            "status": nomination.status,
            "average_score": float(avg_score_result) if avg_score_result else None,
            "review_count": review_count,
            "submitted_at": nomination.submitted_at.isoformat() if nomination.submitted_at else None
        })

    # Sort by average score descending
    result_data.sort(key=lambda x: x["average_score"] if x["average_score"] else 0, reverse=True)

    return success_response(
        message="Nominations with scores fetched successfully",
        data=result_data
    )