from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response

from app.models.user import User, UserRole
from app.models.nomination import Nomination
from app.models.form_answer import FormAnswer
from app.models.form import Form, FormField
from app.models.cycle import Cycle, CycleStatus
from app.models.panel_assignment import PanelAssignment
from app.models.panel_review import PanelReview
from app.models.panel_member import PanelMember

from app.schemas.nominations import NominationCreate

router = APIRouter()

# =====================================================
# CREATE NOMINATION (MANAGER / HR)
# =====================================================
@router.post("", status_code=status.HTTP_201_CREATED)
def submit_nomination(
    payload: NominationCreate,
    user: User = Depends(require_role(UserRole.MANAGER, UserRole.HR)),
    db: Session = Depends(get_db),
):
    cycle = db.get(Cycle, payload.cycle_id)
    if not cycle:
        return failure_response("Nomination failed", "Cycle not found", 404)

    if cycle.status != CycleStatus.OPEN:
        return failure_response(
            "Nomination failed",
            f"Cycle is {cycle.status.value}. Must be OPEN.",
            400,
        )

    # Check if cycle window has opened and not yet ended
    from datetime import date as date_type
    today = date_type.today()
    
    if today < cycle.start_date:
        return failure_response(
            "Nomination failed",
            "The nomination window has not opened yet.",
            400,
        )
    
    if today > cycle.end_date:
        return failure_response(
            "Nomination failed",
            "The nomination window for this cycle has already closed.",
            400,
        )

    form = db.get(Form, payload.form_id)
    if not form or not form.is_active:
        return failure_response("Nomination failed", "Form not found", 404)

    # Forms/criteria are independent and don't belong to any specific cycle

    nominee = db.get(User, payload.nominee_id)
    if not nominee or not nominee.is_active:
        return failure_response("Nomination failed", "Invalid nominee", 404)

    existing = db.query(Nomination).filter(
        Nomination.cycle_id == payload.cycle_id,
        Nomination.nominee_id == payload.nominee_id,
        Nomination.status.in_(["SUBMITTED", "PANEL_REVIEW", "HR_REVIEW"]),
    ).first()

    if existing:
        return failure_response(
            "Nomination failed",
            "Nomination already exists for this employee",
            400,
        )

    form_fields = db.query(FormField).filter(
        FormField.form_id == payload.form_id
    ).all()

    required_keys = {f.field_key for f in form_fields if f.is_required}
    answer_keys = {a.field_key for a in payload.answers}

    missing = required_keys - answer_keys
    if missing:
        return failure_response(
            "Nomination failed",
            f"Missing required fields: {', '.join(missing)}",
            400,
        )

    nomination = Nomination(
        cycle_id=payload.cycle_id,
        form_id=payload.form_id,
        nominee_id=payload.nominee_id,
        nominated_by_id=user.id,
        status="SUBMITTED",
        submitted_at=datetime.utcnow(),
    )

    db.add(nomination)
    db.flush()

    for ans in payload.answers:
        db.add(FormAnswer(
            nomination_id=nomination.id,
            field_key=ans.field_key,
            value=ans.value,
        ))

    db.commit()

    return success_response(
        message="Nomination submitted successfully",
        data={
            "id": str(nomination.id),
            "status": nomination.status,
        },
    )


# =====================================================
# LIST NOMINATIONS
# =====================================================
@router.get("")
def list_nominations(
    cycle_id: UUID | None = None,
    status: str | None = None,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.PANEL)),
    db: Session = Depends(get_db),
):
    query = db.query(Nomination)

    if cycle_id:
        query = query.filter(Nomination.cycle_id == cycle_id)

    if status:
        query = query.filter(Nomination.status == status)

    if user.role == UserRole.MANAGER:
        query = query.filter(Nomination.nominated_by_id == user.id)

    if user.role == UserRole.PANEL:
        nomination_ids = (
            db.query(PanelAssignment.nomination_id)
            .join(PanelReview, PanelReview.panel_assignment_id == PanelAssignment.id)
            .distinct()
        )
        query = query.filter(Nomination.id.in_(nomination_ids))

    nominations = query.order_by(Nomination.created_at.desc()).all()

    result = []

    for n in nominations:
        nominee = db.get(User, n.nominee_id) if n.nominee_id else None
        nominated_by = db.get(User, n.nominated_by_id) if n.nominated_by_id else None
        cycle = db.get(Cycle, n.cycle_id)

        result.append({
            "id": str(n.id),
            "cycle_id": str(n.cycle_id),
            "cycle": {
                "id": str(cycle.id),
                "name": cycle.name,
                "quarter": cycle.quarter,
                "year": cycle.year,
            } if cycle else None,
            "nominee_id": str(n.nominee_id),
            "nominee": {
                "id": str(nominee.id),
                "name": nominee.name,
                "email": nominee.email,
                "employee_code": nominee.employee_code,
            } if nominee else None,
            "nominated_by_id": str(n.nominated_by_id) if n.nominated_by_id else None,
            "nominated_by": {
                "id": str(nominated_by.id),
                "name": nominated_by.name,
                "email": nominated_by.email,
            } if nominated_by else None,
            "status": n.status,
            "submitted_at": n.submitted_at.isoformat() if n.submitted_at else None,
        })

    return success_response(
        message="Nominations fetched successfully",
        data=result,
    )

@router.get("/history")
def nomination_history(
    cycle_id: UUID | None = None,
    user: User = Depends(require_role(UserRole.MANAGER, UserRole.HR)),
    db: Session = Depends(get_db),
):
    query = db.query(Nomination)

    if user.role == UserRole.MANAGER:
        query = query.filter(Nomination.nominated_by_id == user.id)

    if cycle_id:
        query = query.filter(Nomination.cycle_id == cycle_id)

    nominations = query.order_by(Nomination.created_at.desc()).all()

    result = []

    for n in nominations:
        nominee = db.get(User, n.nominee_id) if n.nominee_id else None
        cycle = db.get(Cycle, n.cycle_id)

        result.append({
            "id": str(n.id),
            "cycle_id": str(n.cycle_id),
            "cycle": {
                "id": str(cycle.id),
                "name": cycle.name,
                "quarter": cycle.quarter,
                "year": cycle.year,
            } if cycle else None,
            "nominee_id": str(n.nominee_id),
            "nominee": {
                "id": str(nominee.id),
                "name": nominee.name,
                "email": nominee.email,
                "employee_code": nominee.employee_code,
            } if nominee else None,
            "status": n.status,
            "submitted_at": n.submitted_at.isoformat()
            if n.submitted_at else None,
        })

    return success_response(
        message="Nomination history fetched successfully",
        data=result,
    )


# =====================================================
# GET SINGLE NOMINATION
# =====================================================
@router.get("/{nomination_id}")
def get_nomination(
    nomination_id: UUID,
    user: User = Depends(require_role(
        UserRole.HR, UserRole.MANAGER, UserRole.PANEL
    )),
    db: Session = Depends(get_db),
):
    nomination = db.get(Nomination, nomination_id)
    if not nomination:
        return failure_response("Not found", "Nomination not found", 404)

    answers = db.query(FormAnswer).filter(
        FormAnswer.nomination_id == nomination.id
    ).all()

    nominee = db.get(User, nomination.nominee_id) if nomination.nominee_id else None
    nominated_by = db.get(User, nomination.nominated_by_id) if nomination.nominated_by_id else None
    cycle = db.get(Cycle, nomination.cycle_id)

    # Panel reviews for this nomination
    reviews_query = (
        db.query(PanelReview, PanelMember, User, PanelAssignment)
        .join(PanelAssignment, PanelAssignment.id == PanelReview.panel_assignment_id)
        .join(PanelMember, PanelMember.id == PanelReview.panel_member_id)
        .join(User, User.id == PanelMember.user_id)
        .filter(PanelAssignment.nomination_id == nomination.id)
        .order_by(PanelReview.reviewed_at.desc())
    )

    review_payload = []
    for review, member, reviewer_user, assignment in reviews_query.all():
        review_payload.append({
            "id": str(review.id),
            "score": review.score,
            "comment": review.comment,
            "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
            "reviewer": {
                "id": str(reviewer_user.id),
                "name": reviewer_user.name,
                "email": reviewer_user.email,
            },
            "panel": {
                "id": str(assignment.panel_id),
            },
        })

    return success_response(
        message="Nomination fetched successfully",
        data={
            "id": str(nomination.id),
            "cycle_id": str(nomination.cycle_id),
            "cycle": {
                "id": str(cycle.id),
                "name": cycle.name,
                "quarter": cycle.quarter,
                "year": cycle.year,
            } if cycle else None,
            "form_id": str(nomination.form_id),
            "nominee_id": str(nomination.nominee_id),
            "nominee": {
                "id": str(nominee.id),
                "name": nominee.name,
                "email": nominee.email,
                "employee_code": nominee.employee_code,
            } if nominee else None,
            "nominated_by": {
                "id": str(nominated_by.id),
                "name": nominated_by.name,
                "email": nominated_by.email,
            } if nominated_by else None,
            "status": nomination.status,
            "submitted_at": nomination.submitted_at.isoformat() if nomination.submitted_at else None,
            "created_at": nomination.created_at.isoformat(),
            "answers": [
                {"field_key": a.field_key, "value": a.value}
                for a in answers
            ],
            "reviews": review_payload,
        },
    )


# =====================================================
# HR → UPDATE NOMINATION STATUS
# =====================================================
@router.patch("/{nomination_id}/status")
def update_nomination_status(
    nomination_id: UUID,
    status: str = Query(..., description="New status for the nomination"),
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    valid = ["SUBMITTED", "PANEL_REVIEW", "HR_REVIEW", "FINALIZED"]
    if status not in valid:
        return failure_response("Invalid", "Invalid status", 400)

    nomination = db.get(Nomination, nomination_id)
    if not nomination:
        return failure_response("Not found", "Nomination not found", 404)

    cycle = db.get(Cycle, nomination.cycle_id)
    if not cycle:
        return failure_response("Not found", "Cycle not found", 404)

    # Can only finalize nominations after cycle is CLOSED
    if status == "FINALIZED":
        if cycle.status != CycleStatus.CLOSED and cycle.status != CycleStatus.FINALIZED:
            return failure_response(
                "Invalid operation",
                "Cannot finalize nominations until the nomination window is closed",
                400,
            )
        
        # Can only finalize if nomination is in HR_REVIEW (has been reviewed)
        if nomination.status != "HR_REVIEW":
            return failure_response(
                "Invalid operation",
                "Can only finalize nominations that are in HR_REVIEW status",
                400,
            )

    nomination.status = status
    nomination.updated_at = datetime.utcnow()

    db.commit()

    return success_response(
        message="Nomination status updated",
        data={"status": nomination.status},
    )


# =====================================================
# DELETE SINGLE NOMINATION (HR)
# =====================================================
@router.delete("/{nomination_id}")
def delete_nomination(
    nomination_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    nomination = db.get(Nomination, nomination_id)
    if not nomination:
        return failure_response("Not found", "Nomination not found", 404)

    # Check if nomination has associated awards
    from app.models.award import Award
    existing_award = db.query(Award).filter(
        Award.nomination_id == nomination_id,
        Award.is_active == True,
    ).first()

    if existing_award:
        return failure_response(
            "Deletion failed",
            "Cannot delete nomination with associated award. Delete the award first.",
            400,
        )

    # Delete related data (cascade should handle most, but being explicit)
    # Panel reviews
    db.query(PanelReview).filter(
        PanelReview.panel_assignment_id.in_(
            db.query(PanelAssignment.id).filter(
                PanelAssignment.nomination_id == nomination_id
            )
        )
    ).delete(synchronize_session=False)

    # Panel assignments
    db.query(PanelAssignment).filter(
        PanelAssignment.nomination_id == nomination_id
    ).delete(synchronize_session=False)

    # Form answers (cascade should handle this)
    db.query(FormAnswer).filter(
        FormAnswer.nomination_id == nomination_id
    ).delete(synchronize_session=False)

    # Delete nomination
    db.delete(nomination)
    db.commit()

    return success_response(
        message="Nomination deleted successfully",
        data={"id": str(nomination_id)},
    )


# =====================================================
# DELETE ALL NOMINATIONS FOR A CYCLE (HR)
# =====================================================
@router.delete("/cycle/{cycle_id}/all")
def delete_all_nominations_for_cycle(
    cycle_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    cycle = db.get(Cycle, cycle_id)
    if not cycle:
        return failure_response("Not found", "Cycle not found", 404)

    # Get all nominations for this cycle
    nominations = db.query(Nomination).filter(
        Nomination.cycle_id == cycle_id
    ).all()

    if not nominations:
        return success_response(
            message="No nominations found for this cycle",
            data={"deleted_count": 0},
        )

    nomination_ids = [n.id for n in nominations]

    # Check if any nomination has associated awards
    from app.models.award import Award
    existing_awards = db.query(Award).filter(
        Award.nomination_id.in_(nomination_ids),
        Award.is_active == True,
    ).count()

    if existing_awards > 0:
        return failure_response(
            "Deletion failed",
            f"Cannot delete nominations with associated awards. {existing_awards} nomination(s) have awards. Delete the awards first.",
            400,
        )

    # Delete panel reviews
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

    # Delete form answers
    db.query(FormAnswer).filter(
        FormAnswer.nomination_id.in_(nomination_ids)
    ).delete(synchronize_session=False)

    # Delete nominations
    deleted_count = db.query(Nomination).filter(
        Nomination.cycle_id == cycle_id
    ).delete()

    db.commit()

    return success_response(
        message=f"Deleted {deleted_count} nomination(s) successfully",
        data={"deleted_count": deleted_count},
    )