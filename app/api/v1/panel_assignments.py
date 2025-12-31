from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response

from app.models.user import User, UserRole
from app.models.nomination import Nomination
from app.models.panel import Panel
from app.models.panel_assignment import PanelAssignment
from app.models.panel_member import PanelMember
from app.models.panel_task import PanelTask
from app.models.panel_review import PanelReview

from app.schemas.panel import PanelAssignmentCreate, PanelReviewCreate

# ✅ IMPORTANT: prefix added
router = APIRouter()


# =====================================================
# HR → Assign panels to nomination
# =====================================================
@router.post(
    "/nomination/{nomination_id}/assign",
    status_code=status.HTTP_201_CREATED,
)
def assign_panels_to_nomination(
    nomination_id: UUID,
    payload: PanelAssignmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.HR)),
):
    nomination = db.get(Nomination, nomination_id)
    if not nomination:
        return failure_response("Nomination not found", status_code=404)

    existing = (
        db.query(PanelAssignment)
        .filter(PanelAssignment.nomination_id == nomination_id)
        .first()
    )
    if existing:
        return failure_response(
            "Panels already assigned to this nomination",
            status_code=400,
        )

    for panel_id in payload.panel_ids:
        panel = db.get(Panel, panel_id)
        if not panel:
            return failure_response(
                f"Panel {panel_id} not found",
                status_code=404,
            )

        assignment = PanelAssignment(
            nomination_id=nomination_id,
            panel_id=panel_id,
            assigned_by=user.id,
            status="PENDING",
        )
        db.add(assignment)

    nomination.status = "PANEL_REVIEW"
    db.commit()

    return success_response(
        message="Panels assigned successfully",
        data={"nomination_id": str(nomination_id)},
        status_code=201,
    )


# =====================================================
# PANEL MEMBER → View my assignments
# =====================================================
@router.get("/my", response_model=dict)
def get_my_panel_assignments(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.PANEL)),
):
    assignments = (
        db.query(PanelAssignment)
        .join(PanelMember, PanelMember.panel_id == PanelAssignment.panel_id)
        .filter(PanelMember.user_id == user.id)
        .order_by(PanelAssignment.assigned_at.desc())  # ✅ FIXED
        .all()
    )

    data = []

    for assignment in assignments:
        panel = db.get(Panel, assignment.panel_id)
        nomination = db.get(Nomination, assignment.nomination_id)

        if not panel or not nomination:
            continue

        panel_member = (
            db.query(PanelMember)
            .filter(
                PanelMember.panel_id == panel.id,
                PanelMember.user_id == user.id,
            )
            .first()
        )

        tasks = (
            db.query(PanelTask)
            .filter(PanelTask.panel_id == panel.id)
            .order_by(PanelTask.order_index)
            .all()
        )

        reviews = (
            db.query(PanelReview)
            .filter(
                PanelReview.panel_assignment_id == assignment.id,
                PanelReview.panel_member_id == panel_member.id,
            )
            .all()
        )

        review_map = {r.task_id: r for r in reviews}
        completed = 0

        task_payload = []
        for t in tasks:
            review = review_map.get(t.id)
            if review:
                completed += 1

            task_payload.append({
                "task_id": str(t.id),
                "title": t.title,
                "description": t.description,
                "max_score": t.max_score,
                "is_required": t.is_required,
                "order_index": t.order_index,
                "review": (
                    {
                        "score": review.score,
                        "comment": review.comment,
                        "reviewed_at": review.reviewed_at.isoformat(),
                    }
                    if review else None
                ),
            })

        data.append({
            "assignment_id": str(assignment.id),
            "assignment_status": assignment.status,
            "panel": {
                "id": str(panel.id),
                "name": panel.name,
                "description": panel.description,
            },
            "nomination": {
                "id": str(nomination.id),
                "nominee_id": str(nomination.nominee_id),
                "status": nomination.status,
                "submitted_at": nomination.submitted_at.isoformat()
                if nomination.submitted_at else None,
            },
            "tasks": task_payload,
            "progress": {
                "completed": completed,
                "total": len(tasks),
                "is_complete": completed == len(tasks) and len(tasks) > 0,
            },
        })

    return success_response(
        message="Panel assignments fetched successfully",
        data=data,
    )


# =====================================================
# PANEL MEMBER → Submit / update task review
# =====================================================
@router.post(
    "/{assignment_id}/tasks/{task_id}/review",
    status_code=status.HTTP_201_CREATED,
)
def submit_panel_review(
    assignment_id: UUID,
    task_id: UUID,
    payload: PanelReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.PANEL)),
):
    assignment = db.get(PanelAssignment, assignment_id)
    if not assignment:
        return failure_response("Panel assignment not found", status_code=404)

    panel_member = (
        db.query(PanelMember)
        .filter(
            PanelMember.panel_id == assignment.panel_id,
            PanelMember.user_id == user.id,
        )
        .first()
    )
    if not panel_member:
        return failure_response("You are not a member of this panel", 403)

    task = db.get(PanelTask, task_id)
    if not task or task.panel_id != assignment.panel_id:
        return failure_response("Task does not belong to this panel", 400)

    review = (
        db.query(PanelReview)
        .filter(
            PanelReview.panel_assignment_id == assignment_id,
            PanelReview.panel_member_id == panel_member.id,
            PanelReview.task_id == task_id,
        )
        .first()
    )

    if review:
        review.score = payload.score
        review.comment = payload.comment
        review.reviewed_at = datetime.utcnow()
    else:
        review = PanelReview(
            panel_assignment_id=assignment_id,
            panel_member_id=panel_member.id,
            task_id=task_id,
            score=payload.score,
            comment=payload.comment,
        )
        db.add(review)

    db.flush()

    # ===== AUTO COMPLETE ASSIGNMENT =====
    required_task_ids = {
        t.id
        for t in db.query(PanelTask)
        .filter(
            PanelTask.panel_id == assignment.panel_id,
            PanelTask.is_required == True,
        )
        .all()
    }

    reviewed_task_ids = {
        r.task_id
        for r in db.query(PanelReview.task_id)
        .filter(
            PanelReview.panel_assignment_id == assignment_id,
            PanelReview.panel_member_id == panel_member.id,
        )
        .all()
    }

    if required_task_ids.issubset(reviewed_task_ids):
        assignment.status = "COMPLETED"
        assignment.completed_at = datetime.utcnow()

        all_assignments = (
            db.query(PanelAssignment)
            .filter(PanelAssignment.nomination_id == assignment.nomination_id)
            .all()
        )

        if all(a.status == "COMPLETED" for a in all_assignments):
            nomination = db.get(Nomination, assignment.nomination_id)
            nomination.status = "HR_REVIEW"
            nomination.updated_at = datetime.utcnow()

    db.commit()

    return success_response(
        message="Review submitted successfully",
        data={
            "assignment_id": str(assignment.id),
            "task_id": str(task_id),
            "assignment_status": assignment.status,
        },
        status_code=201,
    )