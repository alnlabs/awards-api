from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class AwardTypeBase(BaseModel):
    code: str
    label: str
    description: Optional[str] = None
    is_active: bool = True


class AwardTypeCreate(AwardTypeBase):
    pass


class AwardTypeUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AwardTypeResponse(BaseModel):
    id: UUID
    code: str
    label: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


