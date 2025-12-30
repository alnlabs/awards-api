from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.response import failure_response
from app.models.user import User, UserRole

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