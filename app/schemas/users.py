from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class SecurityQuestionCreate(BaseModel):
    question: str
    answer: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: str
    employee_code: Optional[str] = None
    security_questions: List[SecurityQuestionCreate] = Field(min_length=3, max_length=3)


class UserResponse(BaseModel):
    id: UUID
    employee_code: Optional[str] = None
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    employee_code: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
