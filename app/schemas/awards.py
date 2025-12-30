from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class AwardResponse(BaseModel):
    id: UUID
    cycle_id: UUID
    nomination_id: UUID
    winner_id: UUID
    award_type: Optional[str] = None
    rank: Optional[int] = None
    is_active: bool
    created_at: datetime
    finalized_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AwardCreate(BaseModel):
    cycle_id: UUID
    nomination_id: UUID
    winner_id: UUID
    award_type: Optional[str] = None
    rank: Optional[int] = None
