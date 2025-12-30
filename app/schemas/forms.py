from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, Field


class FormFieldCreate(BaseModel):
    label: str
    field_key: str
    field_type: str  # TEXT, TEXTAREA, NUMBER, SELECT, MULTI_SELECT, RADIO, CHECKBOX, RATING, DATE, BOOLEAN, FILE
    is_required: bool = False
    order_index: int = 0
    options: Optional[Dict[str, Any]] = None  # for select, radio, checkbox options
    ui_schema: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None


class FormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cycle_id: UUID
    fields: List[FormFieldCreate]


class FormFieldResponse(BaseModel):
    id: UUID
    label: str
    field_key: str
    field_type: str
    is_required: bool
    order_index: int
    options: Optional[Dict[str, Any]] = None
    ui_schema: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class FormResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    cycle_id: UUID
    is_active: bool
    created_at: str
    fields: List[FormFieldResponse]

    class Config:
        from_attributes = True


class FormListResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    cycle_id: UUID
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True
