from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from sqlalchemy.exc import ProgrammingError
from app.core.auth import get_current_user
from app.core.response import success_response, failure_response
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.models.user import User, SecurityQuestion, UserRole

router = APIRouter()

# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if len(payload.security_questions) != 3:
        failure_response(
            message="Registration failed",
            error="Exactly 3 security questions are required",
            status_code=400
        )

    if db.query(User).filter(User.email == payload.email).first():
        failure_response(
            message="Registration failed",
            error="Email already registered",
            status_code=400
        )

    try:
        role = UserRole(payload.role)
    except ValueError:
        failure_response(
            message="Registration failed",
            error="Invalid role",
            status_code=400
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
        is_active=True
    )

    db.add(user)
    db.flush()  # get user.id

    for q in payload.security_questions:
        db.add(
            SecurityQuestion(
                user_id=user.id,
                question=q.question,
                answer_hash=hash_password(q.answer)
            )
        )

    db.commit()

    return success_response(
        message="User registered successfully",
        data={"user_id": str(user.id)}
    )

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------
@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == payload.email).first()
    except ProgrammingError:
        # Likely migrations haven't been applied and tables don't exist yet.
        failure_response(
            message="Server error",
            error="Database tables not found. Have you run migrations?",
            status_code=500
        )

    if not user or not verify_password(payload.password, user.password_hash):
        failure_response(
            message="Login failed",
            error="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        failure_response(
            message="Login failed",
            error="User account is inactive",
            status_code=status.HTTP_403_FORBIDDEN
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role.value
        }
    )

    return success_response(
        message="Login successful",
        data={
            "access_token": token,
            "token_type": "bearer"
        }
    )

# ---------------------------------------------------
# CURRENT USER (🔥 FIXED — NO ROLE CHECK HERE)
# ---------------------------------------------------
@router.get("/me", response_model=dict)
def me(user: User = Depends(get_current_user)):
    return success_response(
        message="User fetched successfully",
        data={
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active
        }
    )

# ---------------------------------------------------
# FORGOT PASSWORD (SECURITY QUESTIONS)
# ---------------------------------------------------
@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        failure_response(
            message="Verification failed",
            error="User not found",
            status_code=404
        )

    for q in payload.security_questions:
        stored = (
            db.query(SecurityQuestion)
            .filter(
                SecurityQuestion.user_id == user.id,
                SecurityQuestion.question == q.question
            )
            .first()
        )

        if not stored or not verify_password(q.answer, stored.answer_hash):
            failure_response(
                message="Verification failed",
                error="Security answers do not match",
                status_code=400
            )

    return success_response(
        message="Security questions verified",
        data=None
    )

# ---------------------------------------------------
# RESET PASSWORD
# ---------------------------------------------------
@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        failure_response(
            message="Password reset failed",
            error="User not found",
            status_code=404
        )

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return success_response(
        message="Password reset successful",
        data=None
    )