from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from sqlalchemy import func

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response

from app.models.user import User, UserRole
from app.models.award import Award
from app.models.nomination import Nomination
from app.models.cycle import Cycle, CycleStatus
from app.models.panel_review import PanelReview
from app.models.panel_assignment import PanelAssignment
from app.models.award_type import AwardType

from app.schemas.awards import AwardCreate, AwardUpdate
from app.schemas.award_types import (
    AwardTypeCreate,
    AwardTypeUpdate,
    AwardTypeResponse,
)

router = APIRouter()


@router.get("/current")
def list_current_awards(
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.PANEL, UserRole.EMPLOYEE)),
    db: Session = Depends(get_db),
):
    """List all currently active awards (winners gallery)."""
    awards = (
        db.query(Award)
        .filter(Award.is_active == True)
        .order_by(Award.created_at.desc())
        .all()
    )
    
    result = []
    for a in awards:
        winner = db.get(User, a.winner_id)
        cycle = db.get(Cycle, a.cycle_id)
        
        # Determine award type label
        award_type_label = a.award_type
        if not award_type_label and cycle and cycle.award_type_id:
            at = db.get(AwardType, cycle.award_type_id)
            if at:
                award_type_label = at.label

        result.append({
            "id": str(a.id),
            "winner": {
                "id": str(winner.id),
                "name": winner.name,
                "email": winner.email,
            } if winner else None,
            "cycle": {
                "id": str(cycle.id),
                "name": cycle.name,
                "quarter": cycle.quarter,
                "year": cycle.year,
            } if cycle else None,
            "award_type": {
                "label": award_type_label or "Employee Award",
            },
            "rank": a.rank,
            "comment": a.comment,
            "created_at": a.created_at.isoformat(),
        })
        
    return success_response(
        message="Current awards fetched successfully",
        data=result
    )


# =====================================================
# AWARD TYPES (STATIC CATALOG)
# =====================================================

@router.get("/types")
def list_award_types(
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.PANEL, UserRole.EMPLOYEE)),
    db: Session = Depends(get_db),
):
    """List active award types (visible to all authenticated users)."""
    award_types = (
        db.query(AwardType)
        .filter(AwardType.is_active == True)  # noqa: E712
        .order_by(AwardType.created_at.asc())
        .all()
    )

    return success_response(
        message="Award types fetched successfully",
        data=[AwardTypeResponse.model_validate(at) for at in award_types],
    )


@router.post("/types", status_code=status.HTTP_201_CREATED)
def create_award_type(
    payload: AwardTypeCreate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    """Create a new award type (HR only)."""
    existing = (
        db.query(AwardType)
        .filter(AwardType.code == payload.code)
        .first()
    )
    if existing:
        return failure_response(
            "Award type creation failed",
            "Award type code already exists",
            400,
        )

    award_type = AwardType(
        code=payload.code,
        label=payload.label,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(award_type)
    db.commit()
    db.refresh(award_type)

    return success_response(
        message="Award type created successfully",
        data=AwardTypeResponse.model_validate(award_type),
    )


@router.put("/types/{award_type_id}")
def update_award_type(
    award_type_id: UUID,
    payload: AwardTypeUpdate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    """Update an existing award type (HR only)."""
    award_type = db.get(AwardType, award_type_id)
    if not award_type:
        return failure_response(
            "Award type update failed",
            "Award type not found",
            404,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(award_type, field, value)

    db.commit()
    db.refresh(award_type)

    return success_response(
        message="Award type updated successfully",
        data=AwardTypeResponse.model_validate(award_type),
    )


@router.delete("/types/{award_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_award_type(
    award_type_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    """Soft-delete an award type by setting is_active=False (HR only)."""
    award_type = db.get(AwardType, award_type_id)
    if not award_type:
        return failure_response(
            "Award type deletion failed",
            "Award type not found",
            404,
        )

    award_type.is_active = False
    db.commit()

    # 204 with no body
    from fastapi import Response
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{award_id}")
def get_award(
    award_id: UUID,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.PANEL, UserRole.EMPLOYEE)),
    db: Session = Depends(get_db),
):
    """Get single award details."""
    a = db.get(Award, award_id)
    if not a or not a.is_active:
        return failure_response("Not found", "Award not found", 404)
        
    winner = db.get(User, a.winner_id)
    cycle = db.get(Cycle, a.cycle_id)
    
    award_type_label = a.award_type
    if not award_type_label and cycle and cycle.award_type_id:
        at = db.get(AwardType, cycle.award_type_id)
        if at:
            award_type_label = at.label

    return success_response(
        message="Award fetched successfully",
        data={
            "id": str(a.id),
            "winner": {
                "id": str(winner.id),
                "name": winner.name,
                "email": winner.email,
            } if winner else None,
            "cycle": {
                "id": str(cycle.id),
                "name": cycle.name,
                "quarter": cycle.quarter,
                "year": cycle.year,
            } if cycle else None,
            "award_type": {
                "label": award_type_label or "Employee Award",
            },
            "rank": a.rank,
            "comment": a.comment,
            "created_at": a.created_at.isoformat(),
        }
    )


# =====================================================
# CREATE SINGLE AWARD (HR)
# =====================================================
@router.post("", status_code=status.HTTP_201_CREATED)
def create_award(
    payload: AwardCreate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    cycle = db.get(Cycle, payload.cycle_id)
    if not cycle:
        return failure_response("Award creation failed", "Cycle not found", 404)

    # Awards can only be created when the nomination window is open (OPEN)
    # or when the period has just ended (CLOSED) to allow for finalization.
    if cycle.status not in [CycleStatus.OPEN, CycleStatus.CLOSED]:
        return failure_response(
            "Award creation failed",
            f"Awards cannot be created when cycle is {cycle.status.value}",
            400,
        )

    nomination = db.get(Nomination, payload.nomination_id)
    if not nomination:
        return failure_response("Award creation failed", "Nomination not found", 404)

    if nomination.cycle_id != payload.cycle_id:
        return failure_response(
            "Award creation failed",
            "Nomination does not belong to this cycle",
            400,
        )

    # Nomination can be in various statuses during nomination window
    # But for awards, we typically want reviewed nominations
    if nomination.status not in ["SUBMITTED", "PANEL_REVIEW", "HR_REVIEW", "FINALIZED"]:
        return failure_response(
            "Award creation failed",
            "Nomination must be in a valid status (SUBMITTED, PANEL_REVIEW, HR_REVIEW, or FINALIZED)",
            400,
        )

    winner = db.get(User, payload.winner_id)
    if not winner or not winner.is_active:
        return failure_response(
            "Award creation failed",
            "Winner not found or inactive",
            404,
        )

    if nomination.nominee_id != payload.winner_id:
        return failure_response(
            "Award creation failed",
            "Winner must be the nominee",
            400,
        )

    existing = db.query(Award).filter(
        Award.nomination_id == payload.nomination_id,
        Award.is_active == True,
    ).first()

    if existing:
        return failure_response(
            "Award creation failed",
            "Award already exists for this nomination",
            400,
        )

    award = Award(
        cycle_id=payload.cycle_id,
        nomination_id=payload.nomination_id,
        winner_id=payload.winner_id,
        award_type=payload.award_type,
        rank=payload.rank,
        comment=payload.comment,
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
            "rank": award.rank,
            "comment": award.comment,
        },
    )


# =====================================================
# UPDATE AWARD (HR) - Only when winners are announced
# =====================================================
@router.put("/{award_id}")
def update_award(
    award_id: UUID,
    payload: AwardUpdate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    award = db.get(Award, award_id)
    if not award:
        return failure_response("Award update failed", "Award not found", 404)

    if not award.is_active:
        return failure_response("Award update failed", "Award is inactive", 400)

    cycle = db.get(Cycle, award.cycle_id)
    if not cycle:
        return failure_response("Award update failed", "Cycle not found", 404)

    # Awards can only be modified when winners are announced (cycle FINALIZED)
    if cycle.status != CycleStatus.FINALIZED:
        return failure_response(
            "Award update failed",
            "Awards cannot be modified until winners are announced (cycle must be FINALIZED)",
            400,
        )

    # Update award fields
    if payload.award_type is not None:
        award.award_type = payload.award_type
    if payload.rank is not None:
        award.rank = payload.rank
    if payload.comment is not None:
        award.comment = payload.comment

    award.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(award)

    return success_response(
        message="Award updated successfully",
        data={
            "id": str(award.id),
            "cycle_id": str(award.cycle_id),
            "winner_id": str(award.winner_id),
            "award_type": award.award_type,
            "rank": award.rank,
            "comment": award.comment,
        },
    )


# =====================================================
# FINALIZE ALL AWARDS FOR A CYCLE
# =====================================================
@router.post("/cycle/{cycle_id}/finalize")
def finalize_awards(
    cycle_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        return failure_response("Finalization failed", "Cycle not found", 404)

    if cycle.status == CycleStatus.FINALIZED:
        return failure_response(
            "Finalization failed",
            "Cycle already finalized",
            400,
        )

    awards = db.query(Award).filter(
        Award.cycle_id == cycle_id,
        Award.is_active == True,
    ).all()

    if not awards:
        return failure_response(
            "Finalization failed",
            "No awards found for this cycle",
            400,
        )

    finalized_at = datetime.utcnow()
    for award in awards:
        award.finalized_at = finalized_at

    cycle.status = CycleStatus.FINALIZED
    db.commit()

    return success_response(
        message="Awards finalized successfully",
        data={
            "cycle_id": str(cycle_id),
            "awards_count": len(awards),
            "finalized_at": finalized_at.isoformat(),
        },
    )


# =====================================================
# NOMINATIONS WITH SCORES (HR)
# =====================================================
@router.get("/cycle/{cycle_id}/nominations-with-scores")
def get_nominations_with_scores(
    cycle_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        return failure_response("Cycle not found", "Cycle does not exist", 404)

    nominations = db.query(Nomination).filter(
        Nomination.cycle_id == cycle_id,
        Nomination.status.in_(["PANEL_REVIEW", "HR_REVIEW", "FINALIZED"]),
    ).all()

    result = []

    for n in nominations:
        # Nominee & Nominator details
        nominee = db.get(User, n.nominee_id)
        nominated_by = db.get(User, n.nominated_by_id)

        avg_score = (
            db.query(func.avg(PanelReview.score))
            .join(
                PanelAssignment,
                PanelAssignment.id == PanelReview.panel_assignment_id,
            )
            .filter(PanelAssignment.nomination_id == n.id)
            .scalar()
        )

        review_count = (
            db.query(PanelReview)
            .join(
                PanelAssignment,
                PanelAssignment.id == PanelReview.panel_assignment_id,
            )
            .filter(PanelAssignment.nomination_id == n.id)
            .count()
        )

        result.append({
            "nomination_id": str(n.id),
            "nominee_id": str(n.nominee_id),
            "nominee_name": nominee.name if nominee else None,
            "nominee_email": nominee.email if nominee else None,
            "nominated_by_name": nominated_by.name if nominated_by else None,
            "status": n.status,
            "average_score": float(avg_score) if avg_score else None,
            "review_count": review_count,
            "submitted_at": n.submitted_at.isoformat() if n.submitted_at else None,
        })

    result.sort(key=lambda x: x["average_score"] or 0, reverse=True)

    return success_response(
        message="Nominations with scores fetched successfully",
        data=result,
    )


# =====================================================
# HR SUMMARY (FIXED)
# =====================================================
@router.get("/hr/summary")
def hr_summary(
    cycle_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    nominations = db.query(Nomination).filter(
        Nomination.cycle_id == cycle_id,
        Nomination.status.in_(["PANEL_REVIEW", "HR_REVIEW", "FINALIZED"]),
    ).all()

    data = []

    for n in nominations:
        avg_score = (
            db.query(func.avg(PanelReview.score))
            .join(
                PanelAssignment,
                PanelAssignment.id == PanelReview.panel_assignment_id,
            )
            .filter(PanelAssignment.nomination_id == n.id)
            .scalar()
        )

        panel_statuses = db.query(
            PanelAssignment.status
        ).filter(
            PanelAssignment.nomination_id == n.id
        ).all()

        completed_panels = sum(1 for (s,) in panel_statuses if s == "COMPLETED")
        all_completed = completed_panels == len(panel_statuses) and panel_statuses

        data.append({
            "nomination_id": str(n.id),
            "nominee_id": str(n.nominee_id),
            "average_score": float(avg_score) if avg_score else None,
            "panel_count": len(panel_statuses),
            "completed_panels": completed_panels,
            "ready_for_finalization": all_completed,
        })

    return success_response(
        message="HR summary fetched successfully",
        data=data,
    )