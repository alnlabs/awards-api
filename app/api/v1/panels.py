from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.response import success_response
from app.models.panel import Panel
from app.models.panel_member import PanelMember
from app.models.panel_task import PanelTask
from app.models.user import User

from app.schemas.panel import (
    PanelCreate,
    PanelUpdate,
    PanelMemberCreate,
    PanelMemberUpdate,
    PanelTaskCreate,
    PanelTaskUpdate,
)

router = APIRouter()

# =====================================================
# HELPERS
# =====================================================

def require_hr(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "HR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR access required",
        )
    return current_user


# =====================================================
# PANELS
# =====================================================

@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_panel(
    payload: PanelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    panel = Panel(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(panel)
    db.commit()
    db.refresh(panel)

    return success_response(
        message="Panel created successfully",
        data={
            "id": str(panel.id),
            "name": panel.name,
            "description": panel.description,
            "is_active": panel.is_active,
        },
    )


@router.get("", response_model=dict)
def list_panels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    panels = db.query(Panel).order_by(Panel.created_at.desc()).all()

    return success_response(
        message="Panels fetched successfully",
        data=[
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat(),
            }
            for p in panels
        ],
    )


@router.get("/{panel_id}", response_model=dict)
def get_panel(
    panel_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel not found",
        )

    members = (
        db.query(PanelMember)
        .filter(PanelMember.panel_id == panel_id)
        .all()
    )

    tasks = (
        db.query(PanelTask)
        .filter(PanelTask.panel_id == panel_id)
        .order_by(PanelTask.order_index.asc())
        .all()
    )

    return success_response(
        message="Panel fetched successfully",
        data={
            "id": str(panel.id),
            "name": panel.name,
            "description": panel.description,
            "is_active": panel.is_active,
            "created_at": panel.created_at.isoformat(),
            "members": [
                {
                    "id": str(m.id),
                    "user_id": str(m.user_id),
                    "role": m.role,
                }
                for m in members
            ],
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description,
                    "max_score": t.max_score,
                    "order_index": t.order_index,
                    "is_required": t.is_required,
                }
                for t in tasks
            ],
        },
    )


@router.put("/{panel_id}", response_model=dict)
def update_panel(
    panel_id: UUID,
    payload: PanelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(panel, field, value)

    db.commit()
    db.refresh(panel)

    return success_response(
        message="Panel updated successfully",
        data={
            "id": str(panel.id),
            "name": panel.name,
            "description": panel.description,
            "is_active": panel.is_active,
        },
    )


@router.delete("/{panel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_panel(
    panel_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel not found",
        )

    assignment_exists = db.execute(
        text(
            """
            SELECT 1 FROM panel_assignments
            WHERE panel_id = :panel_id
            LIMIT 1
            """
        ),
        {"panel_id": str(panel_id)},
    ).first()

    if assignment_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Panel already assigned to nominations",
        )

    db.delete(panel)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =====================================================
# PANEL MEMBERS
# =====================================================

@router.post("/{panel_id}/members", response_model=dict)
def add_panel_member(
    panel_id: UUID,
    payload: PanelMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel not found",
        )

    exists = db.query(PanelMember).filter(
        PanelMember.panel_id == panel_id,
        PanelMember.user_id == payload.user_id,
    ).first()

    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already added to panel",
        )

    member = PanelMember(
        panel_id=panel_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return success_response(
        message="Panel member added successfully",
        data={
            "id": str(member.id),
            "panel_id": str(member.panel_id),
            "user_id": str(member.user_id),
            "role": member.role,
        },
    )


@router.put("/{panel_id}/members/{member_id}", response_model=dict)
def update_panel_member(
    panel_id: UUID,
    member_id: UUID,
    payload: PanelMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    member = db.query(PanelMember).filter(
        PanelMember.id == member_id,
        PanelMember.panel_id == panel_id,
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel member not found",
        )

    member.role = payload.role
    db.commit()
    db.refresh(member)

    return success_response(
        message="Panel member updated successfully",
        data={
            "id": str(member.id),
            "user_id": str(member.user_id),
            "role": member.role,
        },
    )


@router.delete(
    "/{panel_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_panel_member(
    panel_id: UUID,
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    member = db.query(PanelMember).filter(
        PanelMember.id == member_id,
        PanelMember.panel_id == panel_id,
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel member not found",
        )

    review_exists = db.execute(
        text(
            """
            SELECT 1 FROM panel_reviews
            WHERE panel_member_id = :member_id
            LIMIT 1
            """
        ),
        {"member_id": str(member_id)},
    ).first()

    if review_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Panel member has already submitted reviews",
        )

    db.delete(member)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =====================================================
# PANEL TASKS (CRITERIA)
# =====================================================

@router.post("/{panel_id}/tasks", response_model=dict)
def add_panel_task(
    panel_id: UUID,
    payload: PanelTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel not found",
        )

    task = PanelTask(
        panel_id=panel_id,
        title=payload.title,
        description=payload.description,
        max_score=payload.max_score,
        order_index=payload.order_index,
        is_required=payload.is_required,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return success_response(
        message="Panel task added successfully",
        data={
            "id": str(task.id),
            "panel_id": str(task.panel_id),
            "title": task.title,
            "max_score": task.max_score,
        },
    )


@router.put("/{panel_id}/tasks/{task_id}", response_model=dict)
def update_panel_task(
    panel_id: UUID,
    task_id: UUID,
    payload: PanelTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    task = db.query(PanelTask).filter(
        PanelTask.id == task_id,
        PanelTask.panel_id == panel_id,
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel task not found",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return success_response(
        message="Panel task updated successfully",
        data={
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "max_score": task.max_score,
            "order_index": task.order_index,
            "is_required": task.is_required,
        },
    )


@router.delete(
    "/{panel_id}/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_panel_task(
    panel_id: UUID,
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    task = db.query(PanelTask).filter(
        PanelTask.id == task_id,
        PanelTask.panel_id == panel_id,
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel task not found",
        )

    review_exists = db.execute(
        text(
            """
            SELECT 1 FROM panel_reviews
            WHERE panel_task_id = :task_id
            LIMIT 1
            """
        ),
        {"task_id": str(task_id)},
    ).first()

    if review_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already reviewed and cannot be deleted",
        )

    db.delete(task)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)