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

from app.schemas.awards import AwardCreate

router = APIRouter()


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

    nomination = db.get(Nomination, payload.nomination_id)
    if not nomination:
        return failure_response("Award creation failed", "Nomination not found", 404)

    if nomination.cycle_id != payload.cycle_id:
        return failure_response(
            "Award creation failed",
            "Nomination does not belong to this cycle",
            400,
        )

    if nomination.status != "FINALIZED":
        return failure_response(
            "Award creation failed",
            "Nomination must be FINALIZED before creating an award",
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