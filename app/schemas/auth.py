from typing import List
from pydantic import BaseModel, EmailStr, Field


class SecurityQuestionCreate(BaseModel):
    question: str
    answer: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: str
    security_questions: List[SecurityQuestionCreate]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    security_questions: List[SecurityQuestionCreate]


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"