from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response
from app.core.security import hash_password
from app.models.user import User, UserRole, SecurityQuestion
from app.schemas.users import UserResponse, UserUpdate, UserCreate
from app.core.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=dict)
def me(
    user: User = Depends(get_current_user)
):
    return success_response(
        message="User fetched successfully",
        data={
            "id": str(user.id),
            "employee_code": user.employee_code,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_user(
    payload: UserCreate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    # Validate security questions (exactly 3)
    if len(payload.security_questions) != 3:
        failure_response(
            message="User creation failed",
            error="Exactly 3 security questions are required",
            status_code=400
        )

    # Check for duplicate email
    if db.query(User).filter(User.email == payload.email).first():
        failure_response(
            message="User creation failed",
            error="Email already registered",
            status_code=400
        )

    # Check for duplicate employee_code if provided
    if payload.employee_code:
        existing_code = db.query(User).filter(User.employee_code == payload.employee_code).first()
        if existing_code:
            failure_response(
                message="User creation failed",
                error="Employee code already exists",
                status_code=400
            )

    # Validate role
    try:
        role = UserRole(payload.role)
    except ValueError:
        failure_response(
            message="User creation failed",
            error="Invalid role",
            status_code=400
        )

    # Create user
    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
        employee_code=payload.employee_code,
        is_active=True
    )

    db.add(new_user)
    db.flush()  # Get user.id

    # Add security questions
    for q in payload.security_questions:
        db.add(
            SecurityQuestion(
                user_id=new_user.id,
                question=q.question,
                answer_hash=hash_password(q.answer)
            )
        )

    db.commit()
    db.refresh(new_user)

    return success_response(
        message="User created successfully",
        data={
            "id": str(new_user.id),
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role.value,
            "employee_code": new_user.employee_code,
            "is_active": new_user.is_active
        }
    )


@router.get("", response_model=dict)
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    query = db.query(User)

    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            failure_response(
                message="Invalid role",
                error=f"Role must be one of: {[r.value for r in UserRole]}",
                status_code=400
            )

    users = query.filter(User.is_active == True).offset(skip).limit(limit).all()

    return success_response(
        message="Users fetched successfully",
        data=[
            {
                "id": str(u.id),
                "employee_code": u.employee_code,
                "name": u.name,
                "email": u.email,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]
    )


@router.get("/{user_id}", response_model=dict)
def get_user(
    user_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    target_user = db.get(User, user_id)

    if not target_user:
        failure_response(
            message="User not found",
            error="User does not exist",
            status_code=404
        )

    return success_response(
        message="User fetched successfully",
        data={
            "id": str(target_user.id),
            "employee_code": target_user.employee_code,
            "name": target_user.name,
            "email": target_user.email,
            "role": target_user.role.value,
            "is_active": target_user.is_active,
            "created_at": target_user.created_at.isoformat()
        }
    )


@router.patch("/{user_id}", response_model=dict)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    target_user = db.get(User, user_id)

    if not target_user:
        failure_response(
            message="User not found",
            error="User does not exist",
            status_code=404
        )

    if payload.name is not None:
        target_user.name = payload.name
    if payload.employee_code is not None:
        # Check for duplicate employee_code
        existing = db.query(User).filter(
            User.employee_code == payload.employee_code,
            User.id != user_id
        ).first()
        if existing:
            failure_response(
                message="Update failed",
                error="Employee code already exists",
                status_code=400
            )
        target_user.employee_code = payload.employee_code
    if payload.role is not None:
        try:
            target_user.role = UserRole(payload.role)
        except ValueError:
            failure_response(
                message="Update failed",
                error="Invalid role",
                status_code=400
            )
    if payload.is_active is not None:
        target_user.is_active = payload.is_active

    db.commit()

    return success_response(
        message="User updated successfully",
        data={
            "id": str(target_user.id),
            "employee_code": target_user.employee_code,
            "name": target_user.name,
            "email": target_user.email,
            "role": target_user.role.value,
            "is_active": target_user.is_active
        }
    )


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: UUID,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    target_user = db.get(User, user_id)

    if not target_user:
        failure_response(
            message="User not found",
            error="User does not exist",
            status_code=404
        )

    # Prevent self-deletion
    if target_user.id == user.id:
        failure_response(
            message="Deletion failed",
            error="Cannot delete your own account",
            status_code=400
        )

    # Soft delete (set is_active = False)
    target_user.is_active = False
    db.commit()

    return success_response(
        message="User deleted successfully",
        data={
            "id": str(target_user.id),
            "name": target_user.name,
            "email": target_user.email,
            "is_active": False
        }
    )