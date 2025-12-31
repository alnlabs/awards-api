from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel


# =========================================================
# FORM FIELD (CREATE)
# =========================================================
class FormFieldCreate(BaseModel):
    label: str
    field_key: str
    field_type: str
    is_required: bool = False
    order_index: int = 0
    options: Optional[Dict[str, Any]] = None
    ui_schema: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None


# =========================================================
# FORM (CREATE / UPDATE)
# =========================================================
class FormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fields: List[FormFieldCreate]


# =========================================================
# FORM FIELD (RESPONSE)
# =========================================================
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


# =========================================================
# FORM (DETAILED RESPONSE)
# Used by:
# - GET /forms/{id}
# =========================================================
class FormResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: str
    fields: List[FormFieldResponse]

    class Config:
        from_attributes = True


# =========================================================
# FORM (LIST RESPONSE)
# Used by:
# - GET /forms
# =========================================================
class FormListResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True