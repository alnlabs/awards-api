from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.response import failure_response
from app.models.user import User, UserRole
from app.models.panel_member import PanelMember

# IMPORTANT:
# tokenUrl is RELATIVE to the mounted router, NOT hard-coded with /api/v1
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


# ---------------------------------------------------
# Get currently authenticated user (JWT)
# ---------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        failure_response(
            message="Authentication failed",
            error="Invalid or expired token",
            status_code=401
        )

    user = db.get(User, payload["sub"])

    if not user:
        failure_response(
            message="Authentication failed",
            error="User not found",
            status_code=401
        )

    if not user.is_active:
        failure_response(
            message="Access denied",
            error="User account is inactive",
            status_code=403
        )

    return user


# ---------------------------------------------------
# Role-based access control dependency
# ---------------------------------------------------
def require_role(*allowed_roles: UserRole):
    def role_checker(
        user: User = Depends(get_current_user)
    ) -> User:
        if user.role not in allowed_roles:
            failure_response(
                message="Access denied",
                error="Insufficient permissions",
                status_code=403
            )
        return user

    return role_checker


# ---------------------------------------------------
# Panel member access control (checks if user is assigned to any panel)
# This allows users with any role (EMPLOYEE, MANAGER, etc.) to access panel features
# if they are assigned to a panel, treating PANEL as a sub-role/assignment
# ---------------------------------------------------
def require_panel_member():
    def panel_member_checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Check if user's main role is PANEL
        if user.role == UserRole.PANEL:
            return user
        
        # Check if user is assigned to any panel (sub-role/assignment)
        panel_member = db.query(PanelMember).filter(
            PanelMember.user_id == user.id
        ).first()
        
        if not panel_member:
            failure_response(
                message="Access denied",
                error="You are not assigned to any panel",
                status_code=403
            )
        
        return user

    return panel_member_checker