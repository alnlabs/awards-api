from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# ======================================================
# PANEL
# ======================================================

class PanelCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_active: bool = True


class PanelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PanelResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ======================================================
# PANEL MEMBER
# ======================================================

class PanelMemberCreate(BaseModel):
    user_id: UUID
    role: str = Field(..., pattern="^(CHAIR|REVIEWER)$")


class PanelMemberUpdate(BaseModel):
    role: str = Field(..., pattern="^(CHAIR|REVIEWER)$")


class PanelMemberResponse(BaseModel):
    id: UUID
    panel_id: UUID
    user_id: UUID
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ======================================================
# PANEL TASK (CRITERIA)
# ======================================================

class PanelTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    max_score: int = Field(default=5, ge=1)
    order_index: int = 0
    is_required: bool = True


class PanelTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_score: Optional[int] = Field(None, ge=1)
    order_index: Optional[int] = None
    is_required: Optional[bool] = None


class PanelTaskResponse(BaseModel):
    id: UUID
    panel_id: UUID
    title: str
    description: Optional[str]
    max_score: int
    order_index: int
    is_required: bool

    class Config:
        from_attributes = True


# ======================================================
# PANEL ASSIGNMENT (HR → NOMINATION)
# ======================================================

class PanelAssignmentCreate(BaseModel):
    panel_ids: List[UUID]


class PanelAssignmentResponse(BaseModel):
    id: UUID
    nomination_id: UUID
    panel_id: UUID
    assigned_by: UUID
    status: str
    assigned_at: datetime

    class Config:
        from_attributes = True


# ======================================================
# PANEL REVIEW (TASK-BASED) ✅ FIXED
# ======================================================
# ❌ task_id REMOVED (comes from URL path)

class PanelReviewCreate(BaseModel):
    score: int = Field(..., ge=0)
    comment: Optional[str] = None


class PanelReviewResponse(BaseModel):
    id: UUID
    panel_assignment_id: UUID
    panel_member_id: UUID
    task_id: UUID
    score: int
    comment: Optional[str]
    reviewed_at: datetime

    class Config:
        from_attributes = True


# ======================================================
# AGGREGATED / VIEW MODELS
# ======================================================

class PanelAssignmentWithTasks(BaseModel):
    assignment: PanelAssignmentResponse
    tasks: List[PanelTaskResponse]


class PanelAssignmentWithReviews(BaseModel):
    assignment: PanelAssignmentResponse
    reviews: List[PanelReviewResponse]