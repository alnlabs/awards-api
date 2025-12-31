from fastapi import APIRouter, Depends, status
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

    form = db.get(Form, payload.form_id)
    if not form or not form.is_active:
        return failure_response("Nomination failed", "Form not found", 404)

    if form.cycle_id != payload.cycle_id:
        return failure_response(
            "Nomination failed",
            "Form does not belong to cycle",
            400,
        )

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

    return success_response(
        message="Nominations fetched successfully",
        data=[{
            "id": str(n.id),
            "cycle_id": str(n.cycle_id),
            "nominee_id": str(n.nominee_id),
            "nominated_by_id": str(n.nominated_by_id),
            "status": n.status,
            "submitted_at": n.submitted_at.isoformat() if n.submitted_at else None,
        } for n in nominations],
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

    return success_response(
        message="Nomination history fetched successfully",
        data=[{
            "id": str(n.id),
            "cycle_id": str(n.cycle_id),
            "nominee_id": str(n.nominee_id),
            "status": n.status,
            "submitted_at": n.submitted_at.isoformat()
            if n.submitted_at else None,
        } for n in nominations],
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

    return success_response(
        message="Nomination fetched successfully",
        data={
            "id": str(nomination.id),
            "cycle_id": str(nomination.cycle_id),
            "form_id": str(nomination.form_id),
            "nominee_id": str(nomination.nominee_id),
            "status": nomination.status,
            "answers": [
                {"field_key": a.field_key, "value": a.value}
                for a in answers
            ],
        },
    )


# =====================================================
# HR → UPDATE NOMINATION STATUS
# =====================================================
@router.patch("/{nomination_id}/status")
def update_nomination_status(
    nomination_id: UUID,
    status: str,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    valid = ["SUBMITTED", "PANEL_REVIEW", "HR_REVIEW", "FINALIZED"]
    if status not in valid:
        return failure_response("Invalid", "Invalid status", 400)

    nomination = db.get(Nomination, nomination_id)
    if not nomination:
        return failure_response("Not found", "Nomination not found", 404)

    nomination.status = status
    nomination.updated_at = datetime.utcnow()

    db.commit()

    return success_response(
        message="Nomination status updated",
        data={"status": nomination.status},
    )