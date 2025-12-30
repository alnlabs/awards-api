from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response
from app.models.user import User, UserRole
from app.models.nomination import Nomination, FormAnswer
from app.models.form import Form, FormField
from app.models.cycle import Cycle, CycleStatus
from app.models.panel_review import PanelReview
from app.schemas.nominations import (
    NominationCreate,
    NominationUpdate,
    NominationResponse,
    PanelReviewCreate
)

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
def submit_nomination(
    payload: NominationCreate,
    user: User = Depends(require_role(UserRole.MANAGER, UserRole.HR)),
    db: Session = Depends(get_db)
):
    # Verify cycle exists and is open
    cycle = db.get(Cycle, payload.cycle_id)
    if not cycle:
        failure_response(
            message="Nomination submission failed",
            error="Cycle not found",
            status_code=404
        )

    if cycle.status != CycleStatus.OPEN:
        failure_response(
            message="Nomination submission failed",
            error=f"Cycle is {cycle.status.value}. Nominations can only be submitted when cycle is OPEN.",
            status_code=400
        )

    # Verify form exists and belongs to cycle
    form = db.get(Form, payload.form_id)
    if not form or not form.is_active:
        failure_response(
            message="Nomination submission failed",
            error="Form not found",
            status_code=404
        )

    if form.cycle_id != payload.cycle_id:
        failure_response(
            message="Nomination submission failed",
            error="Form does not belong to this cycle",
            status_code=400
        )

    # Verify nominee exists and is active
    nominee = db.get(User, payload.nominee_id)
    if not nominee or not nominee.is_active:
        failure_response(
            message="Nomination submission failed",
            error="Nominee not found or inactive",
            status_code=404
        )

    # Check for existing nomination (one per employee per cycle)
    existing = db.query(Nomination).filter(
        Nomination.cycle_id == payload.cycle_id,
        Nomination.nominee_id == payload.nominee_id,
        Nomination.status.in_(["DRAFT", "SUBMITTED", "HR_REVIEW", "PANEL_REVIEW"])
    ).first()

    if existing and payload.status != "DRAFT":
        failure_response(
            message="Nomination submission failed",
            error="A nomination for this employee already exists in this cycle",
            status_code=400
        )

    # Get form fields to validate answers
    form_fields = db.query(FormField).filter(
        FormField.form_id == payload.form_id
    ).all()

    field_keys = {f.field_key for f in form_fields}
    answer_keys = {a.field_key for a in payload.answers}

    # Check all required fields are answered
    required_fields = {f.field_key for f in form_fields if f.is_required}
    missing_required = required_fields - answer_keys

    if missing_required and payload.status != "DRAFT":
        failure_response(
            message="Nomination submission failed",
            error=f"Missing required fields: {', '.join(missing_required)}",
            status_code=400
        )

    # Check for invalid field keys
    invalid_keys = answer_keys - field_keys
    if invalid_keys:
        failure_response(
            message="Nomination submission failed",
            error=f"Invalid field keys: {', '.join(invalid_keys)}",
            status_code=400
        )

    # Create nomination
    nomination_status = payload.status if payload.status in ["DRAFT", "SUBMITTED"] else "SUBMITTED"
    submitted_at = datetime.utcnow() if nomination_status == "SUBMITTED" else None

    nomination = Nomination(
        cycle_id=payload.cycle_id,
        form_id=payload.form_id,
        nominee_id=payload.nominee_id,
        nominated_by_id=user.id,
        status=nomination_status,
        submitted_at=submitted_at
    )

    db.add(nomination)
    db.flush()  # Get nomination.id

    # Create answers
    for answer_data in payload.answers:
        answer = FormAnswer(
            nomination_id=nomination.id,
            field_key=answer_data.field_key,
            value=answer_data.value
        )
        db.add(answer)

    db.commit()
    db.refresh(nomination)

    return success_response(
        message="Nomination submitted successfully",
        data={
            "id": str(nomination.id),
            "status": nomination.status,
            "cycle_id": str(nomination.cycle_id),
            "nominee_id": str(nomination.nominee_id)
        }
    )


@router.get("/history", response_model=dict)
def nomination_history(
    cycle_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(require_role(UserRole.MANAGER, UserRole.HR)),
    db: Session = Depends(get_db)
):
    query = db.query(Nomination)

    # Managers see their own nominations
    if user.role == UserRole.MANAGER:
        query = query.filter(Nomination.nominated_by_id == user.id)

    if cycle_id:
        query = query.filter(Nomination.cycle_id == cycle_id)

    nominations = query.order_by(Nomination.created_at.desc()).offset(skip).limit(limit).all()

    return success_response(
        message="Nominations fetched successfully",
        data=[
            {
                "id": str(n.id),
                "cycle_id": str(n.cycle_id),
                "nominee_id": str(n.nominee_id),
                "nominated_by_id": str(n.nominated_by_id),
                "status": n.status,
                "submitted_at": n.submitted_at.isoformat() if n.submitted_at else None,
                "created_at": n.created_at.isoformat()
            }
            for n in nominations
        ]
    )


@router.get("", response_model=dict)
def list_nominations(
    cycle_id: UUID = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(require_role(UserRole.HR, UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    query = db.query(Nomination)

    if cycle_id:
        query = query.filter(Nomination.cycle_id == cycle_id)

    if status:
        query = query.filter(Nomination.status == status)

    # Panel members see only nominations they've reviewed or assigned to them
    if user.role == UserRole.PANEL:
        reviewed_nomination_ids = [
            r[0] for r in db.query(PanelReview.nomination_id).filter(
                PanelReview.panel_member_id == user.id
            ).all()
        ]
        if reviewed_nomination_ids:
            query = query.filter(Nomination.id.in_(reviewed_nomination_ids))
        else:
            query = query.filter(False)  # No nominations if user hasn't reviewed any

    nominations = query.order_by(Nomination.created_at.desc()).offset(skip).limit(limit).all()

    return success_response(
        message="Nominations fetched successfully",
        data=[
            {
                "id": str(n.id),
                "cycle_id": str(n.cycle_id),
                "nominee_id": str(n.nominee_id),
                "nominated_by_id": str(n.nominated_by_id),
                "status": n.status,
                "submitted_at": n.submitted_at.isoformat() if n.submitted_at else None,
                "created_at": n.created_at.isoformat()
            }
            for n in nominations
        ]
    )


@router.get("/{nomination_id}", response_model=dict)
def get_nomination(
    nomination_id: UUID,
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER, UserRole.PANEL, UserRole.EMPLOYEE)),
    db: Session = Depends(get_db)
):
    nomination = db.get(Nomination, nomination_id)

    if not nomination:
        failure_response(
            message="Nomination not found",
            error="Nomination does not exist",
            status_code=404
        )

    # Check access permissions
    if user.role == UserRole.MANAGER and nomination.nominated_by_id != user.id:
        failure_response(
            message="Access denied",
            error="You can only view nominations you created",
            status_code=403
        )

    # Load answers
    answers = db.query(FormAnswer).filter(
        FormAnswer.nomination_id == nomination.id
    ).all()

    # Load reviews if HR or Panel
    reviews = []
    if user.role in [UserRole.HR, UserRole.PANEL]:
        reviews_query = db.query(PanelReview).filter(
            PanelReview.nomination_id == nomination.id
        ).all()
        reviews = [
            {
                "id": str(r.id),
                "panel_member_id": str(r.panel_member_id),
                "score": r.score,
                "comments": r.comments,
                "created_at": r.created_at.isoformat()
            }
            for r in reviews_query
        ]

    return success_response(
        message="Nomination fetched successfully",
        data={
            "id": str(nomination.id),
            "cycle_id": str(nomination.cycle_id),
            "form_id": str(nomination.form_id),
            "nominee_id": str(nomination.nominee_id),
            "nominated_by_id": str(nomination.nominated_by_id),
            "status": nomination.status,
            "submitted_at": nomination.submitted_at.isoformat() if nomination.submitted_at else None,
            "created_at": nomination.created_at.isoformat(),
            "updated_at": nomination.updated_at.isoformat() if nomination.updated_at else None,
            "answers": [
                {
                    "id": str(a.id),
                    "field_key": a.field_key,
                    "value": a.value
                }
                for a in answers
            ],
            "reviews": reviews
        }
    )


@router.patch("/{nomination_id}/status", response_model=dict)
def update_nomination_status(
    nomination_id: UUID,
    status: str,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    nomination = db.get(Nomination, nomination_id)

    if not nomination:
        failure_response(
            message="Nomination not found",
            error="Nomination does not exist",
            status_code=404
        )

    valid_statuses = ["DRAFT", "SUBMITTED", "HR_REVIEW", "PANEL_REVIEW", "FINALIZED"]
    if status not in valid_statuses:
        failure_response(
            message="Invalid status",
            error=f"Status must be one of: {', '.join(valid_statuses)}",
            status_code=400
        )

    nomination.status = status
    nomination.updated_at = datetime.utcnow()

    if status == "SUBMITTED" and not nomination.submitted_at:
        nomination.submitted_at = datetime.utcnow()

    db.commit()

    return success_response(
        message="Nomination status updated successfully",
        data={
            "id": str(nomination.id),
            "status": nomination.status,
            "updated_at": nomination.updated_at.isoformat()
        }
    )


@router.post("/{nomination_id}/review", status_code=status.HTTP_201_CREATED, response_model=dict)
def submit_panel_review(
    nomination_id: UUID,
    payload: PanelReviewCreate,
    user: User = Depends(require_role(UserRole.PANEL)),
    db: Session = Depends(get_db)
):
    nomination = db.get(Nomination, nomination_id)

    if not nomination:
        failure_response(
            message="Nomination not found",
            error="Nomination does not exist",
            status_code=404
        )

    if nomination.status not in ["HR_REVIEW", "PANEL_REVIEW"]:
        failure_response(
            message="Review submission failed",
            error=f"Nomination is in {nomination.status} status. Reviews can only be submitted for nominations in HR_REVIEW or PANEL_REVIEW status.",
            status_code=400
        )

    # Check if user already reviewed this nomination
    existing_review = db.query(PanelReview).filter(
        PanelReview.nomination_id == nomination_id,
        PanelReview.panel_member_id == user.id
    ).first()

    if existing_review:
        # Update existing review
        existing_review.score = payload.score
        existing_review.comments = payload.comments
        existing_review.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_review)

        return success_response(
            message="Review updated successfully",
            data={
                "id": str(existing_review.id),
                "nomination_id": str(existing_review.nomination_id),
                "score": existing_review.score,
                "comments": existing_review.comments
            }
        )

    # Create new review
    review = PanelReview(
        nomination_id=nomination_id,
        panel_member_id=user.id,
        score=payload.score,
        comments=payload.comments
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return success_response(
        message="Review submitted successfully",
        data={
            "id": str(review.id),
            "nomination_id": str(review.nomination_id),
            "score": review.score,
            "comments": review.comments
        }
    )