from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from sqlalchemy.exc import ProgrammingError
from app.core.auth import get_current_user, oauth2_scheme
from app.core.response import success_response, failure_response
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest
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
# GET USER ROLES BY EMAIL (for login role selection)
# ---------------------------------------------------
@router.get("/user-roles/{email}")
def get_user_roles_by_email(email: str, db: Session = Depends(get_db)):
    """
    Get available roles for a user by email.
    Returns user's main role + PANEL if they're assigned to any panel.
    Used to show role selector in login form.
    """
    from app.models.panel_member import PanelMember
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return success_response(
            message="User not found",
            data={"roles": []}
        )
    
    if not user.is_active:
        return success_response(
            message="User is inactive",
            data={"roles": []}
        )
    
    # User's main role
    roles = [user.role.value]
    
    # Check if user is assigned to any panel (sub-role)
    is_panel_member = db.query(PanelMember).filter(
        PanelMember.user_id == user.id
    ).first() is not None
    
    # If user is a panel member, add PANEL as an available role option
    # (unless their main role is already PANEL)
    if is_panel_member and user.role != UserRole.PANEL:
        roles.append(UserRole.PANEL.value)
    
    return success_response(
        message="User roles fetched",
        data={
            "roles": roles,
            "has_multiple_roles": len(roles) > 1
        }
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
        return failure_response(
            message="Server error",
            error="Database tables not found. Have you run migrations?",
            status_code=500
        )

    if not user or not verify_password(payload.password, user.password_hash):
        return failure_response(
            message="Login failed",
            error="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return failure_response(
            message="Login failed",
            error="User account is inactive",
            status_code=status.HTTP_403_FORBIDDEN
        )

    # If role is specified, verify user has that role
    # With sub-role support: users can login with their main role OR as PANEL if they're a panel member
    selected_role = user.role.value
    if payload.role:
        try:
            requested_role = UserRole(payload.role)
            
            # Check if user's main role matches
            if user.role == requested_role:
                selected_role = requested_role.value
            # If requesting PANEL role, check if user is a panel member (sub-role)
            elif requested_role == UserRole.PANEL:
                from app.models.panel_member import PanelMember
                is_panel_member = db.query(PanelMember).filter(
                    PanelMember.user_id == user.id
                ).first() is not None
                
                if not is_panel_member:
                    return failure_response(
                        message="Login failed",
                        error="User is not assigned to any panel",
                        status_code=status.HTTP_403_FORBIDDEN
                    )
                selected_role = requested_role.value
            else:
                return failure_response(
                    message="Login failed",
                    error=f"User does not have {payload.role} role",
                    status_code=status.HTTP_403_FORBIDDEN
                )
        except ValueError:
            return failure_response(
                message="Login failed",
                error="Invalid role specified",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": selected_role
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
def me(
    token: str = Depends(oauth2_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.panel_member import PanelMember
    from app.core.security import decode_access_token
    
    # Get the role from JWT token (the role selected during login)
    # This allows UI to show features based on selected role, not just database role
    token_payload = decode_access_token(token)
    selected_role = token_payload.get("role") if token_payload else user.role.value
    
    # Check if user is a panel member (sub-role/assignment)
    is_panel_member = db.query(PanelMember).filter(
        PanelMember.user_id == user.id
    ).first() is not None
    
    return success_response(
        message="User fetched successfully",
        data={
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "employee_code": user.employee_code,
            "role": selected_role,  # Use role from JWT token (selected during login)
            "main_role": user.role.value,  # Keep original role for reference
            "is_active": user.is_active,
            "profile_image": user.profile_image,
            "is_panel_member": is_panel_member  # Indicates if user is assigned to any panel
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

# ---------------------------------------------------
# CHANGE PASSWORD (for authenticated users)
# ---------------------------------------------------
@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allow authenticated users to change their password."""
    if not verify_password(payload.current_password, user.password_hash):
        return failure_response(
            message="Password change failed",
            error="Current password is incorrect",
            status_code=400
        )

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return success_response(
        message="Password changed successfully",
        data=None
    )