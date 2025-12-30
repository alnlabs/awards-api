from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class FormAnswerCreate(BaseModel):
    field_key: str
    value: Any  # JSONB value


class NominationCreate(BaseModel):
    cycle_id: UUID
    form_id: UUID
    nominee_id: UUID
    answers: List[FormAnswerCreate]
    status: Optional[str] = "DRAFT"


class NominationUpdate(BaseModel):
    answers: Optional[List[FormAnswerCreate]] = None
    status: Optional[str] = None


class FormAnswerResponse(BaseModel):
    id: UUID
    field_key: str
    value: Any

    class Config:
        from_attributes = True


class NominationResponse(BaseModel):
    id: UUID
    cycle_id: UUID
    form_id: UUID
    nominee_id: UUID
    nominated_by_id: UUID
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    answers: List[FormAnswerResponse]

    class Config:
        from_attributes = True


class NominationListResponse(BaseModel):
    id: UUID
    cycle_id: UUID
    nominee_id: UUID
    nominated_by_id: UUID
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PanelReviewCreate(BaseModel):
    nomination_id: UUID
    score: int = Field(ge=1, le=5)
    comments: Optional[str] = None


class PanelReviewResponse(BaseModel):
    id: UUID
    nomination_id: UUID
    panel_member_id: UUID
    score: int
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
