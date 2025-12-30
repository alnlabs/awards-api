from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import date, datetime


class CycleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    quarter: str
    year: int
    start_date: date
    end_date: date
    status: Optional[str] = "DRAFT"


class CycleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class CycleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    quarter: str
    year: int
    start_date: date
    end_date: date
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
