from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import require_role
from app.core.response import success_response, failure_response
from app.core.security import hash_password
from app.models.user import User, UserRole, SecurityQuestion
from app.schemas.users import UserResponse, UserUpdate, UserCreate
from app.core.auth import get_current_user
import csv
import io
import json

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


@router.post("/bulk-upload", response_model=dict)
async def bulk_upload_users(
    file: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    """Bulk upload users from CSV or JSON file.

    CSV format expected (columns):
      name,email,employee_code,role,password,q1,q1_answer,q2,q2_answer,q3,q3_answer

    JSON format expected: list of objects matching the UserCreate schema.
    """

    content = await file.read()
    created = 0
    failures = []

    try:
        if file.filename.lower().endswith(".json") or file.content_type == "application/json":
            records = json.loads(content.decode("utf-8"))
        else:
            # treat as CSV
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            records = []
            for r in reader:
                # map q1/q1_answer... to security_questions array
                sq = []
                for i in range(1, 4):
                    qk = f"q{i}"
                    ak = f"q{i}_answer"
                    if r.get(qk):
                        sq.append({"question": r.get(qk), "answer": r.get(ak)})

                records.append({
                    "name": r.get("name"),
                    "email": r.get("email"),
                    "employee_code": r.get("employee_code") or None,
                    "role": r.get("role") or "EMPLOYEE",
                    "password": r.get("password"),
                    "security_questions": sq,
                })

        if not isinstance(records, list):
            raise ValueError("Uploaded file must contain a list of users")

        for idx, rec in enumerate(records, start=1):
            # Basic validation
            try:
                name = rec.get("name")
                email = rec.get("email")
                password = rec.get("password")
                role = rec.get("role")
                security_questions = rec.get("security_questions")

                if not (name and email and password and role and security_questions):
                    raise ValueError("Missing required fields")

                if len(security_questions) != 3:
                    raise ValueError("Exactly 3 security questions are required")

                # Check duplicate email
                if db.query(User).filter(User.email == email).first():
                    raise ValueError("Email already registered")

                # Validate role
                try:
                    role_enum = UserRole(role)
                except ValueError:
                    raise ValueError("Invalid role")

                # create user
                new_user = User(
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    role=role_enum,
                    employee_code=rec.get("employee_code"),
                    is_active=True,
                )

                db.add(new_user)
                db.flush()

                for q in security_questions:
                    db.add(
                        SecurityQuestion(
                            user_id=new_user.id,
                            question=q.get("question"),
                            answer_hash=hash_password(q.get("answer"))
                        )
                    )

                db.commit()
                created += 1

            except Exception as e:
                db.rollback()
                failures.append({"row": idx, "error": str(e), "record": rec})

    except Exception as e:
        failure_response(
            message="Bulk upload failed",
            error=str(e),
            status_code=400
        )

    return success_response(
        message="Bulk upload completed",
        data={"created": created, "failed": failures}
    )