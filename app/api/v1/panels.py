from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.panel import Panel
from app.models.panel_member import PanelMember
from app.models.panel_task import PanelTask
from app.models.user import User

from app.schemas.panel import (
    PanelCreate,
    PanelUpdate,
    PanelResponse,
    PanelMemberCreate,
    PanelMemberResponse,
    PanelTaskCreate,
    PanelTaskResponse,
)

router = APIRouter(prefix="/panels", tags=["Panels"])


# =====================================================
# PANELS
# =====================================================

@router.post("", response_model=PanelResponse, status_code=status.HTTP_201_CREATED)
def create_panel(
    payload: PanelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    panel = Panel(
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(panel)
    db.commit()
    db.refresh(panel)
    return panel


@router.get("", response_model=list[PanelResponse])
def list_panels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Panel).order_by(Panel.created_at.desc()).all()


@router.get("/{panel_id}", response_model=PanelResponse)
def get_panel(
    panel_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")
    return panel


@router.put("/{panel_id}", response_model=PanelResponse)
def update_panel(
    panel_id: UUID,
    payload: PanelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(panel, field, value)

    db.commit()
    db.refresh(panel)
    return panel


# =====================================================
# PANEL MEMBERS
# =====================================================

@router.post("/{panel_id}/members", response_model=PanelMemberResponse)
def add_panel_member(
    panel_id: UUID,
    payload: PanelMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    exists = (
        db.query(PanelMember)
        .filter(
            PanelMember.panel_id == panel_id,
            PanelMember.user_id == payload.user_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="User already in panel")

    member = PanelMember(
        panel_id=panel_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


# =====================================================
# PANEL TASKS (CRITERIA)
# =====================================================

@router.post("/{panel_id}/tasks", response_model=PanelTaskResponse)
def add_panel_task(
    panel_id: UUID,
    payload: PanelTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    panel = db.query(Panel).filter(Panel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

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
    return task