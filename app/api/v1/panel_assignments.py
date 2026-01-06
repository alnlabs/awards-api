from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import require_role, require_panel_member
from app.core.response import success_response, failure_response

from app.models.user import User, UserRole
from app.models.nomination import Nomination
from app.models.panel import Panel
from app.models.panel_assignment import PanelAssignment
from app.models.panel_member import PanelMember
from app.models.panel_task import PanelTask
from app.models.panel_review import PanelReview
from app.models.form_answer import FormAnswer
from app.models.cycle import Cycle

from app.schemas.panel import PanelAssignmentCreate, PanelReviewCreate

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
        return failure_response("Nomination not found", "Invalid nomination", 404)
    # Existing panel assignments for this nomination
    existing_assignments = (
        db.query(PanelAssignment)
        .filter(PanelAssignment.nomination_id == nomination_id)
        .all()
    )
    existing_panel_ids = {pa.panel_id for pa in existing_assignments}

    created_count = 0

    for panel_id in payload.panel_ids:
        # Skip panels already assigned to this nomination
        if panel_id in existing_panel_ids:
            continue

        panel = db.get(Panel, panel_id)
        if not panel:
            return failure_response(
                f"Panel {panel_id} not found",
                "Invalid panel",
                404,
            )

        db.add(
            PanelAssignment(
                nomination_id=nomination_id,
                panel_id=panel_id,
                assigned_by=user.id,
                status="PENDING",
            )
        )
        created_count += 1

    if created_count == 0:
        return failure_response(
            "No new panels assigned",
            "All selected panels are already assigned to this nomination",
            400,
        )

    nomination.status = "PANEL_REVIEW"
    nomination.updated_at = datetime.utcnow()

    db.commit()

    return success_response(
        message="Panels assigned successfully",
        data={"nomination_id": str(nomination_id)},
    )

# =====================================================
# HR → View assigned panels for a nomination (FIXED)
# =====================================================
@router.get("/nomination/{nomination_id}")
def get_assignments_for_nomination(
    nomination_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db),
):
    assignments = (
        db.query(PanelAssignment)
        .filter(PanelAssignment.nomination_id == nomination_id)
        .all()
    )

    result = []

    for assignment in assignments:
        panel = db.get(Panel, assignment.panel_id)

        # ✅ EXPLICIT JOIN TO USER
        members = (
            db.query(PanelMember, User)
            .join(User, User.id == PanelMember.user_id)
            .filter(PanelMember.panel_id == panel.id)
            .all()
        )

        result.append({
            "assignment_id": str(assignment.id),
            "status": assignment.status,
            "assigned_at": assignment.assigned_at.isoformat(),
            "panel": {
                "id": str(panel.id),
                "name": panel.name,
                "members": [
                    {
                        "id": str(m.id),
                        "user_id": str(u.id),
                        "name": u.name,
                        "email": u.email,
                        "role": m.role,
                    }
                    for m, u in members
                ],
            },
        })

    return success_response(
        message="Assigned panels fetched",
        data=result,
    )

# =====================================================
# HR → View all panel assignments
# =====================================================
@router.get("/all")
def get_all_panel_assignments(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.HR)),
):
    assignments = (
        db.query(PanelAssignment)
        .order_by(PanelAssignment.assigned_at.desc())
        .all()
    )

    data = []

    for assignment in assignments:
        panel = db.get(Panel, assignment.panel_id)
        nomination = db.get(Nomination, assignment.nomination_id)

        if not panel or not nomination:
            continue

        # Get nominee details
        nominee = db.get(User, nomination.nominee_id)
        if not nominee:
            continue

        # Get nominated by details
        nominated_by = db.get(User, nomination.nominated_by_id)

        # Get cycle details
        cycle = db.get(Cycle, nomination.cycle_id)

        # Get all panel members for this panel
        panel_members = (
            db.query(PanelMember, User)
            .join(User, User.id == PanelMember.user_id)
            .filter(PanelMember.panel_id == panel.id)
            .all()
        )

        # Get tasks for this panel
        tasks = (
            db.query(PanelTask)
            .filter(PanelTask.panel_id == panel.id)
            .order_by(PanelTask.order_index)
            .all()
        )

        # Count completed reviews across all panel members
        total_reviews = (
            db.query(PanelReview)
            .filter(PanelReview.panel_assignment_id == assignment.id)
            .count()
        )

        total_possible = len(tasks) * len(panel_members)
        completed = total_reviews
        is_complete = completed == total_possible and total_possible > 0

        data.append({
            "assignment_id": str(assignment.id),
            "assignment_status": assignment.status,
            "assigned_at": assignment.assigned_at.isoformat(),
            "panel": {
                "id": str(panel.id),
                "name": panel.name,
                "description": panel.description,
            },
            "nomination": {
                "id": str(nomination.id),
                "nominee_id": str(nomination.nominee_id),
                "nominee": {
                    "id": str(nominee.id),
                    "name": nominee.name,
                    "email": nominee.email,
                    "employee_code": nominee.employee_code,
                },
                "nominated_by": {
                    "id": str(nominated_by.id) if nominated_by else None,
                    "name": nominated_by.name if nominated_by else None,
                    "email": nominated_by.email if nominated_by else None,
                },
                "cycle": {
                    "id": str(cycle.id) if cycle else None,
                    "name": cycle.name if cycle else None,
                    "quarter": cycle.quarter if cycle else None,
                    "year": cycle.year if cycle else None,
                },
                "status": nomination.status,
                "submitted_at": (
                    nomination.submitted_at.isoformat()
                    if nomination.submitted_at else None
                ),
            },
            "progress": {
                "completed": completed,
                "total": total_possible,
                "is_complete": is_complete,
            },
            "panel_members_count": len(panel_members),
            "tasks_count": len(tasks),
        })

    return success_response(
        message="All panel assignments fetched successfully",
        data=data,
    )

# =====================================================
# PANEL MEMBER → View my assignments
# =====================================================
@router.get("/my")
def get_my_panel_assignments(
    db: Session = Depends(get_db),
    user: User = Depends(require_panel_member()),
):
    assignments = (
        db.query(PanelAssignment)
        .join(PanelMember, PanelMember.panel_id == PanelAssignment.panel_id)
        .filter(PanelMember.user_id == user.id)
        .order_by(PanelAssignment.assigned_at.desc())
        .all()
    )

    data = []

    for assignment in assignments:
        panel = db.get(Panel, assignment.panel_id)
        nomination = db.get(Nomination, assignment.nomination_id)

        if not panel or not nomination:
            continue

        # Get nominee details
        nominee = db.get(User, nomination.nominee_id)
        if not nominee:
            continue

        # Get nominated by details
        nominated_by = db.get(User, nomination.nominated_by_id)

        # Get cycle details
        cycle = db.get(Cycle, nomination.cycle_id)

        # Get nomination answers
        form_answers = (
            db.query(FormAnswer)
            .filter(FormAnswer.nomination_id == nomination.id)
            .all()
        )

        panel_member = (
            db.query(PanelMember)
            .filter(
                PanelMember.panel_id == panel.id,
                PanelMember.user_id == user.id,
            )
            .first()
        )
        # Safety: if for some reason this user is no longer a member of this panel,
        # skip this assignment instead of crashing.
        if not panel_member:
            continue

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

        # Map by panel_task_id so we can attach reviews to tasks
        review_map = {r.panel_task_id: r for r in reviews}
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
                "nominee": {
                    "id": str(nominee.id),
                    "name": nominee.name,
                    "email": nominee.email,
                    "employee_code": nominee.employee_code,
                },
                "nominated_by": {
                    "id": str(nominated_by.id) if nominated_by else None,
                    "name": nominated_by.name if nominated_by else None,
                    "email": nominated_by.email if nominated_by else None,
                },
                "cycle": {
                    "id": str(cycle.id) if cycle else None,
                    "name": cycle.name if cycle else None,
                    "quarter": cycle.quarter if cycle else None,
                    "year": cycle.year if cycle else None,
                },
                "status": nomination.status,
                "submitted_at": (
                    nomination.submitted_at.isoformat()
                    if nomination.submitted_at else None
                ),
                "answers": [
                    {
                        "field_key": fa.field_key,
                        "value": fa.value,
                    }
                    for fa in form_answers
                ],
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
    user: User = Depends(require_panel_member()),
):
    assignment = db.get(PanelAssignment, assignment_id)
    if not assignment:
        return failure_response("Panel assignment not found", "Invalid assignment", 404)

    panel_member = (
        db.query(PanelMember)
        .filter(
            PanelMember.panel_id == assignment.panel_id,
            PanelMember.user_id == user.id,
        )
        .first()
    )
    if not panel_member:
        return failure_response("You are not a member of this panel", "Access denied", 403)

    task = db.get(PanelTask, task_id)
    if not task or task.panel_id != assignment.panel_id:
        return failure_response("Task does not belong to this panel", "Invalid task", 400)

    review = (
        db.query(PanelReview)
        .filter(
            PanelReview.panel_assignment_id == assignment_id,
            PanelReview.panel_member_id == panel_member.id,
            PanelReview.panel_task_id == task_id,
        )
        .first()
    )

    if review:
        review.score = payload.score
        review.comment = payload.comment
        review.reviewed_at = datetime.utcnow()
    else:
        db.add(
            PanelReview(
                panel_assignment_id=assignment_id,
                panel_member_id=panel_member.id,
                panel_task_id=task_id,
                score=payload.score,
                comment=payload.comment,
            )
        )

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
        r.panel_task_id
        for r in db.query(PanelReview.panel_task_id)
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
            "panel_task_id": str(task_id),
            "assignment_status": assignment.status,
        },
    )