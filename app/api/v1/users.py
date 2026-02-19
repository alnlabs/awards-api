from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import os

from app.core.database import get_db
from app.core.auth import require_role, get_current_user
from app.core.response import success_response, failure_response
from app.core.security import hash_password
from app.core.files import save_profile_image
from app.models.user import User, UserRole, SecurityQuestion
from app.schemas.users import UserResponse, UserUpdate, UserCreate, BulkDeleteRequest
from datetime import datetime, timezone
import csv
import io
import json
from pydantic import ValidationError

router = APIRouter()


@router.get("/me", response_model=dict)
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.panel_member import PanelMember
    
    # Check if user is a panel member (sub-role/assignment)
    is_panel_member = db.query(PanelMember).filter(
        PanelMember.user_id == user.id
    ).first() is not None
    
    return success_response(
        message="User fetched successfully",
        data={
            "id": str(user.id),
            "employee_code": user.employee_code,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "profile_image": user.profile_image,
            "is_panel_member": is_panel_member,  # Indicates if user is assigned to any panel
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

    # Only SUPER_ADMIN can create HR or SUPER_ADMIN accounts
    if role in (UserRole.HR, UserRole.SUPER_ADMIN) and user.role != UserRole.SUPER_ADMIN:
        failure_response(
            message="User creation failed",
            error="Only SUPER_ADMIN can create HR or SUPER_ADMIN users",
            status_code=403,
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
    search: str = None,
    sort_by: str = None,
    sort_order: str = "asc",
    user: User = Depends(require_role(UserRole.HR, UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    from sqlalchemy import or_, func

    query = db.query(User)

    # Filter active users
    query = query.filter(User.is_active == True)

    # Filter by role
    if role:
        try:
            role_enum = UserRole(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            return failure_response(
                message="Invalid role",
                error=f"Role must be one of: {[r.value for r in UserRole]}",
                status_code=400
            )

    # Search filter
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(User.name).like(search_term),
                func.lower(User.email).like(search_term),
                func.lower(User.employee_code).like(search_term),
                func.lower(User.role.cast(db.String)).like(search_term),
            )
        )

    # Get total count before pagination
    total_count = query.count()

    # Sorting
    if sort_by:
        sort_column = None
        if sort_by == "name":
            sort_column = User.name
        elif sort_by == "email":
            sort_column = User.email
        elif sort_by == "employee_code":
            sort_column = User.employee_code
        elif sort_by == "role":
            sort_column = User.role
        elif sort_by == "is_active":
            sort_column = User.is_active
        elif sort_by == "created_at":
            sort_column = User.created_at

        if sort_column:
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
    else:
        # Default sorting by name
        query = query.order_by(User.name.asc())

    # Pagination
    users = query.offset(skip).limit(limit).all()

    return success_response(
        message="Users fetched successfully",
        data={
            "items": [
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
            ],
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
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


@router.patch("/me", response_model=dict)
def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allow users to update their own profile (name, email, employee_code only)."""
    if payload.name is not None:
        current_user.name = payload.name
    if payload.employee_code is not None:
        # Check for duplicate employee_code
        existing = db.query(User).filter(
            User.employee_code == payload.employee_code,
            User.id != current_user.id
        ).first()
        if existing:
            return failure_response(
                message="Update failed",
                error="Employee code already exists",
                status_code=400
            )
        current_user.employee_code = payload.employee_code

    db.commit()
    db.refresh(current_user)

    return success_response(
        message="Profile updated successfully",
        data={
            "id": str(current_user.id),
            "employee_code": current_user.employee_code,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "profile_image": current_user.profile_image
        }
    )


@router.post("/me/profile-image", response_model=dict)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload or update profile image for the current user."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        return failure_response(
            message="Upload failed",
            error="File must be an image",
            status_code=400
        )

    # Delete old image if exists
    if current_user.profile_image:
        old_path = current_user.profile_image.replace("/static/", "app/static/")
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass  # Ignore errors when deleting old file

    # Save new image
    image_path = save_profile_image(file)
    current_user.profile_image = image_path

    db.commit()
    db.refresh(current_user)

    return success_response(
        message="Profile image uploaded successfully",
        data={
            "id": str(current_user.id),
            "profile_image": current_user.profile_image
        }
    )


@router.delete("/me/profile-image", response_model=dict)
def delete_profile_image(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete profile image for the current user."""
    if current_user.profile_image:
        old_path = current_user.profile_image.replace("/static/", "app/static/")
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass  # Ignore errors when deleting file

        current_user.profile_image = None
        db.commit()
        db.refresh(current_user)

    return success_response(
        message="Profile image deleted successfully",
        data={
            "id": str(current_user.id),
            "profile_image": None
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
        return failure_response(
            message="User not found",
            error="User does not exist",
            status_code=404
        )

    # Only SUPER_ADMIN can manage HR and SUPER_ADMIN users
    if user.role != UserRole.SUPER_ADMIN:
        # Current role of target is protected OR requested new role is protected
        protected_roles = (UserRole.HR, UserRole.SUPER_ADMIN)
        requested_role = None
        if payload.role is not None:
            try:
                requested_role = UserRole(payload.role)
            except ValueError:
                return failure_response(
                    message="Update failed",
                    error="Invalid role",
                    status_code=400,
                )

        if target_user.role in protected_roles or (requested_role and requested_role in protected_roles):
            return failure_response(
                message="Update failed",
                error="Only SUPER_ADMIN can manage HR and SUPER_ADMIN users",
                status_code=403,
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
            return failure_response(
                message="Update failed",
                error="Employee code already exists",
                status_code=400
            )
        target_user.employee_code = payload.employee_code
    if payload.role is not None:
        try:
            target_user.role = UserRole(payload.role)
        except ValueError:
            return failure_response(
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

    # Only SUPER_ADMIN can delete HR and SUPER_ADMIN users
    if user.role != UserRole.SUPER_ADMIN and target_user.role in (UserRole.HR, UserRole.SUPER_ADMIN):
        failure_response(
            message="Deletion failed",
            error="Only SUPER_ADMIN can delete HR and SUPER_ADMIN users",
            status_code=403,
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


@router.post("/bulk-delete", response_model=dict)
def bulk_delete_users(
    request: BulkDeleteRequest,
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    """Bulk delete users by setting is_active to False (soft delete)."""
    
    ids = request.user_ids
    if not ids:
        failure_response(
            message="Bulk delete failed",
            error="No user IDs provided",
            status_code=400
        )
    
    # Validate UUID format (bulk op should skip non-deletable targets rather than failing the whole request)
    validated_ids = []
    skipped_self_ids = []
    invalid_ids = []
    for id_str in ids:
        try:
            user_uuid = UUID(id_str)
            if user_uuid == user.id:
                skipped_self_ids.append(user_uuid)
                continue
            validated_ids.append(user_uuid)
        except ValueError:
            invalid_ids.append(id_str)

    if invalid_ids:
        failure_response(
            message="Bulk delete failed",
            error=f"Invalid user ID format: {invalid_ids}",
            status_code=400
        )

    # Dedupe IDs while preserving order
    validated_ids = list(dict.fromkeys(validated_ids))

    # If request only contained the current user's id(s), treat as a no-op success
    if not validated_ids:
        return success_response(
            message="No deletable users found (skipped current user)",
            data={
                "deleted_count": 0,
                "requested_ids": len(ids),
                "skipped_self_ids": [str(x) for x in skipped_self_ids],
            },
        )
    
    # Find users to be deleted
    users_to_delete = db.query(User).filter(User.id.in_(validated_ids)).all()
    
    if not users_to_delete:
        failure_response(
            message="Bulk delete failed",
            error="No valid users found to delete",
            status_code=404
        )

    found_ids = {u.id for u in users_to_delete}
    not_found_ids = [str(x) for x in validated_ids if x not in found_ids]
    
    # Filter out protected users from deletion
    if user.role == UserRole.SUPER_ADMIN:
        # SUPER_ADMIN can delete HR users but not other SUPER_ADMIN users
        non_admin_users = [
            u for u in users_to_delete
            if u.role != UserRole.SUPER_ADMIN
        ]
        skipped_admin_users = [
            u for u in users_to_delete
            if u.role == UserRole.SUPER_ADMIN
        ]
    else:
        # HR (and others) cannot delete HR or SUPER_ADMIN users
        non_admin_users = [
            u for u in users_to_delete
            if u.role not in (UserRole.HR, UserRole.SUPER_ADMIN)
        ]
        skipped_admin_users = [
            u for u in users_to_delete
            if u.role in (UserRole.HR, UserRole.SUPER_ADMIN)
        ]
    
    # Perform soft delete on non-admin users only
    deleted_count = 0
    already_inactive_ids = []
    for target_user in non_admin_users:
        if target_user.is_active is False:
            already_inactive_ids.append(str(target_user.id))
            continue
        target_user.is_active = False
        deleted_count += 1
    
    db.commit()
    
    response_data = {
        "deleted_count": deleted_count,
        "requested_ids": len(ids),
        "validated_ids": len(validated_ids),
    }

    if skipped_self_ids:
        response_data["skipped_self_ids"] = [str(x) for x in skipped_self_ids]

    if not_found_ids:
        response_data["not_found_ids"] = not_found_ids

    if already_inactive_ids:
        response_data["already_inactive_ids"] = already_inactive_ids
    
    # Include skipped admin users info if any
    if skipped_admin_users:
        response_data["skipped_admin_users"] = [
            {
                "id": str(admin_user.id),
                "name": admin_user.name,
                "email": admin_user.email,
                "role": admin_user.role.value
            }
            for admin_user in skipped_admin_users
        ]
        message = f"Successfully deleted {deleted_count} user(s), skipped {len(skipped_admin_users)} admin user(s)"
    else:
        message = f"Successfully deleted {deleted_count} user(s)"
    
    return success_response(
        message=message,
        data=response_data
    )


@router.post("/bulk-upload", response_model=dict)
async def bulk_upload_users(
    file: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.HR)),
    db: Session = Depends(get_db)
):
    """Bulk upload users from CSV or JSON file."""
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
            try:
                # Use UserCreate for thorough validation
                user_data = UserCreate(**rec)
                
                # Check duplicate email
                if db.query(User).filter(User.email == user_data.email).first():
                    raise ValueError("Email already registered")

                # Validate role (UserCreate handles the basic check, but we can do extra if needed)
                role_enum = UserRole(user_data.role)
                
                # Check for duplicate employee_code if provided
                if user_data.employee_code:
                    if db.query(User).filter(User.employee_code == user_data.employee_code).first():
                        raise ValueError("Employee code already exists")

                new_user = User(
                    name=user_data.name,
                    email=user_data.email,
                    password_hash=hash_password(user_data.password),
                    role=role_enum,
                    employee_code=user_data.employee_code,
                    is_active=True,
                )

                db.add(new_user)
                db.flush()

                for q in user_data.security_questions:
                    db.add(
                        SecurityQuestion(
                            user_id=new_user.id,
                            question=q.question,
                            answer_hash=hash_password(q.answer)
                        )
                    )

                db.commit()
                created += 1

            except (ValidationError, ValueError) as e:
                db.rollback()
                error_msg = str(e)
                if isinstance(e, ValidationError):
                    error_msg = e.errors()
                failures.append({"row": idx, "error": error_msg, "record": rec})
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